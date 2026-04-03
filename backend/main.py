"""FastAPI application — SSE endpoint, approval CRUD, serves static frontend."""

import json
import uuid
import base64
from datetime import datetime
from typing import AsyncGenerator

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sse_starlette.sse import EventSourceResponse
from langchain_core.messages import HumanMessage

from backend.models import ChatRequest, ApprovalUpdate
from backend.database import init_db, get_db
from backend.agent import create_agent as create_general_agent

app = FastAPI(title="Qosina Enterprise AI Assistant")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store conversation histories in memory (sufficient for demo)
conversations: dict[str, list] = {}

# Agent registry — lazily initialized per use case
_agents: dict[str, object] = {}


def get_agent(use_case: str):
    """Get or create the agent for a given use case."""
    if use_case not in _agents:
        if use_case == "sales_orders":
            from backend.use_case_1.agent import create_uc1_agent
            _agents[use_case] = create_uc1_agent()
        elif use_case == "ap_processing":
            from backend.use_case_2.agent import create_uc2_agent
            _agents[use_case] = create_uc2_agent()
        elif use_case == "product_data":
            from backend.use_case_3.agent import create_uc3_agent
            _agents[use_case] = create_uc3_agent()
        else:
            _agents[use_case] = create_general_agent()
    return _agents[use_case]


def clear_agent_cache():
    """Clear all cached agents so they get recreated with the new model."""
    _agents.clear()


# Initialize database on startup
@app.on_event("startup")
def startup():
    init_db()


async def stream_agent_response(agent, message, conversation_id: str) -> AsyncGenerator[dict, None]:
    """Run the agent and yield SSE events. message can be str or list (multimodal content blocks)."""
    if conversation_id not in conversations:
        conversations[conversation_id] = []

    conversations[conversation_id].append(HumanMessage(content=message))
    input_messages = {"messages": conversations[conversation_id]}

    try:
        # Use astream to get state updates, then stream tokens from events
        full_response = ""

        async for event in agent.astream_events(input_messages, version="v2"):
            kind = event["event"]

            if kind == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                # Handle both string content and list content (tool calls)
                content = chunk.content
                if isinstance(content, str) and content:
                    full_response += content
                    yield {"event": "token", "data": json.dumps({"content": content})}
                elif isinstance(content, list):
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text" and block.get("text"):
                            full_response += block["text"]
                            yield {"event": "token", "data": json.dumps({"content": block["text"]})}

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
                    output_str = tool_output.content if hasattr(tool_output, 'content') else str(tool_output)
                    parsed = json.loads(output_str) if isinstance(output_str, str) else output_str
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
                except (json.JSONDecodeError, TypeError, AttributeError):
                    pass

                yield {
                    "event": "tool_result",
                    "data": json.dumps({
                        "tool": event["name"],
                        "status": "complete",
                    }),
                }

        # Save conversation state without re-invoking
        from langchain_core.messages import AIMessage
        if full_response:
            conversations[conversation_id].append(AIMessage(content=full_response))

    except Exception as e:
        error_str = str(e)
        import traceback
        traceback.print_exc()
        if "overloaded" in error_str.lower() or "rate" in error_str.lower() or "529" in error_str:
            friendly = "Claude is temporarily busy. Please wait a moment and try again."
        elif "auth" in error_str.lower() or "api_key" in error_str.lower() or "401" in error_str:
            friendly = "API authentication error. Please check the API key configuration."
        else:
            friendly = f"Something went wrong: {error_str[:200]}"
        yield {"event": "error", "data": json.dumps({"message": friendly})}

    yield {"event": "done", "data": json.dumps({"conversation_id": conversation_id})}


@app.post("/api/chat")
async def chat(request: ChatRequest):
    """SSE streaming chat endpoint."""
    conversation_id = request.conversation_id or str(uuid.uuid4())
    use_case = request.use_case or "general"
    agent = get_agent(use_case)

    async def event_generator():
        async for event in stream_agent_response(agent, request.message, conversation_id):
            yield event

    return EventSourceResponse(event_generator())


@app.post("/api/upload")
async def upload_file(
    file: UploadFile = File(...),
    use_case: str = Form("general"),
    prompt: str = Form(""),
):
    """Upload a file (PDF, image) for AI processing. Returns SSE stream."""
    conversation_id = str(uuid.uuid4())
    agent = get_agent(use_case)

    file_bytes = await file.read()
    b64 = base64.b64encode(file_bytes).decode("utf-8")

    # Determine media type
    filename = (file.filename or "").lower()
    is_pdf = filename.endswith(".pdf")

    if is_pdf:
        media_type = "image/png"
    elif filename.endswith((".jpg", ".jpeg")):
        media_type = "image/jpeg"
    elif filename.endswith(".png"):
        media_type = "image/png"
    elif filename.endswith(".gif"):
        media_type = "image/gif"
    elif filename.endswith(".webp"):
        media_type = "image/webp"
    else:
        media_type = "image/png"

    # Build multimodal message: text prompt + document/image
    uc_prompts = {
        "sales_orders": "Process this purchase order document. Extract all fields, match the customer, match the products against our catalog, validate pricing, and create a sales order approval.",
        "ap_processing": "Process this document. If it's a vendor invoice, extract the vendor, PO reference, line items, and amounts, then run a three-way match against our PO and receipt data. If it's a payment remittance, extract the payment details and match against open invoices. Create an approval with the result.",
        "product_data": "Extract product data from this supplier document. Apply the Qosina constitutional naming framework, validate consistency against our catalog, find similar products, and create a product entry approval.",
    }
    text_prompt = prompt or uc_prompts.get(use_case, "Analyze this document and extract all relevant information.")

    # For PDFs, render each page to an image
    if is_pdf:
        from backend.pdf_utils import pdf_to_images
        page_images = pdf_to_images(file_bytes)
        content_blocks = [{"type": "text", "text": text_prompt}]
        for page_b64 in page_images:
            content_blocks.append({
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{page_b64}"},
            })
    else:
        content_blocks = [
            {"type": "text", "text": text_prompt},
            {
                "type": "image_url",
                "image_url": {"url": f"data:{media_type};base64,{b64}"},
            },
        ]

    async def event_generator():
        async for event in stream_agent_response(agent, content_blocks, conversation_id):
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
    """Approve, reject, or revert an approval queue item."""
    if update.status not in ("approved", "rejected", "pending"):
        raise HTTPException(400, "Status must be 'approved', 'rejected', or 'pending'")

    now = datetime.now().isoformat()

    with get_db() as conn:
        if update.status == "pending":
            # Undo — move back to pending
            result = conn.execute(
                """UPDATE approval_queue
                   SET status = 'pending', reviewed_by = NULL, reviewed_at = NULL
                   WHERE id = ?""",
                (approval_id,)
            )
        else:
            # If structured_data was edited, save that too
            if update.structured_data:
                result = conn.execute(
                    """UPDATE approval_queue
                       SET status = ?, reviewed_by = ?, reviewed_at = ?, structured_data = ?
                       WHERE id = ? AND status = 'pending'""",
                    (update.status, update.reviewed_by, now, update.structured_data, approval_id)
                )
            else:
                result = conn.execute(
                    """UPDATE approval_queue
                       SET status = ?, reviewed_by = ?, reviewed_at = ?
                       WHERE id = ? AND status = 'pending'""",
                    (update.status, update.reviewed_by, now, approval_id)
                )
        if result.rowcount == 0:
            raise HTTPException(404, "Approval not found")

        row = conn.execute(
            "SELECT * FROM approval_queue WHERE id = ?", (approval_id,)
        ).fetchone()

    return dict(row)


@app.delete("/api/approvals/resolved")
def clear_resolved():
    """Delete all non-pending approval items."""
    with get_db() as conn:
        result = conn.execute(
            "DELETE FROM approval_queue WHERE status != 'pending'"
        )
    return {"deleted": result.rowcount}


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


@app.get("/api/model")
def get_model_info():
    """Get current model and available models."""
    from backend.shared.llm_provider import get_active_model_id, AVAILABLE_MODELS
    import os
    use_openrouter = os.getenv("USE_OPENROUTER", "true").lower() == "true"
    return {
        "active_model": get_active_model_id(),
        "active_model_name": AVAILABLE_MODELS.get(get_active_model_id(), get_active_model_id()),
        "available_models": AVAILABLE_MODELS,
        "use_openrouter": use_openrouter,
    }


@app.put("/api/model")
def switch_model(body: dict):
    """Switch the active LLM model at runtime."""
    from backend.shared.llm_provider import set_active_model, AVAILABLE_MODELS
    model_id = body.get("model_id", "")
    if model_id not in AVAILABLE_MODELS:
        raise HTTPException(400, f"Unknown model. Available: {list(AVAILABLE_MODELS.keys())}")
    set_active_model(model_id)
    clear_agent_cache()
    return {
        "active_model": model_id,
        "active_model_name": AVAILABLE_MODELS[model_id],
        "message": f"Switched to {AVAILABLE_MODELS[model_id]}. All agents will use the new model.",
    }


@app.get("/api/dashboard")
def get_dashboard():
    """Dashboard alerts — live counts of issues needing attention."""
    from datetime import datetime, timedelta
    now = datetime.now()
    cutoff_90 = (now + timedelta(days=90)).strftime("%Y-%m-%d")
    cutoff_30 = (now + timedelta(days=30)).strftime("%Y-%m-%d")

    with get_db() as conn:
        # Low stock items
        low_stock = conn.execute("""
            SELECT COUNT(DISTINCT i.item_id) FROM inventory i
            JOIN (SELECT item_id, SUM(quantity_on_hand) as total
                  FROM inventory GROUP BY item_id) t ON i.item_id = t.item_id
            WHERE t.total < i.reorder_point
        """).fetchone()[0]

        # Expiring within 90 days
        expiring_90 = conn.execute("""
            SELECT COUNT(*) FROM inventory
            WHERE expiration_date IS NOT NULL
            AND expiration_date <= ? AND quantity_on_hand > 0
        """, (cutoff_90,)).fetchone()[0]

        # Expiring within 30 days (urgent)
        expiring_30 = conn.execute("""
            SELECT COUNT(*) FROM inventory
            WHERE expiration_date IS NOT NULL
            AND expiration_date <= ? AND quantity_on_hand > 0
        """, (cutoff_30,)).fetchone()[0]

        # Pending approvals
        pending = conn.execute(
            "SELECT COUNT(*) FROM approval_queue WHERE status = 'pending'"
        ).fetchone()[0]

        # Customers with no orders in last 6 months (at-risk)
        six_months_ago = (now - timedelta(days=180)).strftime("%Y-%m-%d")
        at_risk = conn.execute("""
            SELECT COUNT(*) FROM customers c
            WHERE NOT EXISTS (
                SELECT 1 FROM order_history o
                WHERE o.customer_id = c.customer_id
                AND o.order_date >= ?
            )
        """, (six_months_ago,)).fetchone()[0]

        # Total inventory value
        total_value = conn.execute("""
            SELECT COALESCE(SUM(i.quantity_on_hand * p.unit_price), 0)
            FROM inventory i JOIN products p ON i.item_id = p.item_id
        """).fetchone()[0]

    return {
        "low_stock_items": low_stock,
        "expiring_90_days": expiring_90,
        "expiring_30_days": expiring_30,
        "pending_approvals": pending,
        "at_risk_customers": at_risk,
        "total_inventory_value": round(total_value, 2),
    }


# --- Data Explorer endpoints ---

@app.get("/api/products")
def get_products():
    """All products with inventory summary."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT p.*,
                   COALESCE(SUM(i.quantity_on_hand), 0) as total_stock,
                   MIN(i.reorder_point) as reorder_point
            FROM products p
            LEFT JOIN inventory i ON p.item_id = i.item_id
            GROUP BY p.item_id
            ORDER BY p.category, p.item_id
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/products/{item_id}")
def get_product_detail(item_id: str):
    """Single product with full inventory lots and compatibility."""
    with get_db() as conn:
        product = conn.execute("SELECT * FROM products WHERE item_id = ?", (item_id,)).fetchone()
        if not product:
            raise HTTPException(404, "Product not found")

        lots = conn.execute(
            "SELECT * FROM inventory WHERE item_id = ? ORDER BY expiration_date", (item_id,)
        ).fetchall()

        compat = conn.execute("""
            SELECT pc.*,
                   pa.product_name as part_a_name,
                   pb.product_name as part_b_name
            FROM product_compatibility pc
            JOIN products pa ON pc.part_a = pa.item_id
            JOIN products pb ON pc.part_b = pb.item_id
            WHERE pc.part_a = ? OR pc.part_b = ?
        """, (item_id, item_id)).fetchall()

    return {
        "product": dict(product),
        "inventory": [dict(r) for r in lots],
        "compatibility": [dict(r) for r in compat],
    }


@app.get("/api/customers")
def get_customers():
    """All customers with order summary."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT c.*,
                   COUNT(o.order_id) as total_orders,
                   COALESCE(SUM(o.total_price), 0) as total_revenue,
                   MAX(o.order_date) as last_order_date
            FROM customers c
            LEFT JOIN order_history o ON c.customer_id = o.customer_id
            GROUP BY c.customer_id
            ORDER BY total_revenue DESC
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/customers/{customer_id}")
def get_customer_detail(customer_id: str):
    """Single customer with full order history."""
    with get_db() as conn:
        customer = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()
        if not customer:
            raise HTTPException(404, "Customer not found")

        orders = conn.execute("""
            SELECT o.*, p.product_name, p.category
            FROM order_history o
            JOIN products p ON o.item_id = p.item_id
            WHERE o.customer_id = ?
            ORDER BY o.order_date DESC
        """, (customer_id,)).fetchall()

    return {
        "customer": dict(customer),
        "orders": [dict(r) for r in orders],
    }


@app.get("/api/inventory")
def get_inventory():
    """All inventory lots."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT i.*, p.product_name, p.category
            FROM inventory i
            JOIN products p ON i.item_id = p.item_id
            ORDER BY i.item_id, i.expiration_date
        """).fetchall()
    return [dict(r) for r in rows]


@app.get("/api/compatibility")
def get_compatibility():
    """All compatibility relationships."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT pc.*,
                   pa.product_name as part_a_name,
                   pb.product_name as part_b_name
            FROM product_compatibility pc
            JOIN products pa ON pc.part_a = pa.item_id
            JOIN products pb ON pc.part_b = pb.item_id
            ORDER BY pc.compatibility_type, pc.part_a
        """).fetchall()
    return [dict(r) for r in rows]


# Serve static files and index.html
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/")
def serve_frontend():
    """Serve the frontend."""
    return FileResponse("static/index.html")
