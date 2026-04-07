# ARCHITECTURE.md — Technical Architecture (Round 4)

## SYSTEM OVERVIEW

```
                    ┌──────────────────────────┐
                    │     OpenRouter Gateway    │
                    │  Claude → GPT-4o → Gemini │
                    └────────────┬─────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
         ┌────▼─────┐      ┌────▼─────┐      ┌────▼─────┐
         │ UC1 Agent│      │ UC2 Agent│      │ UC3 Agent│
         │  Sales   │      │    AP    │      │ Product  │
         │  Orders  │      │ Process  │      │   Data   │
         └────┬─────┘      └────┬─────┘      └────┬─────┘
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │   Shared Approval Queue   │
                    │   (Human-in-the-Loop)     │
                    └────────────┬──────────────┘
                                 │
                    ┌────────────▼──────────────┐
                    │   SQLite (mocks D365)     │
                    │   OData-formatted JSON    │
                    └───────────────────────────┘
```

## BACKEND API ENDPOINTS

### Chat — `POST /api/chat`

SSE streaming endpoint. Routes to the right agent based on `use_case` param.

**Request:**
```json
{
  "message": "Process this PO",
  "conversation_id": "uuid-or-null",
  "use_case": "sales_orders"
}
```

`use_case` values: `general` (Round 3 agent), `sales_orders` (UC1), `ap_processing` (UC2), `product_data` (UC3)

**SSE events streamed back:**
```
event: token            → {"content": "incremental text"}
event: tool_call        → {"tool": "match_customer", "input": {...}, "status": "calling"}
event: tool_result      → {"tool": "match_customer", "status": "complete"}
event: approval_created → {"id": 1, "type": "sales_order", "title": "...", "status": "pending"}
event: error            → {"message": "friendly error"}
event: done             → {"conversation_id": "uuid"}
```

### File Upload — `POST /api/upload`

Multipart form upload for PDFs and images.

**Form fields:**
- `file` — the document
- `use_case` — which agent to route to
- `prompt` — optional text prompt to send with the file

**Backend pipeline:**
1. Read file bytes
2. If PDF: render each page to PNG via PyMuPDF (`fitz.Matrix(zoom)`, `pix.tobytes("png")`)
3. Base64-encode each page image
4. Construct multimodal `HumanMessage` with text prompt + image_url blocks
5. Pass to the selected agent via the same SSE streaming pipeline

### Approvals

- `GET /api/approvals` — list all (sidebar polls every 5s)
- `PATCH /api/approvals/{id}` — approve/reject/undo, accepts `structured_data` for edited fields
- `DELETE /api/approvals/resolved` — clear non-pending

### Model Switching

- `GET /api/model` — returns active model + available models
- `PUT /api/model` — body `{"model_id": "openai/gpt-4o"}`, sets active model and clears agent cache so next request rebuilds with new model

### Data Explorer

- `GET /api/products`, `/api/products/{id}`
- `GET /api/customers`, `/api/customers/{id}`
- `GET /api/inventory`, `/api/compatibility`
- `GET /api/stats`, `/api/dashboard`

## LANGGRAPH AGENT DESIGN

Each use case has its own agent created via `create_react_agent`. They all use the same LLM provider (`get_model()` from `backend/shared/llm_provider.py`) which routes through OpenRouter.

```python
from langgraph.prebuilt import create_react_agent
from backend.shared.llm_provider import get_model

def create_uc1_agent():
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
```

### LLM Provider

`backend/shared/llm_provider.py` is a factory that returns either:
- `ChatOpenAI` pointed at OpenRouter (production, default)
- `ChatAnthropic` direct (local dev, set `USE_OPENROUTER=false`)

A module-level `_active_model` variable allows runtime model switching via `set_active_model()`. The agent cache in `main.py` is cleared whenever the model changes so agents rebuild with the new model on next request.

### Streaming

Uses `agent.astream_events(version="v2")`. Parses event types and forwards as SSE:
- `on_chat_model_stream` → `event: token`
- `on_tool_start` → `event: tool_call`
- `on_tool_end` → checks if `create_approval` was called, fires `event: approval_created`, then `event: tool_result`

### Tool Pattern

Each UC has a `tools.py` (pure functions querying SQLite, no LangGraph imports) and an `agent.py` (LangChain `@tool` wrappers + system prompt).

```python
# backend/use_case_1/tools.py
def match_customer(name: str = "", email: str = "") -> dict:
    """Pure function — testable, no LangGraph dependency."""
    with get_db() as conn:
        # ... SQL query ...
    return {"@odata.context": "...", "value": [...], "BestMatch": {...}}

# backend/use_case_1/agent.py
@tool
def match_customer(name: str = "", email: str = "") -> str:
    """LangChain wrapper that calls the pure function."""
    return json.dumps(_match_customer(name, email), indent=2)
```

### Conversation Memory

`main.py` stores `conversations: dict[str, list]` mapping `conversation_id` → message list. Each chat request appends to the existing conversation, enabling follow-up questions within a session. Per-tab conversation IDs in the frontend mean each UC tab has its own context.

## STRUCTURED APPROVAL DATA

The approval queue table has a `structured_data TEXT` column storing JSON. When agents create approvals, they pass field-level data with confidence scores so the frontend can render an editable form.

**UC1 sales order format:**
```json
{
  "fields": {
    "customer_id": {"value": "CUST-001", "confidence": 0.95, "label": "Customer ID"},
    "po_number": {"value": "ACME-PO-2026-0412", "confidence": 0.99, "label": "PO Number"},
    "delivery_date": {"value": "2026-04-15", "confidence": 0.90, "label": "Delivery Date"}
  },
  "line_items": [
    {"item_id": "11195", "description": "1-Way Stopcock", "quantity": 500, "unit_price": 2.57, "confidence": 0.99}
  ],
  "total": 2231.00
}
```

**UC3 product entry format:** Grouped by section.
```json
{
  "sections": [
    {"name": "Basic Info", "fields": [
      {"key": "product_name", "label": "Product Name", "value": "...", "raw_value": "...", "confidence": 0.90, "rule_applied": "..."}
    ]},
    {"name": "Dimensions", "fields": [...]}
  ]
}
```

When the reviewer clicks Approve, the frontend gathers the edited values from the form inputs and PATCHes the approval with the updated `structured_data`.

## FRONTEND ARCHITECTURE

`static/index.html` is a single-page app with no build step.

**Layout (3 columns):**
- **Left (240px):** Dynamic agent tools panel — updates per active tab to show that UC's tools
- **Center (flex):** Tab content (Dashboard, UC1, UC2, UC3, Chat, Data Explorer, Architecture, Review Panel)
- **Right (380px):** Approval queue, auto-filtered by active tab

**Key JS state:**
```js
let ucConvIds = { uc1: null, uc2: null, uc3: null };  // per-tab conversation persistence
let ucFiles = { uc1: null, uc2: null, uc3: null };    // pending file attachments
let ucLastUpload = { uc1: null, uc2: null, uc3: null }; // data URLs for review panel
let activeUseCase = 'general';                         // for chat routing
let currentTabTypes = null;                            // for approval filtering
let reviewingApproval = null;                          // currently open in review panel
window._approvalDocs = {};                             // approval ID → source document data URL
```

**SSE handling:** A single `handleStream(response, container, typing)` function used by both text chat and file upload. Parses SSE events and updates the DOM in real time.

**File upload UX:**
- Paperclip button → file picker
- Drag-drop on input field or panel area
- Cmd+V on input → checks `clipboardData.files` (Finder copy) and `clipboardData.items` (image screenshots)
- File shows as a chip above the input until sent or cleared

**Review panel:**
- Two-column grid: doc viewer (left, with tab toggle for Summary vs Original Document) and editable form (right)
- Confidence-colored field borders (green/yellow/red)
- Fullscreen modal for the original document
- Approve/Reject buttons at top, save edited structured_data on approve

## DATABASE SCHEMA

17 tables total. See [SEED_DATA.md](SEED_DATA.md) for the full schema and seed data.

**Round 3 (6):** products, product_compatibility, inventory, customers, order_history, approval_queue (extended with `structured_data` column)

**UC1 (1):** customer_pricing — contracted rates per customer/product

**UC2 (9):** vendors, purchase_orders, po_lines, receipts, receipt_lines, vendor_invoices, invoice_lines, customer_invoices, payments

**UC3 (2):** product_extended (30+ fields per SKU), naming_conventions (constitutional framework rules)

## DEPLOYMENT

**Docker:**
- `python:3.12-slim` base
- Installs `requirements.txt`
- Runs `python -m backend.seed` at build time (DB baked into image)
- Exposes port 8000, uvicorn runs on `0.0.0.0`

**docker-compose.yml** maps host port 8085 → container 8000, loads `.env`

**Railway:**
- Auto-deploys from GitHub `main` branch
- Env vars set via `railway variables --set "KEY=value"`
- Live URL: https://qosina-demo-production.up.railway.app

## ERROR HANDLING

- API errors caught in `stream_agent_response` exception handler
- Friendly messages for: "overloaded" (Claude busy), "auth" (API key issue), generic fallback
- Verbose error message in dev shows the actual exception (truncated to 200 chars)
- Frontend shows error as red bubble in chat
- CORS allows all origins (`allow_origins=["*"]`)
