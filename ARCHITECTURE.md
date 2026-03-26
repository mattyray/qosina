# ARCHITECTURE.md — Technical Architecture

## BACKEND API ENDPOINTS

### POST /api/chat
SSE streaming endpoint. Accepts a message from the user, runs the LangGraph agent, and streams back events.

**Request body:**
```json
{
    "message": "What stopcocks are compatible with part 80147?",
    "conversation_id": "optional-uuid"
}
```

**SSE event types streamed back:**

```
event: token
data: {"content": "Based on"}

event: token
data: {"content": " the compatibility"}

event: tool_call
data: {"tool": "find_compatible_parts", "input": {"part_number": "80147"}, "status": "calling"}

event: tool_result
data: {"tool": "find_compatible_parts", "result": {"@odata.context": "...", "value": [...]}, "status": "complete"}

event: token
data: {"content": "Part #80147 is compatible with..."}

event: approval_created
data: {"id": 1, "type": "reorder", "title": "Reorder Part #91050", "status": "pending"}

event: done
data: {"conversation_id": "uuid"}
```

### GET /api/approvals
Returns all approval queue items.

**Response:**
```json
[
    {
        "id": 1,
        "recommendation_type": "reorder",
        "title": "Reorder Part #91050 — High-Flow Check Valve",
        "content": "Current stock: 45 units. Reorder point: 100. Recommend ordering 500 units.",
        "source_query": "What parts are running low?",
        "status": "pending",
        "ai_generated_at": "2026-03-27T14:30:00Z",
        "reviewed_by": null,
        "reviewed_at": null
    }
]
```

### PATCH /api/approvals/{id}
Approve or reject an approval item.

**Request body:**
```json
{
    "status": "approved",
    "reviewed_by": "Tom Livingston"
}
```

### GET /api/stats
Database stats for the status bar.

**Response:**
```json
{
    "product_count": 28,
    "inventory_lots": 30,
    "pending_approvals": 3,
    "total_customers": 6
}
```

### GET /
Serves the static index.html frontend.

---

## LANGGRAPH AGENT DESIGN

### Agent setup (agent.py)

Use `create_react_agent` from langgraph.prebuilt with ChatAnthropic.

```python
from langchain_anthropic import ChatAnthropic
from langgraph.prebuilt import create_react_agent

model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)

# Tools are LangChain @tool decorated functions that call pure functions from tools.py
agent = create_react_agent(model, tools=[...], state_modifier=SYSTEM_PROMPT)
```

### Streaming

Use `agent.astream_events(...)` to get both token-level streaming and tool call events. Parse event types and forward as SSE events to the frontend:

- `on_chat_model_stream` → extract token → send as `event: token`
- `on_tool_start` → send as `event: tool_call` with status "calling"
- `on_tool_end` → send as `event: tool_result` with the output

### Tool binding

Tools are defined as LangChain `@tool` decorated functions. Each wraps a pure function from tools.py:

```python
from langchain_core.tools import tool
from backend.tools import search_products as _search_products

@tool
def search_products(query: str) -> str:
    """Search the Qosina product catalog by name, category, material, or connection type.
    Use this when a user asks about products, parts, or components."""
    result = _search_products(query)
    return json.dumps(result, indent=2)
```

### Conversation memory

For the demo, keep conversation history in a simple list per session. Use LangGraph's built-in message state. No persistent storage needed — demo conversations are short.

---

## TOOLS IMPLEMENTATION (tools.py)

Each function queries SQLite and returns a dict formatted as OData JSON.

### search_products(query: str) -> dict
```python
# SQL: SELECT * FROM products WHERE 
#   product_name LIKE '%query%' OR 
#   category LIKE '%query%' OR 
#   material LIKE '%query%' OR 
#   connection_type LIKE '%query%' OR
#   description LIKE '%query%'
# Return as OData format with @odata.context header
```

### check_inventory(part_number: str) -> dict
```python
# SQL: SELECT i.*, p.product_name FROM inventory i 
#   JOIN products p ON i.item_id = p.item_id
#   WHERE i.item_id = ?
# Also compute total_on_hand across all lots
# Flag if below reorder_point
# Return as OData InventoryOnHand format
```

### find_compatible_parts(part_number: str) -> dict
```python
# SQL: SELECT * FROM product_compatibility 
#   WHERE part_a = ? OR part_b = ?
# Then JOIN with products to get full product details for each compatible part
# Return with compatibility_type and notes
```

### check_expiring_inventory(days_ahead: int = 90) -> dict
```python
# SQL: SELECT i.*, p.product_name FROM inventory i
#   JOIN products p ON i.item_id = p.item_id
#   WHERE i.expiration_date IS NOT NULL 
#   AND i.expiration_date <= date('now', '+? days')
#   AND i.quantity_on_hand > 0
# Return sorted by expiration_date ascending
```

### check_low_stock() -> dict
```python
# SQL: SELECT item_id, SUM(quantity_on_hand) as total_on_hand, 
#   MIN(reorder_point) as reorder_point, MIN(reorder_quantity) as reorder_qty
#   FROM inventory GROUP BY item_id
#   HAVING total_on_hand < reorder_point
# JOIN with products for names
```

### get_customer_order_history(customer_id: str, months_back: int = 12) -> dict
```python
# SQL: SELECT o.*, p.product_name, c.company_name FROM order_history o
#   JOIN products p ON o.item_id = p.item_id
#   JOIN customers c ON o.customer_id = c.customer_id
#   WHERE o.customer_id = ? AND o.order_date >= date('now', '-? months')
# Order by order_date DESC
```

### create_approval(recommendation_type: str, title: str, content: str) -> dict
```python
# INSERT INTO approval_queue (recommendation_type, title, content, ai_generated_at, status)
# VALUES (?, ?, ?, datetime('now'), 'pending')
# Return the created record with its ID
```

---

## FRONTEND SPECIFICATION (static/index.html)

### Layout
- **Full viewport height**, no scrolling on the page itself
- **Header bar:** "Qosina Enterprise AI Assistant" left, "Powered by Claude • Human-in-the-Loop" right
- **Main area:** Two columns — 60% chat (left), 40% approval queue (right)
- **Chat column:** Messages area (scrollable), tool activity feed (collapsible, below messages), input bar (fixed bottom)
- **Approval column:** List of approval items with status badges, approve/reject buttons for pending items
- **Footer status bar:** Product count, inventory lot count, pending approval count

### Styling
- **Tailwind CSS via CDN:** `<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2.19/dist/tailwind.min.css" rel="stylesheet">`
- Or use Tailwind Play CDN: `<script src="https://cdn.tailwindcss.com"></script>`
- **Brand color:** #005DAA (Qosina blue) for header and accents
- **Clean, enterprise look.** White backgrounds. Gray borders. No rounded everything. Professional.
- **Message bubbles:** User messages right-aligned (blue), agent messages left-aligned (gray)
- **Tool activity:** Monospace font, subtle background, shows tool name + abbreviated input/output

### JavaScript
- **EventSource** for SSE connection to `/api/chat`
- **Fetch API** for approval CRUD and stats
- **No framework.** Vanilla JS with DOM manipulation.
- Handle SSE events: append tokens to current message, show tool calls in activity feed, add approvals to queue
- Poll `/api/stats` every 10 seconds for status bar updates
- Poll `/api/approvals` every 5 seconds to keep approval queue current

### Responsive
- On narrow screens, stack panels vertically (chat on top, approvals below)
- Not critical for demo — it'll be shown on a laptop via screen share

---

## ERROR HANDLING

- If Claude API fails, return an SSE event: `event: error` with a user-friendly message
- If a tool query fails (bad part number, etc.), the tool returns an informative error message that the agent can relay to the user
- Database connection errors get caught and returned as 500 responses
- CORS: Allow all origins for development (`allow_origins=["*"]`)

---

## OPTIONAL ENHANCEMENTS (if time allows)

1. **LangSmith integration** — Add tracing so you can show the agent trace in the interview
2. **Conversation ID persistence** — Allow refreshing without losing chat history
3. **Typing indicator** — Show "thinking..." while agent is processing before first token
4. **Export approval** — Button to "export" an approved recommendation (just logs it, shows the concept)
5. **Railway deployment** — Push to Railway for a live URL to share post-interview
