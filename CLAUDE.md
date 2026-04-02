# CLAUDE.md — Qosina Round 4: Three Use Case Demos

## WHAT THIS IS

This is Round 4 of a job interview at Qosina (medical device component distributor, Ronkonkoma, NY). I'm interviewing for Enterprise Applications & Automation Engineer. The interviewers are Tom Livingston (Director of Enterprise Applications — my future boss) and DJ Rettman (EVP/CIO/CTO).

Tom sent a project brief with three real business automation use cases from AI workshops with department stakeholders. He said "you do not need to build anything — just present your thinking." We're building working demos anyway because that's what won Round 3.

**Round 3 context:** I built a one-day demo (this repo's existing code) with a Claude-powered AI agent that queries Qosina's product catalog and inventory, with a human-in-the-loop approval queue. It's live at https://qosina-demo-production.up.railway.app. Tom said he hadn't seen that level of effort in a long time. That demo is the foundation we're expanding.

**Round 4 goal:** Expand the existing demo into three use-case-specific demos, all under one app with tab navigation and a shared approval queue. Deploy to Railway with one live URL. Present on a 90-minute Teams call (~25-30 min per use case).

## THE THREE USE CASES

### Use Case 1: Automate Sales Order Entry from Emails & Documents
**Department:** Customer Experience (CX)
**Problem:** POs arrive via email in diverse formats (PDFs, typed emails, scans, handwritten). Staff manually reads each one and keys it into D365 F&O as a sales order.
**What we demo:** Paste/upload a PO → AI extracts customer, part numbers, quantities, pricing → fuzzy matches against product catalog and customer master → confidence scores per field → human reviews in approval queue → approve creates the order.
**Key tools:** match_customer, match_products, validate_pricing, parse_po_text
**Key concepts:** Fuzzy matching against 5000+ SKU catalog, confidence scoring, handling edge cases (partial orders, new customers, pricing mismatches)

### Use Case 2: Automate Accounts Payable Processing
**Department:** Finance
**Problem:** Three sub-problems: (A) Cash application — matching incoming payments to open invoices, handling penny discrepancies and partial payments. (B) Three-way invoice matching — PO vs receipt vs invoice comparison. (C) Collections prioritization — which overdue accounts to chase first.
**What we demo:** View invoices → AI runs three-way match against PO and receipt → shows discrepancies with tolerance rules → auto-approves within threshold, flags exceptions → collections scoring ranks overdue accounts by risk.
**Key tools:** three_way_match, match_payment, check_discrepancies, score_collections
**Key concepts:** Tolerance thresholds (auto-approve under $0.05 variance), partial payments, penny discrepancies from rounding, line-item vs header-level matching

### Use Case 3: New Product Data Entry from Supplier Documents
**Department:** Product Development
**Problem:** Suppliers send spec sheets, certificates of analysis, catalogs, technical drawings. Staff manually extracts 30+ fields per SKU and enters them into D365 item master. With 8,000+ SKUs, this is a huge time investment.
**What we demo:** Upload/paste supplier spec sheet → AI extracts fields → applies "constitutional framework" (Qosina naming conventions) to normalize data → validates consistency against existing catalog → human reviews side-by-side (original doc | normalized fields) → approve creates item master record.
**Key tools:** extract_fields, normalize_to_conventions, validate_consistency, find_similar_products
**Key concepts:** Constitutional framework (non-negotiable naming rules the AI must follow), consistency validation against 8,000+ existing SKUs, 30+ fields per product

## EXISTING CODEBASE — WHAT'S ALREADY HERE

The Round 3 demo is fully functional. DO NOT break what works. Build on top of it.

### Existing files and what they do:

**backend/database.py** — SQLite with context manager, Row factory, init_db creates tables. KEEP THIS. Add new tables alongside existing ones.

**backend/tools.py** — 7 pure functions returning OData-formatted dicts. No LangGraph dependency. Unit testable.
- search_products(query) — LIKE search across product fields
- check_inventory(part_number) — lot-level inventory with expiration dates
- find_compatible_parts(part_number) — compatibility relationships
- check_expiring_inventory(days_ahead) — lots expiring within N days
- check_low_stock() — parts below reorder point
- get_customer_order_history(customer_id) — order history with revenue totals
- create_approval(type, title, content) — THE ONE WRITE TOOL. Creates pending approval queue items.

**backend/agent.py** — Creates LangGraph ReAct agent with ChatAnthropic, binds all 7 tools, has a detailed system prompt. Uses `create_react_agent` from `langgraph.prebuilt`.

**backend/main.py** — FastAPI app with:
- POST /api/chat — SSE streaming endpoint using `agent.astream_events()`
- GET /api/approvals — list all approval items
- PATCH /api/approvals/{id} — approve/reject
- DELETE /api/approvals/resolved — clear non-pending items
- GET /api/stats — dashboard counts
- GET /api/dashboard — alert counts (low stock, expiring, at-risk customers)
- GET /api/products, /api/customers, /api/inventory, /api/compatibility — data explorer endpoints
- Serves static/index.html at /

**backend/seed.py** — Seeds 29 real Qosina products, inventory with lot numbers and expiration dates, 6 customers, order history, compatibility relationships. ALL REAL PART NUMBERS from qosina.com.

**backend/models.py** — ChatRequest(message, conversation_id) and ApprovalUpdate(status, reviewed_by).

**static/index.html** — Single-page app with Tailwind CDN. Three tabs: Dashboard, AI Chat, Data Explorer. Right sidebar: approval queue with approve/reject, type filters, status tabs. Tool activity panel in chat. ~1100 lines of HTML/JS.

**Dockerfile, docker-compose.yml, railway.toml** — Railway deployment config.
- Dockerfile: python:3.12-slim, runs `python -m backend.seed` at build time (DB baked into image), uvicorn on 0.0.0.0:8000
- docker-compose.yml: maps port 8085 (host) → 8000 (container), mounts qosina.db as volume, loads .env
- .dockerignore: excludes .md files (except requirements.txt), .env, .pyc, .git, qosina.db
- **Important:** seed runs during `docker build`, so any schema or data changes require a rebuild

**tests/test_tools.py** — Unit tests for all 7 tool functions.

### Existing database schema:
- products (item_id PK, product_name, category, description, connection_type, material, technical_detail, iso_compliance, manufacturing_environment, shelf_life_months, shelf_life_post_irradiation_months, unit_price, minimum_order_qty, status)
- product_compatibility (id PK, part_a FK, part_b FK, compatibility_type, notes)
- inventory (id PK, item_id FK, lot_number, quantity_on_hand, warehouse_location, received_date, expiration_date, reorder_point, reorder_quantity)
- customers (customer_id PK, company_name, contact_name, industry, region, account_tier)
- order_history (order_id PK, customer_id FK, item_id FK, quantity, order_date, unit_price, total_price)
- approval_queue (id PK, recommendation_type, title, content, source_query, status, ai_generated_at, reviewed_by, reviewed_at)

## WHAT WE'RE BUILDING — THE CHANGES

### 1. OpenRouter LLM Provider Layer (NEW FILE)

Create `backend/shared/llm_provider.py`:

```python
"""LLM provider factory — OpenRouter (production) vs direct Claude (dev)."""

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic


def get_model(temperature: float = 0):
    """
    Returns a LangChain chat model.
    
    USE_OPENROUTER=true (default, production): Routes through OpenRouter.
    Claude primary, automatic failover to GPT-4o/Gemini if Claude is down.
    
    USE_OPENROUTER=false (local dev): Direct Claude API, no routing overhead.
    """
    if os.getenv("USE_OPENROUTER", "true").lower() == "true":
        return ChatOpenAI(
            model=os.getenv("PRIMARY_MODEL", "anthropic/claude-sonnet-4-20250514"),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=temperature,
            default_headers={
                "HTTP-Referer": os.getenv("APP_URL", "https://qosina-demo-production.up.railway.app"),
                "X-Title": "Qosina Enterprise AI Assistant"
            },
        )
    else:
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=temperature,
        )
```

**Why OpenRouter:** Tom and I specifically discussed LLM routing for API failover in the Round 3 interview. If Claude's API goes down, OpenRouter automatically routes to GPT-4o or Gemini. Zero downtime. The agent, tools, and approval queue don't know or care which model is answering — OpenRouter is OpenAI-compatible so LangChain's ChatOpenAI works directly.

**Add to requirements.txt:** `langchain-openai>=0.3.0`

**Add to .env:**
```
OPENROUTER_API_KEY=sk-or-v1-...
USE_OPENROUTER=true
PRIMARY_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...   # fallback for local dev
```

### 2. Per-Use-Case Agents (NEW FILES)

Each use case gets its own agent.py and tools.py. They all import `get_model()` from the shared provider.

**Pattern for each agent:**

```python
# backend/use_case_N/agent.py
from backend.shared.llm_provider import get_model
from langgraph.prebuilt import create_react_agent

SYSTEM_PROMPT = """..."""  # Use-case-specific prompt

TOOLS = [...]  # Use-case-specific tools

def create_uc_N_agent():
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
```

**Pattern for each tools.py:** Same as existing — pure functions returning OData-formatted dicts. No LangGraph imports. Testable independently.

### 3. Expanded Database Schema (MODIFY database.py)

Add to init_db() — DO NOT remove existing tables:

```sql
-- USE CASE 1: Sales Order Entry (expand existing customer/product data)
CREATE TABLE IF NOT EXISTS customer_pricing (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    item_id TEXT NOT NULL REFERENCES products(item_id),
    contracted_price REAL NOT NULL,
    discount_pct REAL DEFAULT 0,
    effective_date TEXT,
    expiry_date TEXT
);

-- USE CASE 2: AP Processing
CREATE TABLE IF NOT EXISTS vendors (
    vendor_id TEXT PRIMARY KEY,
    vendor_name TEXT NOT NULL,
    contact_name TEXT,
    payment_terms TEXT DEFAULT 'Net 30',
    region TEXT
);

CREATE TABLE IF NOT EXISTS purchase_orders (
    po_number TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
    order_date TEXT NOT NULL,
    expected_date TEXT,
    status TEXT DEFAULT 'confirmed',
    total_amount REAL
);

CREATE TABLE IF NOT EXISTS po_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    po_number TEXT NOT NULL REFERENCES purchase_orders(po_number),
    item_id TEXT NOT NULL REFERENCES products(item_id),
    quantity_ordered INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS receipts (
    receipt_id TEXT PRIMARY KEY,
    po_number TEXT NOT NULL REFERENCES purchase_orders(po_number),
    received_date TEXT NOT NULL,
    received_by TEXT
);

CREATE TABLE IF NOT EXISTS receipt_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    receipt_id TEXT NOT NULL REFERENCES receipts(receipt_id),
    item_id TEXT NOT NULL REFERENCES products(item_id),
    quantity_received INTEGER NOT NULL,
    lot_number TEXT
);

CREATE TABLE IF NOT EXISTS vendor_invoices (
    invoice_id TEXT PRIMARY KEY,
    vendor_id TEXT NOT NULL REFERENCES vendors(vendor_id),
    po_number TEXT REFERENCES purchase_orders(po_number),
    invoice_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    status TEXT DEFAULT 'pending',
    match_status TEXT DEFAULT 'unmatched'
);

CREATE TABLE IF NOT EXISTS invoice_lines (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id TEXT NOT NULL REFERENCES vendor_invoices(invoice_id),
    item_id TEXT NOT NULL REFERENCES products(item_id),
    quantity_invoiced INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    line_total REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS customer_invoices (
    invoice_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    invoice_date TEXT NOT NULL,
    due_date TEXT NOT NULL,
    total_amount REAL NOT NULL,
    amount_paid REAL DEFAULT 0,
    status TEXT DEFAULT 'open'
);

CREATE TABLE IF NOT EXISTS payments (
    payment_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    payment_date TEXT NOT NULL,
    amount REAL NOT NULL,
    reference TEXT,
    applied_to TEXT,
    status TEXT DEFAULT 'unapplied'
);

-- USE CASE 3: Product Data Entry (expand products table)
-- Add columns to products if they don't exist. Since SQLite doesn't support
-- IF NOT EXISTS on ALTER TABLE, we'll create an expanded_product_fields table
-- and join when needed.
CREATE TABLE IF NOT EXISTS product_extended (
    item_id TEXT PRIMARY KEY REFERENCES products(item_id),
    inner_diameter_mm REAL,
    outer_diameter_mm REAL,
    length_mm REAL,
    weight_g REAL,
    color TEXT,
    tolerance TEXT,
    sterilization_compatibility TEXT,
    biocompatibility TEXT,
    country_of_origin TEXT,
    supplier_part_number TEXT,
    tariff_code TEXT,
    units_per_case INTEGER,
    lead_time_days INTEGER,
    vendor_id TEXT
);

CREATE TABLE IF NOT EXISTS naming_conventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    field_name TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    pattern TEXT NOT NULL,
    example_correct TEXT,
    example_incorrect TEXT
);
```

### 4. Expanded main.py (MODIFY)

Add a `use_case` parameter to the chat endpoint:

```python
@app.post("/api/chat")
async def chat(request: ChatRequest):
    conversation_id = request.conversation_id or str(uuid.uuid4())
    use_case = getattr(request, 'use_case', 'general')
    
    # Select the right agent based on use case
    agent = get_agent(use_case)
    
    async def event_generator():
        async for event in stream_agent_response(agent, request.message, conversation_id):
            yield event
    
    return EventSourceResponse(event_generator())
```

Update ChatRequest model:
```python
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    use_case: Optional[str] = "general"  # "general", "sales_orders", "ap_processing", "product_data"
```

Create an agent registry:
```python
from backend.use_case_1.agent import create_uc1_agent
from backend.use_case_2.agent import create_uc2_agent
from backend.use_case_3.agent import create_uc3_agent
from backend.agent import create_agent as create_general_agent

agents = {}

def get_agent(use_case: str):
    if use_case not in agents:
        if use_case == "sales_orders":
            agents[use_case] = create_uc1_agent()
        elif use_case == "ap_processing":
            agents[use_case] = create_uc2_agent()
        elif use_case == "product_data":
            agents[use_case] = create_uc3_agent()
        else:
            agents[use_case] = create_general_agent()
    return agents[use_case]
```

Modify `stream_agent_response` to accept an agent parameter instead of using the global one.

### 5. Frontend Changes (MODIFY index.html)

The current frontend has 3 tabs: Dashboard, AI Chat, Data Explorer.

**New structure:** 5 tabs:
1. **Dashboard** (keep existing — shows alerts, quick actions)
2. **Sales Order Entry** (UC1 — document paste/upload + extraction preview + confidence scores)
3. **AP Processing** (UC2 — invoice list + three-way match view + collections ranking)
4. **Product Data Entry** (UC3 — spec sheet upload + side-by-side extraction + constitutional rules applied)
5. **Architecture** (diagrams showing all three approaches for each use case — n8n, custom Python, Power Platform)

The approval queue sidebar stays on the right, shared across all tabs.

Add to the header status bar:
```
🟢 Primary: Claude Sonnet 4 (via OpenRouter) | Fallbacks: GPT-4o → Gemini
```

Each use case tab sends messages with the appropriate `use_case` parameter so the backend routes to the right agent.

### 6. Seed Data (NEW/EXPANDED)

**UC1 seeds:** Add customer_pricing records (contracted rates for top customers). Create 3-4 sample PO texts stored as constants that the UI can load as "sample documents."

**UC2 seeds:** Vendors (4-5), purchase orders with line items, receipts (some with quantity discrepancies vs PO), vendor invoices (some matching perfectly, some with penny discrepancies, some with line-item mismatches). Customer invoices and payments (some exact matches, some partial, some with no remittance info). INTENTIONALLY include edge cases: a $0.03 penny discrepancy, a partial payment covering 2 of 3 invoices, a vendor invoice for 500 units when receipt shows 480.

**UC3 seeds:** Expand product_extended with real dimensional data for existing products. Add naming_conventions rules (material naming, connection type formatting, dimension units, product name patterns). Create 2-3 sample supplier spec sheet texts.

### 7. Tests (NEW FILES)

One test file per use case, same pattern as existing test_tools.py:
- test_uc1_tools.py — test match_customer finds the right customer, match_products handles fuzzy input, validate_pricing catches mismatches
- test_uc2_tools.py — test three_way_match catches discrepancies, match_payment handles exact/partial/no-match cases, tolerance thresholds work
- test_uc3_tools.py — test normalize_conventions applies naming rules, validate_consistency catches deviations from catalog patterns

## BUILD ORDER

Do these in this exact order. Each step should be deployable.

1. **Create shared/llm_provider.py** — add langchain-openai to requirements.txt. Test that the existing agent still works through OpenRouter (tool calling + SSE streaming).

2. **Add use_case parameter to chat endpoint** — modify ChatRequest, modify main.py to route by use_case. The "general" use case should still use the existing agent. Test that existing functionality is unbroken.

3. **Add new database tables** — expand init_db(). Run seed with new data. Verify existing data is untouched.

4. **Build UC1** — agent, tools, seed data, sample POs. Add the Sales Order Entry tab to frontend. Test end-to-end: paste a PO → extraction → matching → approval.

5. **Build UC2** — agent, tools, seed data. Add the AP Processing tab. Test: view invoices → three-way match → discrepancy flagging → approval.

6. **Build UC3** — agent, tools, constitution rules, seed data, sample spec sheets. Add the Product Data Entry tab. Test: paste spec sheet → extraction → normalization → consistency check → approval.

7. **Add Architecture tab** — diagrams showing n8n and Power Platform versions of each use case alongside the custom Python version.

8. **Add OpenRouter status indicator to header.**

9. **Deploy to Railway. Test everything on the live URL.**

10. **Write tests for all new tools.**

## DESIGN PRINCIPLES

1. **Business logic in tools.py, orchestration in agent.py.** Tools are pure functions. No LangGraph dependency in tools. Unit testable independently.

2. **Agent cannot write to system of record.** The only write tool is create_approval. No tool modifies products, inventory, customers, vendors, invoices, or any other data table. Human-in-the-loop enforced architecturally.

3. **OData-formatted responses.** All tool return values structured like D365 OData JSON with @odata.context headers and PascalCase field names. This demonstrates that swapping SQLite for D365 OData API calls = URL + auth change, not architecture change.

4. **Each use case is self-contained.** UC1 tools don't import from UC2. Each agent has its own system prompt. The shared pieces are: database, LLM provider, approval queue, SSE streaming.

5. **OpenRouter for production resilience.** Claude primary → GPT-4o → Gemini failover chain. In local dev, set USE_OPENROUTER=false for direct Claude calls (faster iteration).

6. **Don't break what works.** The existing general agent, tools, seed data, and frontend tabs should continue to work. Add new capabilities alongside, don't replace.

## WHAT TO SAY IN THE INTERVIEW

For each use case:
"Here's a working demo. The database is seeded with your product catalog — real part numbers, real specs. The AI agent runs through OpenRouter with Claude as primary and automatic failover to GPT-4o if Claude goes down — that's the API failover pattern we talked about last time. Every recommendation goes through the approval queue — the agent physically cannot modify the system of record. In production, swap SQLite for D365 OData endpoints and deploy to Azure. The agent, tools, streaming, and approval workflow stay identical."

Then show the architecture diagrams for the n8n and Power Platform versions, explain trade-offs, and give your recommendation for that specific use case.

## TECH STACK

| Layer | Technology | Notes |
|-------|-----------|-------|
| Backend | FastAPI (Python 3.11+) | Async, SSE support |
| AI Agent | LangGraph ReAct + Claude via OpenRouter | create_react_agent from langgraph.prebuilt |
| LLM Routing | OpenRouter | Claude primary, GPT-4o/Gemini failover |
| Database | SQLite | OData-formatted responses, seeds real Qosina data |
| Frontend | Single HTML + Tailwind CDN + vanilla JS | No build step, served by FastAPI |
| Streaming | Server-Sent Events (SSE) | sse-starlette, native EventSource |
| Observability | LangSmith (optional) | Agent tracing |
| Deployment | Docker → Railway | Live URL for interview screen share |
| Tests | pytest | Pure function tools, no mocking needed |

## DEPENDENCIES (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sse-starlette>=1.8.0
langchain-anthropic>=0.3.0
langchain-openai>=0.3.0
langgraph>=0.2.0
langchain-core>=0.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## HOW TO RUN

**Local without Docker:**
```bash
pip install -r requirements.txt
python -m backend.seed              # Seed database (run once, or after schema changes)
uvicorn backend.main:app --reload --port 8000
# Open http://localhost:8000
```

**Local with Docker (uses port 8085):**
```bash
docker-compose up --build
# Open http://localhost:8085
```

**Docker setup:**
- Dockerfile: builds on python:3.12-slim, runs seed at build time, exposes 8000 internally, uvicorn on 0.0.0.0:8000
- docker-compose.yml: maps 8085→8000, mounts qosina.db as volume, loads .env
- Railway: uses Dockerfile CMD directly. Railway assigns its own PORT — if Railway requires dynamic port binding, change the CMD to: `CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8000}`

## ENV VARS (.env)

```
OPENROUTER_API_KEY=sk-or-v1-...
USE_OPENROUTER=true
PRIMARY_MODEL=anthropic/claude-sonnet-4-20250514
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls-...          # Optional
LANGSMITH_PROJECT=qosina-round4   # Optional
LANGCHAIN_TRACING_V2=true         # Optional
```
