# CLAUDE.md — Qosina Enterprise AI Assistant Demo

## PURPOSE

This is an interview demo project. I'm interviewing at Qosina (medical device component distributor) for the role of Enterprise Applications & Automation Engineer. The interview is with DJ Rettman (EVP/CIO) and Tom Livingston (Director, Enterprise Applications — my future boss). I need a working prototype that demonstrates how I would build AI-powered agents for their enterprise systems.

**The demo concept:** A web application with a Claude-powered AI agent that queries Qosina's product catalog, inventory, and customer data — with a human-in-the-loop approval queue for all AI recommendations. I pull this up on screen share during the interview and walk them through it live.

**Time constraint:** Must be built in one day. Prioritize working functionality over polish. Get the agent + tools working first, then UI, then polish.

## ABOUT QOSINA

Qosina is a medical device component distributor founded in 1980, Ronkonkoma, NY. ~120 employees, ~$38M revenue. They buy medical device parts (stopcocks, luer connectors, check valves, tubing, clamps, etc.) in bulk from manufacturers worldwide, stock them in a warehouse on Long Island, and sell them to medical device OEMs so those companies don't have to tool their own parts. 5,000+ SKUs.

**Regulation:** Parts end up inside medical devices in human bodies. Every lot has tracking numbers, expiration dates, certificates of compliance. Part changes require customer notification (FDA). Data accuracy and traceability are regulatory requirements.

**ISO standards:** ISO 13485, ISO 9001, ISO 22301, ISO 14001, ISO 45001. 95,000 sq-ft facility, ISO Class 8 Clean Room.

**ISO 80369-7:** Connector standard for intravascular/hypodermic applications. Most Qosina luer connectors comply.

**Their tech stack:** D365 F&O (ERP), D365 CE (CRM), Celigo iPaaS (integration), PowerHouse WMS (warehouse), DynamicWeb (e-commerce), Azure (Synapse/Data Lake), Anthropic Claude + Microsoft Copilot (AI).

**What we demonstrate:** Claude-powered agent integrated with enterprise data. SQLite mocks D365 with OData-formatted JSON responses. Swapping SQLite for D365 OData API calls = config change, not architecture change.

## TECH STACK

| Layer | Technology | Why |
|-------|-----------|-----|
| Backend | FastAPI (Python 3.11+) | Native async, SSE support, fast scaffold |
| AI Agent | LangGraph + Claude (claude-sonnet-4-20250514) via langchain-anthropic | ReAct agent with tools — same as my production ToteTaxi |
| Database | SQLite | Zero config, file-based |
| Frontend | Single HTML file + Tailwind CSS CDN + vanilla JS | No build step, served by FastAPI |
| Streaming | Server-Sent Events (SSE) | Native EventSource, simple |

## PROJECT STRUCTURE

```
qosina-demo/
├── CLAUDE.md
├── SEED_DATA.md
├── ARCHITECTURE.md
├── DEMO_SCENARIOS.md
├── requirements.txt
├── .env                         # ANTHROPIC_API_KEY, optional LANGSMITH keys
├── backend/
│   ├── __init__.py
│   ├── main.py                  # FastAPI app — SSE endpoint, approval CRUD, serves static
│   ├── agent.py                 # LangGraph ReAct agent setup
│   ├── tools.py                 # Pure tool functions (business logic, unit testable)
│   ├── database.py              # SQLite setup, connection, queries
│   ├── seed.py                  # Seed script — run once to populate database
│   └── models.py                # Pydantic models
├── static/
│   └── index.html               # Single-page frontend
├── tests/
│   └── test_tools.py            # Unit tests for tool functions
└── qosina.db                    # Created by seed.py
```

## SYSTEM PROMPT FOR THE AGENT

```
You are a Qosina Enterprise AI Assistant with access to the product catalog, inventory system, compatibility database, and customer order history.

About Qosina: Qosina is a leading global supplier of over 5,000 OEM single-use components to the medical device and pharmaceutical industries. Founded in 1980, headquartered in Ronkonkoma, NY.

RULES:
1. Always cite specific part numbers (e.g., "Part #11195") in your responses.
2. NEVER modify data directly. You have NO tools that write to the product catalog, inventory, or customer records.
3. When you identify an action that should be taken (reorder, customer outreach, alert, draft response), ALWAYS use the create_approval tool to submit it for human review.
4. Include lot numbers and expiration dates when discussing inventory — required for FDA compliance traceability.
5. When discussing product compatibility, reference the connection type (e.g., "Female Luer Lock") and ISO compliance status.
6. If unsure about a product specification or compatibility, say so. Never guess about medical device component specs.
7. Be concise and professional. Users are enterprise staff who need fast, accurate answers.
```

## TOOLS — 7 Total (6 read-only, 1 creates approvals)

### 1. search_products(query: str) -> list[dict]
Full-text search across product catalog by name, category, material, connection type.

### 2. check_inventory(part_number: str) -> dict
Stock level, lot numbers, expiration dates, warehouse locations, reorder point for a specific part.

### 3. find_compatible_parts(part_number: str) -> list[dict]
Parts that connect to / work with a given part based on connection type.

### 4. check_expiring_inventory(days_ahead: int = 90) -> list[dict]
Inventory lots expiring within specified window.

### 5. check_low_stock() -> list[dict]
Parts where on-hand quantity is below reorder point.

### 6. get_customer_order_history(customer_id: str) -> list[dict]
Order history for a customer.

### 7. create_approval(recommendation_type: str, title: str, content: str) -> dict
Submit AI recommendation for human review. Types: "reorder", "customer_outreach", "expiry_alert", "draft_response", "general". This is the ONLY tool that creates data. Returns confirmation with approval ID and status "pending".

## KEY ARCHITECTURE DECISIONS

1. **Business logic in tools.py, orchestration in agent.py.** Tools are pure functions, no LangGraph dependency. Unit testable independently.
2. **Agent cannot write to system of record.** create_approval only creates pending items. No tool modifies products, inventory, or customers. Human-in-the-loop enforced architecturally.
3. **OData-formatted responses.** Tool return values structured like D365 OData JSON. Demonstrates that swapping to D365 API = URL + auth change.
4. **SSE streaming.** Text tokens → chat panel. Tool call events → tool activity feed. Single stream, two displays.

## DEPENDENCIES (requirements.txt)

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
sse-starlette>=1.8.0
langchain-anthropic>=0.3.0
langgraph>=0.2.0
langchain-core>=0.3.0
pydantic>=2.0.0
python-dotenv>=1.0.0
```

## ENV VARS (.env)

```
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls-...          # Optional
LANGSMITH_PROJECT=qosina-demo     # Optional
LANGCHAIN_TRACING_V2=true         # Optional — enables LangSmith
```

## HOW TO RUN

```bash
pip install -r requirements.txt
python backend/seed.py            # Seed the database (run once)
uvicorn backend.main:app --reload --port 8000
# Open http://localhost:8000
```

## FRONTEND LAYOUT

Single HTML page at `/`. Two-panel layout with tool activity feed and status bar. See ARCHITECTURE.md for full layout spec. Use Qosina brand blue (#005DAA) for headers. Clean, professional, enterprise look. Tailwind CSS via CDN. Vanilla JS with EventSource for SSE.

## WHAT TO SAY IN THE INTERVIEW

"I built this to show how I'd approach your use case. The database is seeded with your actual product catalog — real part numbers, real specs, real connection types. API responses are OData-formatted to match D365. In production, swap SQLite for D365 OData API calls, deploy to Azure. The agent, tools, streaming, and approval workflow stay identical."

"The key decision: the agent has no tool that writes to the system of record. It can only create approval items. That's enforced in code, not policy."

## REFERENCE FILES

- **SEED_DATA.md** — All product data, inventory, customers, orders, compatibility maps
- **ARCHITECTURE.md** — Detailed technical architecture, API endpoints, frontend spec
- **DEMO_SCENARIOS.md** — Scripted demo conversations for the interview
