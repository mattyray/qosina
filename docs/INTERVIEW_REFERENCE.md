# INTERVIEW_REFERENCE.md

Printable backup of the Architecture tab content. If the demo crashes during the call, open this file and walk Tom through the same content from text.

## TABLE OF CONTENTS

1. [Stack at a Glance](#1-stack-at-a-glance)
2. [Human-in-the-Loop Pattern](#2-human-in-the-loop-pattern)
3. [The 21 Tools (20 Read-Only + 1 Write)](#3-the-21-tools)
4. [The Five Approval Types](#4-the-five-approval-types)
5. [AP Processing Primer](#5-ap-processing-primer)
6. [Per-UC Architecture: Three Approaches Compared](#6-per-uc-architecture)
7. [OpenRouter Story](#7-openrouter-story)
8. [Production Path: What Changes](#8-production-path)
9. [Observability & Audit](#9-observability--audit)
10. [Honest Gaps: What This Demo Is NOT](#10-honest-gaps)
11. [Phased Rollout Plan](#11-phased-rollout-plan)

---

## 1. Stack at a Glance

If you read nothing else, read this.

| Layer | Technology |
|---|---|
| Backend | FastAPI (Python 3.12), async SSE streaming |
| Agent Framework | LangGraph ReAct (`create_react_agent`) |
| LLM Provider | OpenRouter (Claude Sonnet 4 / GPT-4o / Gemini 2.5 Flash, switch live) |
| Document AI | Claude Vision (no OCR product). PyMuPDF renders PDFs to PNG before sending to Claude. |
| Database | SQLite, 17 tables, OData-shaped JSON responses (mocks D365) |
| Frontend | Single HTML + Tailwind CDN + vanilla JS, no build step |
| Streaming | Server-Sent Events (sse-starlette, native EventSource) |
| Deployment | Docker → Railway, auto-deploy from GitHub main |

**The point:** Same agent code regardless of model. Same approval queue regardless of use case. Architecture is identical end-to-end — only the tools and prompts differ per agent.

---

## 2. Human-in-the-Loop Pattern

The most important architectural decision in this demo. The agent has no write tools to the system of record. Even a perfect three-way match creates an approval card that a human must click.

**What the agent CAN do:**
- Read products, customers, inventory, orders
- Query vendor invoices, POs, receipts, payments
- Run three-way matches and pricing validation
- Score collections priority
- Apply naming conventions to spec sheets
- Create approval recommendations

**What the agent CANNOT do:**
- Create or modify products
- Update inventory or customer records
- Post sales orders to D365
- Apply payments or pay invoices
- Modify pricing or contracts
- Take ANY action without human approval

**Why:** Medical device supply chain. Every part Qosina ships ends up in a device that goes in a human body. Every approval needs a human signature for FDA traceability and regulatory audit. The architecture makes this impossible to bypass — the agent literally has no tools to modify the system of record. It's not policy, it's code.

---

## 3. The 21 Tools

Across 4 agents, 20 read-only tools query the database. Exactly ONE write tool (`create_approval`) is shared by all 4 agents.

### General Agent (Round 3) — 6 read-only
- `search_products`
- `check_inventory`
- `find_compatible_parts`
- `check_expiring_inventory`
- `check_low_stock`
- `get_customer_order_history`

### UC1 Sales Order Agent — 5 read-only
- `match_customer`
- `match_products`
- `validate_pricing`
- `check_inventory`
- `get_sample_pos`

### UC2 AP Processing Agent — 5 read-only
- `get_vendor_invoices`
- `three_way_match`
- `get_unapplied_payments`
- `match_payment`
- `score_collections`

### UC3 Product Data Agent — 4 read-only
- `get_naming_conventions`
- `find_similar_products`
- `validate_consistency`
- `get_sample_spec_sheets`

### + 1 Write Tool: `create_approval`
Shared across all 4 agents. The only way data gets written. Creates a row in `approval_queue` with structured field data, confidence scores, and source document reference. No bypass possible.

**Tools are pure Python functions** in `tools.py` with no LangGraph dependency. The `agent.py` file wraps them with `@tool` decorators. Business logic is testable in isolation — 42 unit tests run against the pure functions, no LLM mocking required.

---

## 4. The Five Approval Types

| Type | Use Case | What it answers |
|---|---|---|
| `sales_order` | UC1 | Should we accept this PO and create a sales order? |
| `invoice_match` | UC2 | Should we pay this vendor invoice? |
| `payment_application` | UC2 | Which invoice does this customer payment pay off? |
| `collection_outreach` | UC2 | Which overdue customer should we chase first? |
| `product_entry` | UC3 | Should we add this supplier product to our catalog? |

**UC1: 1 type** — One approval per PO, even if 50 line items. An order is one business object.

**UC2: 3 types** — AP is three distinct sub-jobs glued together: pay bills, apply payments, chase overdue.

**UC3: 1 type** — One approval per supplier doc. Catalog page with 3 products = 1 approval with sections.

**If they ask "could you add more types?":** Yes — adding a new type is a 4-line change. Add the type string to the agent's prompt, the frontend's tab type map, the badge color map, and (optionally) a new section renderer for the form. No schema migration. The `approval_queue.recommendation_type` is an open string field.

---

## 5. AP Processing Primer

AP = Accounts Payable. The financial plumbing of "money in, money out." Three sub-jobs.

| Direction | Sub-job | Approval type | The question |
|---|---|---|---|
| Money OUT | Three-way match | `invoice_match` | "Should we pay this bill?" |
| Money IN | Cash application | `payment_application` | "Which invoice does this payment pay off?" |
| Money LATE | Collections | `collection_outreach` | "Who should we chase first?" |

### Sub-job 1: Three-Way Matching (Money OUT)

**What it is:** Three docs need to agree before paying a vendor invoice:
1. **PO** — Qosina says: "We want 500 stopcocks at $3.95"
2. **Receipt** — Warehouse says: "We received 480 stopcocks"
3. **Invoice** — Vendor says: "Pay us for 500 stopcocks at $3.95 = $1,975"

**Why it matters:** Without it, you pay for parts that never arrived, get charged the wrong price, or pay duplicate invoices. #1 way money leaks out of a company.

**What the agent does:** Calls `three_way_match(invoice_id)`, compares line-by-line, creates an `invoice_match` approval that falls into:
- **Perfect match** → recommend fast-track
- **Penny variance <$0.05** → fast-track with write-off note
- **Quantity discrepancy** → HOLD, investigate (TechValve case: billed 500, got 480)
- **Price discrepancy** → HOLD, investigate (Allied case: $65 PO, $67.50 invoice)
- **Orphan invoice** → HOLD, do not pay (MedSupply case: PO doesn't exist)

### Sub-job 2: Cash Application (Money IN)

**What it is:** Customer sends Qosina a payment. Finance has to figure out which open invoice it pays off. Sounds simple but:
- Check arrives with no remittance advice ("$2,800 from someone, figure it out")
- One big payment supposed to cover three invoices
- Customer pays the wrong amount (deductions for damages, freight, early-payment discounts)
- Wire transfer from a payment processor with no clear customer ID

**Why it matters:** Until cash is applied, the customer's account still shows them as overdue even though they paid. You'll call them asking for money they already sent. AR numbers are wrong. Auditors are angry.

**What the agent does:** Calls `match_payment(payment_id)`, proposes allocation, creates a `payment_application` approval:
- **Exact match** → one open invoice equals the payment amount, apply it
- **Partial pay with deduction** → "MedLine paid $332.50 instead of $337.50, deducted $5 for damages"
- **Multi-invoice** → "$1,345 covers CINV-006 + CINV-007"
- **Mystery payment** → "$2,800 check from Unknown, two candidates, recommend phone call"

### Sub-job 3: Collections Prioritization (Money LATE)

**What it is:** Some customers don't pay on time. AP team has 200 overdue accounts and can't call them all today. Which to call first?

**Why naive sorting is bad:** Alphabetical = random. "Biggest amount first" ignores that a $50K customer who always pays late is less urgent than a $5K customer who's gone silent for 90 days.

**What good prioritization considers:**
- Amount owed
- Days overdue (risk shoots up after 90)
- Payment history (always-late but always-pays vs new risk)
- Account size (strategic value)
- Last contact (already called yesterday?)

**Why it matters:** DSO (Days Sales Outstanding) is one of the top metrics finance is measured on. Cutting DSO from 65 to 50 days = tens of thousands in cash flow improvement.

**What the agent does:** Calls `score_collections()`, ranks all overdue accounts, creates a `collection_outreach` approval per customer:
- **High** → "Acme, $12K overdue 75 days, late payer history, recommend phone call today"
- **Medium** → "BioFlow, $3K overdue 45 days, normally pays on time, recommend reminder email"
- **Low** → "Precision, $800 overdue 15 days, excellent history, monitor only"

### One-Sentence Summary

"It handles the three sub-jobs of accounts payable — deciding whether vendor invoices should be paid, deciding which customer payments apply to which invoices, and prioritizing which overdue accounts to chase first. Each one produces a recommendation that goes to a human in an approval queue. The AI doesn't post anything to the books — humans always click."

---

## 6. Per-UC Architecture

For each use case I evaluated n8n, Power Platform, and Custom Python. **Different recommendation per UC** — not "my stack for everything."

### UC1: Sales Order Entry
**Recommendation: Hybrid (n8n + Custom Python)**

- **n8n (Trigger Side):** Watch inbox for PO emails, extract attachments, route to Python webhook. Visual flow, business analyst maintainable.
- **Custom Python (AI Engine):** Claude vision parses any format, fuzzy match vs 5K SKUs, confidence scoring, full pytest coverage. *Built in this demo.*
- **Power Platform:** AI Builder is for structured forms, not 50 PO formats. Can't fuzzy match against 5K SKUs. Can't use Claude natively.

### UC2: AP Processing
**Recommendation: Power Platform + Custom Python**

- **n8n:** Could work, no advantage. D365 F&O needs HTTP node. No native D365 F&O connector.
- **Power Platform (Core):** Native D365 F&O connectors, built-in Approvals via Teams, audit trail for free, finance team already uses it. *The right call for UC2.*
- **Custom Python (Intelligence):** Cash app reasoning, collections risk scoring, Claude judgment calls. *Called from Power Automate.*

**Honest one-liner:** "Power Platform for the boring 90% Microsoft already built. Custom Python for the 10% that's actually novel."

### UC3: Product Data Entry
**Recommendation: Full Custom Python**

- **n8n:** AI Agent node available, but constitutional rules need code precision. Hard to test/validate.
- **Power Platform:** AI Builder not strong enough. Can't enforce naming rules precisely. Not Claude-native.
- **Custom Python (Full):** Constitutional rules in DB + prompt, validation in code (belt + suspenders), consistency check vs catalog, full Claude reasoning. *Built in this demo.*

Lower volume than UC1/UC2 — orchestration tax of n8n/Power Platform isn't worth it.

---

## 7. OpenRouter Story

Round 3 callback. We talked about LLM routing for failover. This is the implementation.

- **Claude Sonnet 4 (primary)** — Best reasoning for fuzzy matching, constitutional framework, complex extraction.
- **GPT-4o (failover)** — Auto-routes if Anthropic is down or rate-limited. ~25ms overhead.
- **Gemini 2.5 Flash (failover)** — Final fallback. Different provider, different region.

**Why it matters at Qosina:** Enterprise systems can't go down because a third-party LLM is having a bad day. One API key, one bill, one dashboard. Provider data policies enforced (no training on Qosina data).

**Demo move:** Switch the model dropdown in the header from Claude to GPT-4o mid-demo. Process the same PO. Show that the agent, tools, and approval queue work identically. The model is interchangeable — everything else is the same code.

---

## 8. Production Path

The architecture stays identical. Only integration points change.

| Layer | Demo (today) | Production (Qosina) |
|---|---|---|
| Database | SQLite + mock data | D365 F&O via OData REST API |
| Auth | None ("Demo User") | Entra ID OAuth + AD groups |
| File storage | Browser memory (data URLs) | Azure Blob with retention policies |
| Conversation history | In-memory dict (lost on restart) | Persisted SQL with FK to approvals |
| Logs | stdout / Docker logs | Application Insights + structured JSON |
| Error tracking | Generic catch-all | Sentry / App Insights with stack traces |
| Agent tracing | None (live activity panel) | LangSmith for full trace replay |
| Hosting | Railway (Docker) | Azure Container Apps (same Azure tenant as D365) |

**The point:** The OData-shaped tool responses make the database swap a config change — URL + auth, not a rewrite. Auth, observability, and audit are integration points, not architectural changes. Everything else stays the same.

---

## 9. Observability & Audit

Medical device compliance is non-negotiable. Every AI decision needs a paper trail.

### User Accounts (production)

Don't roll your own. Integrate with **Entra ID** via OAuth/OIDC. Every Qosina employee already has an account. JWT validated by FastAPI middleware, user attached to each request. Authorization comes from **AD groups** — "AP_Approver" can approve invoice matches, "CX_Manager" can approve sales orders, etc.

Demo has no auth. In production this is a Phase 1 integration.

### Troubleshooting FastAPI in Production

- **Structured JSON logging** → Azure Log Analytics (Qosina is on Azure)
- **Sentry** for error tracking — every uncaught exception captured with context
- **Application Insights** for APM — latency, error rates, dependency tracing
- **Health endpoint** `/health` for Railway/Azure liveness probes
- **LangSmith** for AI traces — the most important one

### Auditing the AI Agent

For regulated industries, every conversation needs to be replayable. The architecture:

1. **Persist every conversation** to a `conversations` + `conversation_messages` table
2. **Link approvals to conversations** via FK on `approval_queue`
3. **Store source documents** in Azure Blob with the approval record
4. **Immutable audit log** (write-once or append-only blob storage)
5. **7+ year retention** for FDA medical device records

**LangSmith does most of the AI-side tracing for free.** Every agent run, every LLM call, every tool input/output captured in a searchable web UI. When the agent does something unexpected, you replay the trace step by step.

Six months later, an auditor pulls approval #5234 and sees: original PO → full conversation → tool calls → AI reasoning → who approved → final D365 sales order. End-to-end traceability.

### The Honest One-Liner

"FastAPI is bare bones compared to Django, so observability is something you add intentionally. For this demo I have basic exception handling and Railway captures container logs. In production at Qosina I'd add Sentry, LangSmith, and Application Insights since you're already on Azure."

---

## 10. Honest Gaps

Tom said: *"We value honest assessment over polished sales pitches."* Here's what's NOT in this demo. Acknowledging this preempts every gotcha question.

- ✗ **No real D365 connection.** All data is seeded SQLite. Tools return OData-shaped JSON so the production swap is a URL + auth change, not a rewrite.
- ✗ **No user accounts.** Everything posts as "Demo User." Production uses Entra ID OAuth with AD groups.
- ✗ **No persisted conversations.** Chat history is in-memory and lost on restart. Production needs persisted SQL + FK to approvals + Blob storage for source docs.
- ✗ **No OCR product.** No Azure Form Recognizer, no Tesseract, no Document Intelligence. Claude Vision reads PDFs and images natively. PyMuPDF just renders PDF pages to PNG before sending.
- ✗ **No specific time-savings claims.** I won't say "10 minutes → 30 seconds" without baselining against Qosina's actual current process. That's a Phase 0 discovery question.
- ✗ **No "FDA traceability built-in" or "healthcare-grade security built-in."** Marketing fluff. These are features you implement, not freebies.
- ✗ **Sample documents are representative, not Qosina's actual format mix.** Phase 0 = audit 50+ real POs to establish format distribution and accuracy baseline.
- ✗ **Constitutional framework rules are representative, not Qosina's actual rules.** The 16 seeded rules are placeholders. Phase 0 = sit with Product Development team to codify their actual conventions.
- ✗ **No D365 F&O write integration.** "Approve" in the demo just changes a status in SQLite. Production write would POST to `/data/SalesOrderHeaders` and `/data/SalesOrderLines` via OData with proper Azure AD auth.

**What I AM saying:** The architecture supports adding all of these. They're integration points, not rewrites. Phase 1 work, on the job.

---

## 11. Phased Rollout Plan

Build in this order. Each phase compounds — Phase 1 builds the foundation that Phase 2 and 3 inherit. Sequence is by complexity (simplest first) and dollar impact (highest-value second).

### Phase 1 — UC1: Sales Order Entry (Foundation Phase)

**Why this first:** One approval type, one team (CX), lowest stakes. Standard product orders only (Tom said this) — skip medical device orders for Phase 1. If something goes wrong, the reviewer rejects the approval and the order gets processed manually like it does today.

**What gets built:**
- The UC1 flow productionized — D365 OData reads + writes, hybrid n8n trigger + Python AI service
- **All foundation pieces every future UC inherits:**
  - Entra ID OAuth + AD groups for authorization
  - Application Insights + structured JSON logging
  - LangSmith for full agent tracing
  - Persisted conversations with FK to approvals (audit trail)
  - Azure Blob Storage for source documents with retention policies
  - Sentry for error tracking, health checks, alerting

**Discovery work (Phase 0 sub-phase):** PO format audit with the CX team. Look at 50+ real POs, establish format distribution, baseline current process time. Map the actual D365 sales order fields they use. Identify top 10 customers and their actual PO formats.

**Success metrics:** 80% of standard POs auto-extracted with high confidence. Approval-to-D365 round trip under 60 seconds. Zero false approvals (reviewer always catches AI errors). Time savings baselined and measured.

---

### Phase 2 — UC2: AP Processing (Highest Dollar Impact)

**Why this second:** Tom's brief literally called this "waste of human effort." It's where Qosina is losing the most money — missed price discrepancies, mystery payments, overdue accounts not being chased optimally. Foundation pieces from Phase 1 are already in place.

**What gets built (sub-phases):**
- **2A: Three-way matching** — most deterministic, easiest to validate. Build first.
- **2B: Cash application** — needs more AI judgment, builds on the 2A approval pattern.
- **2C: Collections prioritization** — pure intelligence layer, lowest write risk.

**Architecture shift:** This is where the recommendation changes. UC1 was Hybrid (n8n + Python). UC2 is **Power Platform + Custom Python**. Power Automate handles the D365 reads/writes via native connectors and the Teams approval routing. The Python service from Phase 1 gets called from Power Automate via HTTP for the AI judgment work — cash app reasoning and collections scoring. *Same Python service, just adding new tools.*

**Discovery work (Phase 0 sub-phase):** Sit with the Finance team. AP has tribal knowledge — which vendors are reliable, which customers short-pay, what tolerance thresholds make sense in practice. Map existing Celigo flows so we don't rebuild them. Get tolerance threshold preferences (the $0.05 number is mine, not theirs). Understand approval authority for what dollar amounts (drives AD group setup).

**Success metrics:** 60-70% of vendor invoices auto-recommend "fast-track approval" (perfect or within tolerance). Cash application coverage rate. Collections priority list adopted by AP team in practice. **DSO improvement** (Days Sales Outstanding) — the executive metric.

---

### Phase 3 — UC3: Product Data Entry (Most Reasoning-Heavy)

**Why this last:** Lowest volume of work (new SKUs added periodically, not hundreds per day). Most reasoning-intensive — you want the foundation rock-solid before building it. Needs the most pre-work because the constitutional framework is currently tribal knowledge.

**What gets built:** The UC3 flow productionized as **Full Custom Python**. Same service from Phases 1 and 2, just adding the UC3 agent and tools. Plus an admin UI for the Product Dev team to edit constitutional rules themselves (rules live in a database table, not code).

**Discovery work (Phase 0 sub-phase, longest):** Sit with Product Development for several weeks. Audit 30-50 existing product entries to extract the implicit naming conventions. Build the constitutional framework as a table the team can edit themselves. Understand the landed cost calculation downstream (Tom mentioned this in the brief). Map technical drawings — do these need vision AI? Vendor-specific?

**Success metrics:** Field-level accuracy per category (start with stopcocks, work outward). Time savings per new SKU. Consistency check pass rate against existing 8K SKUs. Product Dev team self-service rate on new naming rules.

---

### ⚠ Discovery Work Is Non-Negotiable

Every phase starts with a Phase 0 sub-phase: **team interviews, process shadowing, real document audits.** AI tools that ignore the actual workflow get rejected by the team. The Phase 0 work is not optional — it's the most important input.

> "I'd interview each team individually, sit with their process, understand it like the back of my hand, and then design the solution for them — not the other way around."

---

### The Compounding Story

Phase 1 builds the foundation (auth, observability, audit, deployment) with the simplest use case as the vehicle. Phase 2 adds the highest-value AI work to that foundation. Phase 3 adds the most reasoning-heavy work to a now-mature platform. By the end, Qosina has three production AI workflows in active use, one shared platform, and a pattern that can extend to other use cases (warehouse, customer support, QA) without rebuilding.
