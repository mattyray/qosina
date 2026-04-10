# CLAUDE.md — Qosina Round 4 Demo

## WHAT THIS IS

Round 4 of a job interview at Qosina (medical device component distributor, Ronkonkoma, NY) for **Enterprise Applications & Automation Engineer**. Interviewers: **Tom Livingston** (Director of Enterprise Applications, future boss) and **DJ Rettman** (EVP/CIO/CTO).

Tom sent a project brief with three real automation use cases from AI workshops with department stakeholders. He said "you do not need to build anything, just present your thinking." We built working demos anyway.

**Live URL:** https://qosina-demo-production.up.railway.app
**Repo:** https://github.com/mattyray/qosina
**Interview:** Week of 2026-04-13 (90-min Teams call)

## CURRENT STATE — WHAT'S ACTUALLY BUILT

### The Three Use Cases (all working end-to-end)

**UC1 — Sales Order Entry** (CX Department)
- Drop a PO file (PDF, image, handwritten photo) or paste text into chat
- Agent extracts fields, fuzzy matches customer, fuzzy matches products against 5,000+ SKUs, validates pricing against contracted rates, checks inventory
- Creates structured approval with confidence scores per field
- Tools: `match_customer`, `match_products`, `validate_pricing`, `check_inventory`, `get_sample_pos`

**UC2 — AP Processing** (Finance Department)
- Three sub-processes: three-way invoice matching, cash application, collections prioritization
- Drop a vendor invoice PDF or remittance — agent parses it and runs against system data
- Tolerance thresholds: under $0.05 → auto-approve, $0.05-$50 → quick review, over $50 → full review
- Tools: `get_vendor_invoices`, `three_way_match`, `get_unapplied_payments`, `match_payment`, `score_collections`

**UC3 — Product Data Entry** (Product Development)
- Drop a supplier spec sheet or paste text
- Agent extracts fields, applies the **constitutional framework** (Qosina naming rules stored in DB), normalizes terminology, validates consistency against existing catalog
- Constitutional rules: "PC plastic" → "Polycarbonate (PC)", "M Luer" → "Male Luer Lock", inches → millimeters, etc.
- Tools: `get_naming_conventions`, `find_similar_products`, `validate_consistency`, `get_sample_spec_sheets`

### Architecture

```
User → FastAPI → LangGraph ReAct Agent → OpenRouter → Claude/GPT-4o/Gemini
                       ↓
                   Per-UC Tools (match, validate, score)
                       ↓
                   SQLite (OData-formatted, mocks D365)
                       ↓
                   Approval Queue (HITL — agent cannot write to system of record)
```

### File Structure

```
backend/
├── shared/
│   └── llm_provider.py        # OpenRouter factory, runtime model switching
├── use_case_1/
│   ├── agent.py               # UC1 ReAct agent + system prompt
│   └── tools.py               # match_customer, match_products, validate_pricing
├── use_case_2/
│   ├── agent.py               # UC2 ReAct agent
│   └── tools.py               # three_way_match, match_payment, score_collections
├── use_case_3/
│   ├── agent.py               # UC3 ReAct agent
│   └── tools.py               # naming_conventions, find_similar, validate_consistency
├── agent.py                   # General agent (Round 3 — still works)
├── main.py                    # FastAPI app — chat, upload, approvals, model switching
├── models.py                  # Pydantic ChatRequest, ApprovalUpdate
├── database.py                # SQLite + 17 tables (Round 3 + UC1/UC2/UC3)
├── tools.py                   # General agent's 7 tools (Round 3)
├── seed.py                    # Seeds all data including UC2 vendors/POs/invoices
└── pdf_utils.py               # PyMuPDF: render PDF pages to base64 PNG for Claude

static/
└── index.html                 # Single-page app: 7 tabs + review panel + approval queue

sample_docs/
├── uc1_sales_orders/          # 6 sample POs (PDF, handwritten, email body, etc.)
├── uc2_ap_processing/         # 7 vendor invoices, remittance, bank statement
└── uc3_product_data/          # 5 spec sheets, certificate of analysis, catalog

tests/
├── test_tools.py              # General agent tools (Round 3)
├── test_uc1_tools.py          # 13 UC1 tests
├── test_uc2_tools.py          # 15 UC2 tests
└── test_uc3_tools.py          # 14 UC3 tests

docs/                          # Project documentation and prep notes
generate_samples.py            # Generates all sample PDFs/images
```

### Database Tables (17 total)

**Round 3 (6):** products, product_compatibility, inventory, customers, order_history, approval_queue

**UC1 (1):** customer_pricing — contracted rates per customer/product

**UC2 (9):** vendors, purchase_orders, po_lines, receipts, receipt_lines, vendor_invoices, invoice_lines, customer_invoices, payments

**UC3 (2):** product_extended (30+ fields per SKU), naming_conventions (constitutional framework rules)

### API Endpoints

**Chat & Upload:**
- `POST /api/chat` — SSE streaming, accepts `use_case` param to route to UC1/UC2/UC3/general agent
- `POST /api/upload` — multipart file upload (PDF/image), renders PDFs via PyMuPDF, sends as multimodal to Claude

**Approvals:**
- `GET /api/approvals` — list all (sidebar fetches every 5s)
- `PATCH /api/approvals/{id}` — approve/reject/undo, accepts edited `structured_data`
- `DELETE /api/approvals/resolved` — clear non-pending

**Model Switching:**
- `GET /api/model` — current model + available models
- `PUT /api/model` — switch active model at runtime, clears agent cache

**Data Explorer:**
- `GET /api/products`, `/api/customers`, `/api/inventory`, `/api/compatibility`
- `GET /api/stats`, `/api/dashboard`

### Frontend Features

**7 tabs** (top): Dashboard, Sales Order Entry (UC1), AP Processing (UC2), Product Data Entry (UC3), General Chat, Data Explorer, Architecture

**Header:**
- Live model selector dropdown — switch Claude/GPT-4o/Gemini during demo
- Clean Qosina branding

**Left sidebar:**
- Dynamic agent tools panel — updates per active tab to show that UC's tools
- Live activity log — tool calls highlight as the agent uses them

**Center (chat area):**
- Unified input bar — type, paste text, paste image (Cmd+V), drag-drop file, paperclip button
- Per-tab conversation history (follow-ups work within a UC tab)
- Inline approval cards in chat stream — yellow card appears when agent creates approval
- Streaming markdown rendering with tool call highlights

**Right sidebar (approval queue):**
- Auto-filters to active tab's approval types
- Default-collapsed cards with title + type badge + "Review & Edit" button
- Pending/Approved/Rejected status tabs
- Undo button on resolved cards

**Review panel** (opens when clicking "Review & Edit"):
- Left: AI Summary tab + Original Document tab (with fullscreen expand)
- Right: Editable form fields with confidence-colored borders
  - Green border = high confidence (95%+)
  - Yellow border = medium (70-94%)
  - Red border = low confidence (<70%) — needs review
- Line items as editable table rows
- Section grouping for UC3 (Basic Info, Dimensions, Connections, Compliance, Commercial)
- Approve / Reject buttons at top — saves edited structured data with the approval

**Architecture tab** (11-section interview reference with sticky TOC):
1. Stack at a Glance — tech choices + boring plumbing
2. Human in the Loop — zero-write enforcement
3. The Three Use Cases — per-UC business problem + what was built + platform comparison + recommendation
4. The Tools — 20 read-only + 1 write across 4 agents
5. Approval Types — 5 types, "4-line change" extensibility
6. AP Processing Primer — money in/out/late framework
7. OpenRouter — resilience story, Claude-is-already-in-your-stack callout
8. Production Path — demo-vs-production table + D365 F&O/CE entity mapping + Celigo iPaaS integration
9. Observability & Audit — Entra ID, structured logging, LangSmith, FDA audit trail
10. Phased Rollout — UC1 first (foundation), UC2 second (dollar impact), UC3 third (reasoning-heavy)
11. Honest Gaps — 9 explicit gaps acknowledged upfront
- Recommendations per use case: UC1 = n8n + Python, UC2 = Power Platform + Python, UC3 = Full Python

**Agent prompt architecture** (added fc0743b):
- Each UC agent's system prompt includes an **HONESTY RULE** (permission to say "I don't know"), **GROUND TRUTH** (actual demo architecture, actual production recommendations, explicit list of things never to say), and **KNOWN DEMO DOCUMENTS** (per-sample-doc reference so the agent can explain what it demonstrated when asked)

## TECH STACK

| Layer | Technology |
|-------|-----------|
| Backend | FastAPI (Python 3.12), async SSE |
| AI Agent | LangGraph ReAct (`create_react_agent`) |
| LLM Provider | OpenRouter (Claude Sonnet 4 primary, GPT-4o + Gemini 2.5 Flash failover) |
| Document AI | Claude vision (PDFs rendered to PNG via PyMuPDF) |
| Database | SQLite with OData-formatted responses (mocks D365 F&O) |
| Frontend | Single HTML + Tailwind CDN + vanilla JS (no build step) |
| File Upload | python-multipart, fpdf2 + PyMuPDF + Pillow for sample doc generation |
| Streaming | sse-starlette, native EventSource |
| Deployment | Docker → Railway (auto-deploy from GitHub main) |
| Tests | pytest — 64 tests across 4 test files |

## ENV VARS (.env locally, Railway dashboard in prod)

```
OPENROUTER_API_KEY=sk-or-v1-...
USE_OPENROUTER=true
PRIMARY_MODEL=anthropic/claude-sonnet-4
ANTHROPIC_API_KEY=sk-ant-...   # optional fallback for local dev
```

## HOW TO RUN

**Local with Docker (port 8085):**
```bash
docker-compose up --build -d
# Open http://localhost:8085
```

**Generate sample documents:**
```bash
python3 generate_samples.py
```

**Run tests:**
```bash
pytest tests/
```

**Deploy to Railway:**
```bash
git push origin main   # auto-deploys
```

## DESIGN PRINCIPLES (still hold)

1. **Business logic in tools.py, orchestration in agent.py.** Tools are pure functions, no LangGraph dependency. Unit testable.
2. **Agent cannot write to system of record.** The only write tool is `create_approval`. Human-in-the-loop enforced architecturally.
3. **OData-formatted responses.** All tool returns mimic D365 OData JSON with `@odata.context` headers. Production swap = URL + auth change, not architecture change.
4. **Each use case is self-contained.** UC1 tools don't import from UC2. Shared pieces: database, LLM provider, approval queue, SSE streaming.
5. **Extensibility over hardcoding.** Field extraction is dynamic (Claude pulls whatever's in the doc). Naming rules stored as data. Tolerance thresholds configurable.
6. **OpenRouter for resilience.** Claude primary → GPT-4o → Gemini. Same agent code regardless of model.

## TOM'S BRIEF — KEY FEEDBACK (received 2026-04-03)

Tom answered Matt's clarifying questions. The big themes:

1. **PO formats** — PDFs, scanned, images, email body. Variety is the challenge. ✓ All handled.
2. **Sales order fields** — Standard B2B (ship-to, delivery, terms). Wants **extensible** extraction, not hardcoded. ✓ Claude extracts dynamically.
3. **Three-way match** — Line-item level. Partial receipts, qty/price variances. ✓ Built that way.
4. **Vendor invoice format** — Varies widely, like POs. Good AI use case. ✓ Same upload pipeline.
5. **Item master fields** — Not providing the list. Wants a **framework that handles any set of fields**. ✓ Dynamic extraction, no hardcoded list.
6. **Naming conventions** — Wants the **design pattern**, not specific rules. ✓ Rules stored as data, enforced in prompt + code.
7. **No sample documents** — "Use representative examples you create." ✓ Generated 18 sample docs.

**Key theme:** Extensibility and framework thinking over specific implementations. During presentation, lead with "this isn't hardcoded — adding a new field/rule is a config change, not a code change."

## INTERVIEW STRATEGY

**Build:** All three use cases as working Custom Python demos.
**Show:** Architecture diagrams for n8n and Power Platform versions.
**Recommend:** Different approach per use case, not "my stack for everything":
- UC1: Hybrid (n8n + Python)
- UC2: Power Platform + Python intelligence
- UC3: Full Custom Python

**Per use case (~25-30 min each):**
1. Business problem (30 sec)
2. Architecture diagram (1 min)
3. Live demo (5-7 min) — drop a doc, watch the agent process it, review and edit the approval, approve
4. Three-platform comparison (3-5 min)
5. Recommendation + reasoning (1-2 min)
6. Phased rollout (2-3 min)
7. Risks & unknowns (1-2 min)
8. Pattern connection to other UCs (1 min)

**Key demo moments:**
- Switch the LLM dropdown mid-demo from Claude to GPT-4o, process the same doc, show it works identically — proves model-agnostic architecture
- Open the Original Document tab in a review panel, click expand — shows full PDF viewer
- Edit a low-confidence (red) field, hit approve — shows HITL with corrections
- Show the Architecture tab diagrams when comparing n8n/PP/Python

## WHAT NOT TO DO

- Don't say "my stack is best for everything." Recommend Power Platform for UC2 to show enterprise maturity.
- Don't auto-approve anything in the demo without showing the human review step first.
- Don't pretend the constitutional framework rules are exhaustive — say "I'd codify Qosina's actual rules with the Product Development team in Phase 0."
- Don't skip the document upload step. Drop an actual PDF or photo each demo.
