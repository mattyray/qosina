"""FastAPI application — SSE endpoint, approval CRUD, serves static frontend."""

import json
import uuid
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from backend.models import ChatRequest, ApprovalUpdate
from backend.database import init_db, get_db
from backend.agent import create_agent

app = FastAPI(title="Qosina Enterprise AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation histories in memory (sufficient for demo)
conversations: dict[str, list] = {}

# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()

# Create agent once
agent = create_agent()


async def stream_agent_response(message: str, conversation_id: str) -> AsyncGenerator[dict, None]:
    """Run the agent and yield SSE events."""
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    conversations[conversation_id].append(HumanMessage(content=message))
    input_messages = {"messages": conversations[conversation_id]}

    try:
        async for event in agent.astream_events(input_messages, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                content = event["data"]["chunk"].content
                if content and isinstance(content, str):
                    yield {"event": "token", "data": json.dumps({"content": content})}

            elif kind == "on_tool_start":
                yield {
                    "event": "tool_call",
                    "data": json.dumps({
                        "tool": event["name"],
                        "input": event["data"].get("input", {}),
                        "status": "calling",
                    }),
                }

            elif kind == "on_tool_end":
                tool_output = event["data"].get("output", "")
                # Check if an approval was created
                try:
                    parsed = json.loads(tool_output) if isinstance(tool_output, str) else tool_output
                    if isinstance(parsed, dict) and parsed.get("Status") == "pending":
                        yield {
                            "event": "approval_created",
                            "data": json.dumps({
                                "id": parsed.get("Id"),
                                "type": parsed.get("RecommendationType"),
                                "title": parsed.get("Title"),
                                "status": "pending",
                            }),
                        }
                except (json.JSONDecodeError, TypeError):
                    pass

                yield {
                    "event": "tool_result",
                    "data": json.dumps({
                        "tool": event["name"],
                        "status": "complete",
                    }),
                }

        # Get the final AI message from the agent's state
        final_state = await agent.ainvoke(input_messages)
        ai_message = final_state["messages"][-1]
        conversations[conversation_id] = final_state["messages"]

    except Exception as e:
        yield {"event": "error", "data": json.dumps({"message": f"Agent error: {str(e)}"})}

    yield {"event": "done", "data": json.dumps({"conversation_id": conversation_id})}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """SSE streaming chat endpoint."""
    conversation_id = request.conversation_id or str(uuid.uuid4())

    async def event_generator():
        async for event in stream_agent_response(request.message, conversation_id):
            yield event

    return EventSourceResponse(event_generator())


@app.get("/api/approvals")
def get_approvals():
    """Get all approval queue items."""
    with get_db() as conn:
        rows = conn.execute(
            "SELECT * FROM approval_queue ORDER BY ai_generated_at DESC"
        ).fetchall()

    return [dict(r) for r in rows]


@app.patch("/api/approvals/{approval_id}")
def update_approval(approval_id: int, update: ApprovalUpdate):
    """Approve or reject an approval queue item."""
    if update.status not in ("approved", "rejected"):
        raise HTTPException(400, "Status must be 'approved' or 'rejected'")

    now = datetime.now().isoformat()

    with get_db() as conn:
        result = conn.execute(
            """UPDATE approval_queue
               SET status = ?, reviewed_by = ?, reviewed_at = ?
               WHERE id = ? AND status = 'pending'""",
            (update.status, update.reviewed_by, now, approval_id)
        )
        if result.rowcount == 0:
            raise HTTPException(404, "Approval not found or already reviewed")

        row = conn.execute(
            "SELECT * FROM approval_queue WHERE id = ?", (approval_id,)
        ).fetchone()

    return dict(row)


@app.get("/api/stats")
def get_stats():
    """Database stats for the status bar."""
    with get_db() as conn:
        product_count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        inventory_lots = conn.execute("SELECT COUNT(*) FROM inventory").fetchone()[0]
        pending_approvals = conn.execute(
            "SELECT COUNT(*) FROM approval_queue WHERE status = 'pending'"
        ).fetchone()[0]
        total_customers = conn.execute("SELECT COUNT(*) FROM customers").fetchone()[0]

    return {
        "product_count": product_count,
        "inventory_lots": inventory_lots,
        "pending_approvals": pending_approvals,
        "total_customers": total_customers,
    }


# Serve static files and index.html
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    """Serve the frontend."""
    return FileResponse("static/index.html")
