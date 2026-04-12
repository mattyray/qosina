# INTERVIEW_REFERENCE.md

Printable backup of the Architecture tab. Same content, same order, same voice. If the demo crashes during the call, open this file and walk Tom and DJ through it.

## TABLE OF CONTENTS

1. [Stack at a Glance](#1-stack-at-a-glance)
2. [Human in the Loop](#2-human-in-the-loop)
3. [The Three Use Cases](#3-the-three-use-cases)
4. [The Tools](#4-the-tools)
5. [Approval Types](#5-approval-types)
6. [AP Processing Primer](#6-ap-processing-primer)
7. [OpenRouter](#7-openrouter)
8. [Production Path](#8-production-path)
9. [Observability & Audit](#9-observability--audit)
10. [Phased Rollout Plan](#10-phased-rollout-plan)
11. [Honest Gaps](#11-honest-gaps)

---

## 1. Stack at a Glance

I created a Python web app that wraps a LangGraph AI agent with a SQLite database mocked to look like D365 Finance & Operations. Here are the key technology choices and why I made them:

**LangGraph ReAct Agents** — The framework that lets Claude reason through a problem with tools. Reason → Act (call a tool) → Observe the result → repeat. Same agent code regardless of which LLM is behind it.

**OpenRouter for LLM Resilience** — Claude Sonnet 4 primary, GPT-4o and Gemini 2.5 Flash as failover. This is the resilience story we talked about in Round 3 — if Anthropic goes down, the agent keeps working with a different model. Same code, no rewrite. Switch live in the header dropdown.

**Claude Vision (No OCR Product)** — Worth flagging because everyone assumes you need an OCR product for document parsing. You don't. PDFs get rendered to PNG with PyMuPDF, then sent directly to Claude Vision. No Form Recognizer, no Tesseract, no Document Intelligence. Claude reads the image natively.

**SQLite with OData-Shaped Responses** — All 17 tables return data formatted to look exactly like D365 F&O OData responses. Same field names, same JSON shape, same `@odata.context` headers. The production swap from SQLite to D365 is a URL + auth change, not a rewrite.

**Application Infrastructure** — FastAPI backend (Python 3.12), vanilla JS frontend with Tailwind CDN, Server-Sent Events for real-time streaming, Docker on Railway with auto-deploy from GitHub. ~7,800 lines of code total, 64 unit tests across 4 test files.

---

## 2. Human in the Loop

We briefly discussed this in Round 3, but in summary:

- The agent has **zero write tools** to your system of record. It can read everything — products, inventory, customers, orders, vendor invoices, payments. It can run matches, score risk, validate pricing. But it cannot post to D365, modify a customer, apply a payment, or create an item master entry.
- The only write tool is `create_approval`, which adds a recommendation to a queue. That's it.
- I made it impossible in code, not policy. Even if someone tried to bypass it later, there's literally no tool for the agent to call.
- Every approval is reviewed in a side-by-side panel that shows the original document, the AI's extracted summary, and editable form fields with confidence colors. The reviewer can change anything before clicking Approve.

As we discussed, the goal isn't to replace anyone — it's to improve their workflow so they have time for higher-value work like growth, analysis, and vendor relationships. The AI handles the repetitive extraction and matching; the team makes the decisions that matter.

---

## 3. The Three Use Cases

For each use case I'd like to go over the business problem, what I built, and which approach I would recommend for production. The recommendation is different for each use case. I would need your guidance on which technologies are the best fit — my recommendations are based on research, but I don't have hands-on experience with Qosina's actual systems. Getting this right would require working closely with you and the teams involved.

### UC1 — Sales Order Entry (CX Department)

**The business problem:** Your CX team gets POs by email in every format imaginable. Clean PDFs from larger customers, scanned documents from smaller ones, the occasional handwritten form, and sometimes just text typed into the email body. Today someone reads each one and manually keys it into D365 as a sales order with the right customer, line items, prices, and ship-to. It's slow, it doesn't scale, and human typing introduces errors that get caught downstream when something ships wrong.

**What I built:**
- Drop a PO in any format — PDF, image, paste text. Claude reads it directly.
- Agent extracts customer, contact, PO number, line items, ship-to, delivery date, payment terms.
- Then it runs through five tools: `match_customer` against the master, `match_products` fuzzy-matched against the catalog, `validate_pricing` against contracted rates, `check_inventory`, then `create_approval`.
- Each field gets a confidence score. The reviewer sees red/yellow/green borders so they know exactly which fields the AI was unsure about and need to be checked.

**My recommendation: Hybrid (n8n + Custom Python)**

| Tool | Role |
|---|---|
| n8n | Trigger side — watch inbox, extract attachments, route to Python webhook. Visual, business analysts can maintain it. |
| Custom Python | AI engine — Claude vision, fuzzy match vs 5K SKUs, confidence scoring, full pytest coverage. *Built in this demo.* |
| Power Platform | AI Builder is for structured forms, can't fuzzy match 5K SKUs, can't use Claude natively. Not the right tool here. |

Why hybrid: n8n is great at the email plumbing — watching an inbox, pulling attachments, routing them to a webhook. That's commodity work and a visual flow is easier for the team to maintain than Python. But the AI extraction and fuzzy matching against 5,000 SKUs needs Claude reasoning, which lives in the custom Python service. Use each tool for what it's best at.

### UC2 — AP Processing (Finance Department)

**The business problem:** This is the one your finance team called "waste of human effort" in the brief. It's actually three sub-jobs glued together: deciding whether to pay vendor invoices (three-way matching), figuring out which open invoices an incoming customer payment covers (cash application), and prioritizing which overdue accounts to chase first (collections). All three are full of edge cases — penny rounding, partial payments, mystery checks with no remittance, discontinued POs, vendor price increases. Today your AP team handles each one manually and the long tail of edge cases eats their time.

**What I built:**
- **Three-way matching:** Drop a vendor invoice PDF or click "Three-Way Match All" — agent calls `three_way_match`, compares the invoice line-by-line against the seeded PO and receipt, and creates an `invoice_match` approval. Tolerance thresholds determine whether it's recommended for fast-track or flagged for investigation.
- **Cash application:** Drop a payment remittance or click "Cash Application" — agent calls `match_payment`, proposes which invoices the payment covers, handles partial pays and deductions, and creates a `payment_application` approval.
- **Collections:** Click "Collections Priority" — agent calls `score_collections`, ranks overdue accounts by amount + age + payment trend + tier, creates a `collection_outreach` approval per customer with reasoning.

**My recommendation: Power Platform + Custom Python**

| Tool | Role |
|---|---|
| n8n | Could work, no advantage. D365 F&O needs HTTP node. No native D365 F&O connector. Not the right call here. |
| Power Platform | Core. Native D365 F&O connectors, built-in Approvals via Teams, audit trail for free, finance team already uses it. *The right call here.* |
| Custom Python | Intelligence. Cash app reasoning, collections risk scoring, Claude judgment calls. Called from Power Automate via HTTP. |

This is the one where I'm explicitly NOT recommending my own stack as the core. Microsoft already built the boring 90% — the D365 F&O connectors, the Teams approval routing, the audit trail. You're already paying for it. Don't rebuild what you own. The custom Python piece is just for the 10% that's actually novel: the AI judgment calls on cash application and collections scoring.

**Why not Copilot Studio?** The brief called out Copilot Studio as the AI piece of Power Platform. Copilot Studio is strong for chatbot-style assistants over indexed knowledge bases — it would be fine for a "check my invoice status" portal. But it's not the right runtime for multi-tool ReAct agent loops (fuzzy matching against 5K SKUs, deterministic tool calls with confidence scoring, vision on handwritten documents). AI Builder has the same gap: designed for templated form extraction, not the variable formats the brief explicitly called out. That's why the intelligence layer stays in custom Python even when the orchestration layer is Power Platform.

### UC3 — Product Data Entry (Product Development)

**The business problem:** When Product Development sources a new SKU, the supplier sends documentation in every format — spec sheets, certificates of analysis, catalog pages, technical drawings. Today someone manually extracts 30+ data fields per SKU and types them into the D365 item master. With 8,000+ existing SKUs and new ones added regularly, this is a significant time investment. The brief specifically called out that AI would need a "constitutional framework" — non-negotiable rules for translating supplier terminology into Qosina's standards. That's the most interesting part of this use case.

**What I built:**
- Drop a supplier spec sheet — Claude reads it directly.
- Agent calls `get_naming_conventions` to load the constitutional rules from a database table.
- Then it normalizes every field according to the rules: "PC plastic" becomes "Polycarbonate (PC)", "M Luer Lock" becomes "Male Luer Lock", inches become millimeters, "valve" with luer connections becomes "Stopcock".
- Calls `find_similar_products` to compare against existing catalog entries for consistency, then `validate_consistency` to check the normalized fields against the rules and the catalog patterns.
- Creates a `product_entry` approval with the structured data grouped by section — Basic Info, Dimensions, Connections, Compliance, Commercial.

**Downstream connection — Landed cost estimation:** The brief mentioned this connects to landed cost calculation. Several fields the agent extracts — country of origin, tariff code, MOQ, supplier unit price, weight — are direct inputs to landed cost formulas (product cost + freight + duties + insurance + handling). Once these fields are normalized and approved into the D365 item master, downstream tools like StockIQ or D365's own costing module can pull them. The agent doesn't calculate landed cost itself — that's a separate engine. But it ensures the inputs are clean and consistent, which is the failure mode landed cost estimation hates most: garbage in, garbage out.

**The constitutional framework is the interesting part:** The naming rules live in a database table, not in code. Adding a new rule is an INSERT, not a deployment. The Product Dev team could maintain their own rules through an admin UI without needing me to push code. The rules are enforced in two places: in the agent's prompt (so Claude follows them during extraction) and in validation code (so we double-check before the approval is created). Belt and suspenders.

**My recommendation: Full Custom Python**

| Tool | Role |
|---|---|
| n8n | AI Agent node available, but constitutional rules need code precision. Hard to test/validate. Not the right call. |
| Power Platform | AI Builder not strong enough. Can't enforce naming rules precisely. Not Claude-native. Not the right call. |
| Custom Python | Full. Constitutional rules in DB + prompt, validation in code (belt + suspenders), consistency check vs catalog, full Claude reasoning. *Built in this demo.* |

This one is full custom Python because the constitutional framework needs precision that low-code tools can't give you. You don't want a no-code workflow subtly mistranslating "PC plastic" as "Polycarbonate (Plastic)" instead of "Polycarbonate (PC)". The rules need to be precisely controlled, testable, and enforceable. It's also lower volume than UC1/UC2 — new product entries, not hundreds of POs per day — so the orchestration tax of a workflow tool isn't worth it.

---

## 4. The Tools

There are four agents total — the original general agent from Round 3 plus one specialized agent per use case. Across all four agents there are 20 read-only tools and exactly 1 write tool.

### General Agent — 6 read-only
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

### UC2 AP Agent — 5 read-only
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
Shared across all four agents. Adds a row to the approval queue with the structured field data, confidence scores, and a reference to the source document. That's the only way data gets written. There's no other path.

A few things worth knowing about how I structured this. Each tool is a pure Python function in `tools.py` with no LangGraph dependency. The `agent.py` file wraps them with `@tool` decorators for the agent. That separation matters because it means the business logic is testable in isolation — 64 unit tests run against the pure functions, no LLM mocking required. If you want to know whether `three_way_match` handles a quantity discrepancy correctly, you write a test against the function directly. You don't need to spin up an agent.

---

## 5. Approval Types

The agent produces six distinct approval types across the three use cases. Each one renders differently in the review panel and would route to a different downstream action in production — writing to D365 F&O for sales orders, vendor payments, and item master entries, creating activities in D365 CE for collections outreach, or linking quality data to existing catalog entries. The specifics of those write-backs would depend on how Qosina's D365 and Celigo are configured.

| Type | Use Case | What it answers |
|---|---|---|
| `sales_order` | UC1 | Should we accept this PO and create a sales order? |
| `invoice_match` | UC2 | Should we pay this vendor invoice? |
| `payment_application` | UC2 | Which invoice does this customer payment pay off? |
| `collection_outreach` | UC2 | Which overdue customer should we chase first? |
| `product_entry` | UC3 | Should we add this supplier product to our catalog? |
| `quality_document` | UC3 | Is this batch of an existing product safe to receive and ship? |

**UC1: 1 type** — One approval per PO, even if it has 50 line items. An order is one business object that gets approved or rejected as a whole.

**UC2: 3 types** — AP is three distinct sub-jobs glued together: pay bills, apply payments, chase overdue. Each one routes differently.

**UC3: 2 types** — Product entry for new catalog items (spec sheets, catalogs). Quality document for lot tracking and test results (CoAs). Different document types, different approval routing.

The system is extensible — new approval types can be added without schema changes since the type field is an open string.

---

## 6. Accounts Payable — The Three Sub-Jobs

Accounts Payable looks like it has the biggest impact — the brief called it "waste of human effort." It's actually three sub-jobs that I'd like to walk through. The AI handles the analysis for each and produces a recommendation; humans always make the final call.

| Direction | Sub-job | The question being answered |
|---|---|---|
| Money OUT | Three-way match | "Should we pay this vendor's bill?" |
| Money IN | Cash application | "Which open invoice does this customer payment pay off?" |
| Money LATE | Collections | "Which overdue customer should we call first?" |

### Three-way matching (money out)

Three documents need to agree before paying a vendor. The PO says "we ordered 500 stopcocks at $3.95." The receipt says "we got 480 stopcocks." The invoice says "pay us $1,975 for 500 stopcocks." If all three agree, the bill gets paid. If they don't agree, somebody investigates before money moves.

Without three-way matching you pay for parts that never arrived, get charged the wrong price, or pay the same invoice twice. It's the number one way money leaks out of a business. My agent calls `three_way_match`, compares line by line, and creates an approval that's either green (perfect match), yellow (penny variance, recommend write-off), or red (real discrepancy, hold and investigate).

### Cash application (money in)

A customer sends Qosina a payment. Finance has to figure out which open invoice it pays off. Sounds simple, but it's actually the hardest of the three. Customers send checks with no remittance advice (the note that tells you which invoices the payment is for). They send one big check that's supposed to cover three invoices. They pay the wrong amount because of damage deductions, freight charges, or early-payment discounts.

Until cash is applied, the customer's account still shows them as overdue even though they paid you. You'll call them asking for money they already sent. AR numbers are wrong. Auditors get angry. My agent calls `match_payment`, proposes how to allocate the money, and creates an approval the reviewer can adjust before applying.

### Collections prioritization (money late)

Some customers don't pay on time. The AP team might have 200 overdue accounts on any given day and they can't call them all. Which to call first? Naive sorting like "biggest amount" or alphabetical is bad. Good prioritization considers amount owed, days overdue, payment history, account size, and last contact date.

This matters at the executive level because **DSO** — Days Sales Outstanding — is one of the top metrics finance teams are measured on. Cutting DSO from 65 days to 50 days is tens of thousands in cash flow improvement. My agent calls `score_collections` and produces a ranked list with reasoning per customer.

---

## 7. OpenRouter

This is the resilience story we talked about last time. The idea is that all LLM calls go through a single gateway that can route to whichever provider is healthy.

- **Claude Sonnet 4 (primary)** — best reasoning for fuzzy matching, the constitutional framework, complex extraction.
- **GPT-4o (failover)** — auto-routes if Anthropic is down or rate-limited. Roughly 25 ms of routing overhead.
- **Gemini 2.5 Flash (failover)** — final fallback. Different provider, different region, completely separate infrastructure.

The reason this matters at Qosina specifically: enterprise systems can't go down because a third-party LLM provider is having a bad day. With this setup you get one API key, one bill, one dashboard, and provider data policies enforced (no training on Qosina data). If Claude breaks, the agent keeps working. If OpenRouter itself breaks, I can flip a feature flag and call Claude or OpenAI directly.

When we get to the live demos and start working with the agents and documents, I'll show you how the OpenRouter model switching works in real time — switching between Claude, GPT-4o, and Gemini mid-demo to demonstrate that the entire system is model-agnostic.

---

## 8. Production Path

The architecture stays identical between this demo and production. Only the integration points change:

| Layer | Demo (today) | Production (Qosina) |
|---|---|---|
| **ERP Data** | SQLite + mock data | **D365 F&O** via OData REST / MCP |
| **CRM Data** | SQLite + mock data | **D365 CE** via Dataverse API |
| **Integration** | None | **Celigo iPaaS** triggers + write-back |
| **Workflow (UC1)** | None | **n8n** email triggers + attachment routing |
| **Auth** | None ("Demo User") | **Entra ID** OAuth + AD groups |
| **File Storage** | Browser memory (data URLs) | **Azure Blob** with retention policies |
| **Conversations** | In-memory (lost on restart) | Persisted SQL with FK to approvals |
| **Logs** | stdout / Docker logs | **Application Insights** + structured JSON |
| **Error Tracking** | Generic catch-all | **Sentry** / App Insights with stack traces |
| **Agent Tracing** | Live activity panel | **LangSmith** full trace replay |
| **Hosting** | Railway (Docker) | **Azure Container Apps** same tenant as D365 |

**D365 ERP MCP Server (GA February 2026):** Microsoft recently released a Model Context Protocol server for D365 Finance & Operations. This could simplify the production integration significantly — instead of hand-writing OData calls per entity, the agent connects through MCP with built-in governance, auth, and business logic execution. This is something I'd evaluate in Phase 0 discovery.

### What each use case connects to in production

- **UC1:** n8n triggers (inbox, attachments) → reads F&O (customers, products, pricing, inventory) + reads CE (customer context) → writes F&O (sales orders)
- **UC2:** Reads F&O (POs, receipts, invoices, payments) + reads CE (customer history, last contact) → writes F&O (payment journals) + writes CE (collection activities)
- **UC3:** Reads F&O (existing products for consistency) → writes F&O (item master) → syncs to CE (product catalog) via Dual Write / Celigo
- **Celigo:** Trigger layer (inbox watching, document routing) + write-back layer (D365 field mappings, retries) + F&O ↔ CE sync

---

## 9. Observability & Audit

Three things matter here for medical device compliance. I want to be clear about all of them because for a regulated industry this isn't optional.

### User accounts in production

I wouldn't roll my own user system. Qosina is on Azure, every employee already has an account in Entra ID (the new name for Azure AD). I'd integrate with that via OAuth. The user logs in through Microsoft, comes back with a JWT, FastAPI middleware validates it and attaches the user to each request. Authorization comes from **AD groups** — like "AP_Approver", "CX_Manager", "Product_Dev_Lead". Your IT team already manages who's in what group. I'm just consuming that. Don't rebuild what you own.

### Troubleshooting FastAPI in production

FastAPI is bare-bones compared to Django, so observability is something you add on purpose. For this demo I have basic exception handling and Railway captures the container logs. In production at Qosina I'd add:

- **Structured JSON logging** flowing into Azure Log Analytics
- **Sentry** or **Application Insights** for error tracking with full stack traces and request context
- **Health endpoint** at `/health` for liveness probes
- **Application Insights APM** for latency, error rates, dependency tracing (you're already on Azure, may as well use it)
- **LangSmith** for AI traces — this is the most important one, see below

### Auditing the AI agent — the FDA story

For a regulated industry every conversation needs to be replayable. Six months later, an auditor pulls approval #5234 and needs to see the original PO, the full conversation, every tool call, the AI's reasoning, who approved it, and the final D365 sales order. End to end traceability. Here's how I'd build that:

1. Persist every conversation to a `conversations` + `conversation_messages` table
2. Foreign key approvals back to the conversation that produced them
3. Store source documents in Azure Blob Storage with retention policies (7+ years for FDA medical device records)
4. Append-only or write-once storage for the audit log (tamper-evident)
5. LangSmith captures the agent side automatically — every LLM call, every tool input/output, searchable web UI, replay step by step

The honest framing: most of this is integration work, not algorithm work. The architecture supports adding it. It's Phase 1 alongside building UC1.

---

## 10. Phased Rollout Plan

Build in this order. Each phase compounds — Phase 1 builds the foundation that Phase 2 and 3 inherit. The sequence is by complexity (simplest first) and dollar impact (highest-value second).

### Phase 1 — UC1: Sales Order Entry (Foundation Phase)

**Why this first:** One approval type, one team (CX), lowest stakes. Standard product orders only — skip medical device orders for Phase 1 like Tom suggested. If something goes wrong, the reviewer rejects the approval and the order gets processed manually like it does today.

**What gets built:** The UC1 flow productionized — D365 OData reads and writes, hybrid n8n trigger plus the Python AI service. Plus all the foundation pieces every future use case will inherit: Entra ID OAuth, AD groups for authorization, Application Insights logging, LangSmith agent tracing, persisted conversations with audit FK, Azure Blob Storage for source documents, Sentry, health checks, alerting.

**Discovery work first:** Spend a couple weeks doing a PO format audit with the CX team. Look at 50+ real POs, establish format distribution, baseline current process time. Map the actual D365 sales order fields they use in production. Identify the top 10 customers and what their POs actually look like.

### Phase 2 — UC2: AP Processing (Highest Dollar Impact)

**Why this second:** The brief literally called this "waste of human effort". This is where Qosina is losing the most money — missed price discrepancies, mystery payments, overdue accounts not being chased optimally. By the time we get here all the foundation pieces from Phase 1 are already in place.

**Sub-phased delivery:** Three-way matching first because it's the most deterministic and easiest to validate. Cash application second, builds on the same approval pattern. Collections prioritization third, lowest write risk because it just produces a ranked list.

**Architecture shift:** This is the use case where I switch the recommendation. UC1 was hybrid n8n + Python. UC2 is Power Platform plus custom Python. Power Automate handles the D365 reads and writes via native connectors and the Teams approval routing. The same Python service from Phase 1 gets called from Power Automate via HTTP for the AI judgment work. New tools, same service.

**Discovery work first:** Sit with the Finance team for a couple weeks. AP has tribal knowledge — which vendors are reliable, which customers are notorious for short-pays, what tolerance thresholds make sense in practice. Map existing Celigo flows so we don't rebuild what's already working. Get the team's actual tolerance threshold preferences. Understand who has approval authority for what dollar amounts so we set up AD groups correctly.

### Phase 3 — UC3: Product Data Entry (Most Reasoning-Heavy)

**Why this last:** Lowest volume of work (new SKUs added periodically, not hundreds per day). Most reasoning-intensive — you want the foundation rock-solid before building it. And it needs the most pre-work because the constitutional framework is currently tribal knowledge that nobody has codified.

**What gets built:** The UC3 flow productionized as full custom Python. Same service from Phases 1 and 2, just adding the UC3 agent and tools. Plus an admin UI for the Product Dev team to edit the constitutional rules themselves — rules live in a database table, not code, so no developer needed for new rules.

**Discovery work first (longest of the three):** Sit with Product Development for several weeks. Audit 30-50 existing product entries to extract the implicit naming conventions. Build the constitutional framework as a database table they can edit themselves. Understand the landed cost calculation downstream — the brief mentioned this connects to it. Map technical drawings — do those need vision AI? Are they vendor-specific?

**Every phase starts with discovery.** Team interviews, process shadowing, real document audits. Each workflow needs to be fully understood before anything gets built. The discovery work is the most important input.

**The compounding story:** Phase 1 builds the foundation (auth, observability, audit, deployment) with the simplest use case. Phase 2 adds the highest-value AI work to that foundation. Phase 3 adds the most reasoning-heavy work to a mature platform. By the end: three production workflows, one shared platform, and a pattern that extends to future use cases without rebuilding.

---

## 11. Honest Gaps

Tom said in the brief: "we value honest assessment over polished sales pitches." So here's what's NOT in this demo, explicitly. I'd rather acknowledge these upfront than have them caught in a gotcha question.

- ✗ **No real D365 connection.** All data is seeded SQLite. The tools return OData-shaped JSON so the production swap is a URL + auth change, not a rewrite, but the actual D365 integration is Phase 1 work.
- ✗ **No user accounts.** Everything posts as "Demo User". Production uses Entra ID OAuth with AD groups for authorization. Phase 1 integration.
- ✗ **No persisted conversations.** Chat history is in-memory and lost on restart. Production needs persisted SQL with FK to approvals and Azure Blob Storage for source documents. The audit trail story is the architecture, not what's actually wired up today.
- ✗ **No specific time-savings claims.** I'm not going to say "this saves your team 10 hours a week" without baselining against your actual current process. That's a Phase 0 discovery question for each team.
- ✗ **No "FDA traceability built-in" or "healthcare-grade security built-in".** Marketing fluff. These are features you implement, not free architectural defaults. The HITL pattern and the audit trail story are how I'd build toward FDA compliance, but neither is "free."
- ✗ **Sample documents are representative, not Qosina's actual format mix.** I generated the PDFs and the handwritten image to cover a range of scenarios. The real format distribution is something you only learn from auditing 50+ actual POs in Phase 0.
- ✗ **Constitutional framework rules are representative, not Qosina's actual rules.** The 16 seeded rules are placeholders. The real ones are tribal knowledge in your Product Development team and codifying them is Phase 0 work for UC3.
- ✗ **No D365 F&O write integration.** "Approve" in this demo just changes a status in SQLite. A production write would POST to `/data/SalesOrderHeaders` and `/data/SalesOrderLines` via OData with proper Azure AD auth.
- ✗ **I need to understand Qosina's actual system landscape.** D365 F&O, D365 CE, Celigo iPaaS, StockIQ, the Shopify migration — every technology choice I've proposed needs to be validated against how these systems are actually configured and connected at Qosina. I don't know which Celigo flows exist today, how D365 F&O entities are customized, what the approval authority structure looks like, or how CE is being used for customer management. This is Phase 0 work that requires Tom's and the team's expertise. The architecture is designed to plug into these systems, but the specific wiring is a conversation, not a guess.

**What I AM saying:** The architecture supports adding all of these. They're integration points, not rewrites. Phase 1 work, on the job. The reason I built it this way is that I wanted the demo to land the hardest part — the AI reasoning, the tool architecture, the HITL pattern, the OData mock layer — and let the boring integration work be exactly what it is: boring integration work that takes two weeks per piece, not architectural risk.
