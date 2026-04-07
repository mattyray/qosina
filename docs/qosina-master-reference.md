# Qosina Round 4 — Complete Reference

Everything discussed, one place. Use this as your reference while building and prepping.

---

## THE SITUATION

Round 4 interview at Qosina. 90-minute Teams call. Tom Livingston (Director of Enterprise Applications, your future boss) sent a project brief with three real automation use cases from AI workshops with department heads. He said "you do not need to build anything." You're building working demos anyway — same play that won Round 3.

**Tom Livingston** — execution-focused, wrote the brief, lives with these pain points daily. Previously worked with DJ at D'Addario and Perfumania. Said he hadn't seen that level of effort in a long time after your Round 3 demo.

**DJ Rettman** — EVP/CIO/CTO, PhD, enterprise transformation veteran. Governance and security-focused. Loved that your Round 3 agent couldn't write to the system of record. Cares about "why" behind architectural decisions.

**Deadline:** ~April 11, 2026

---

## QOSINA — THE COMPANY

Medical device component distributor (not manufacturer). Founded 1980, Ronkonkoma, Long Island, NY. ~120 employees, ~$38M revenue. Privately held (Herskovitz family — Scott is President/Chairman, Lee Pochter is CEO). Stocks 5,000+ OEM single-use components (stopcocks, luer connectors, check valves, tubing, clamps, syringes, filters). Sells to medical device OEMs globally. Think McMaster-Carr of medical device parts.

**Regulation:** Parts end up in medical devices inside human bodies. Every lot requires tracking numbers, expiration dates, certificates of compliance. FDA notification required for part changes. ISO 13485, 9001, 22301, 14001, 45001. 95,000 sq-ft facility with ISO Class 8 Clean Room. ISO 80369-7 connector standard for luer connectors.

### Complete Tech Stack

| System | Platform | What It Does |
|--------|----------|-------------|
| ERP | D365 Finance & Operations (F&O) | System of record — products, inventory, orders, purchasing, financials |
| CRM | D365 Customer Engagement (CE) | Sales pipeline, customer relationships |
| Integration | Celigo iPaaS | Connects ERP, CRM, ecommerce. Handles EDI, order sync, invoice automation |
| Data | Azure Synapse + Data Lake + SQL Server + Power BI | Reporting and analytics |
| Warehouse | PowerHouse WMS | Pick/pack/ship |
| Ecommerce | DynamicWeb (migrating to Shopify) | Online catalog at qosina.com |
| Inventory Planning | StockIQ | Demand forecasting |
| AI | Anthropic Claude (dev/automation) + Microsoft Copilot (M365 productivity) | Multi-model approach |
| Cloud | Microsoft Azure | Infrastructure, identity (Azure AD) |

---

## THE THREE USE CASES — EXPLAINED SIMPLY

### Use Case 1: Sales Order Entry from Emails & Documents

**The pain:** CX team gets purchase orders via email. PDFs, typed emails, scans, handwritten. Someone reads each one and manually types it into D365 as a sales order. Slow, error-prone, doesn't scale.

**What a PO contains:** Customer name/account, part numbers, quantities, unit prices, ship-to address, delivery date, their PO reference number, payment terms.

**What goes into a D365 sales order:** Customer account (Qosina's ID for them), line items (part number + quantity + price per line), PO reference, delivery date, ship-to address, payment terms, warehouse/site, shipping method.

**What the demo does:** Paste/upload PO → Claude extracts all fields → fuzzy matches customer against customer master and parts against 5,000+ SKU catalog → confidence scores each field → routes to approval queue → human reviews → approve creates the order.

**What makes it hard:** Document format diversity (clean PDF vs photo of handwritten form), fuzzy matching (customer writes "3 way stopcock luer" and you need to find Part #11195), pricing validation against contracted rates, edge cases (new customers, partial orders, ambiguous items).

**Tom's note:** Medical device orders have extra compliance requirements. Standard product orders = Phase 1.

**Our tool recommendation:** Hybrid — n8n for email trigger/routing + Custom Python (Claude) for document parsing and fuzzy matching.

### Use Case 2: Accounts Payable Processing

**The pain:** Finance team processes hundreds of vendor invoices monthly. Three sub-problems they called "waste of human effort."

**Sub-problem A — Three-Way Matching:**
- **Purchase Order (PO):** What Qosina ordered from a vendor ("500 units of Part X at $2.00")
- **Receipt / Goods Receipt:** What the warehouse logged when shipment arrived ("Got 480 units of Part X")
- **Vendor Invoice:** The bill from the vendor ("Pay us $1,000 for 500 units")
- **The match:** Compare all three. PO says 500, receipt says 480, invoice says 500 — mismatch. Someone investigates. Do this hundreds of times per month.
- **Line-item level:** Compare each product line individually
- **Header level:** Compare totals
- Usually need both

**Sub-problem B — Cash Application:**
- Customer XYZ owes Qosina on 3 invoices: $5,000 + $3,200 + $1,800
- A payment for $8,200 hits the bank. Which invoices does it cover?
- Simple case: $8,200 = $5,000 + $3,200. Done.
- Hard case: Payment is $7,995. Is that a rounding difference? Discount? Short-pay? Someone investigates.
- **Remittance advice:** Some customers send a note saying "this covers Invoice #1001 and #1002." Many don't. Then you're guessing.

**Sub-problem C — Collections Prioritization:**
- Which overdue customers to chase first?
- AI analyzes payment patterns: "Customer DEF went from 5 days late → 30 days → 60 days. Trending toward non-payment. Customer GHI owes $50K and is 45 days late — prioritize."

**Key concepts:**
- **Penny discrepancy:** Invoice says $10,472.37, payment is $10,472.38. One cent off from rounding. Nobody cares but the system shows it as "not fully paid." Automation auto-writes off under threshold.
- **Tolerance threshold:** "Under $0.05 variance → auto-approve. $0.05-$50 → quick review. Over $50 → full investigation."
- **Partial payment:** Customer pays $3,000 on a $5,000 invoice. System records $3,000 applied, $2,000 still outstanding.
- **Credit memo:** "We overcharged you $200. Here's a credit." Complicates cash application.

**Our tool recommendation:** Power Platform for core matching (deterministic logic, native D365 connectors, finance team lives in Microsoft) + Custom Python for collections intelligence scoring.

### Use Case 3: New Product Data Entry from Supplier Documents

**The pain:** Suppliers send spec sheets, certificates of analysis, catalogs, technical drawings. Product Development manually extracts 30+ fields per SKU and types them into D365 item master. 8,000+ SKUs and constantly adding new ones.

**The 30+ fields (our best guess):** Item ID, product name, short/long description, category, sub-category, status, material, color, inner diameter (mm), outer diameter (mm), length (mm), weight (g), tolerances, connection type 1/2/3, ISO 80369-7 compliance, compatible parts, ISO certifications, manufacturing environment, sterilization compatibility, shelf life, shelf life post-irradiation, biocompatibility certs, country of origin, unit price, minimum order qty, units per case, lead time, supplier/vendor, tariff code, lot tracking enabled, serial tracking enabled.

**The constitutional framework:** Non-negotiable rules for how AI translates supplier terminology into Qosina's standard vocabulary. Examples:
- "valve" → "Stopcock" (when it has luer connections)
- Material: always "Polycarbonate (PC)" never just "PC" or "polycarbonate plastic"
- Connections: "Male Luer Lock" never "M Luer" or "male luer lock"
- Dimensions: always millimeters, format "X.Xmm"
- Product names: "[Material] [Type], [Connection 1] x [Connection 2] x [Connection 3]"

**Item master:** The central product database in D365. Every SKU has a record with all its attributes. "Enter into the item master" = create a new product record.

**What makes it hard:** Document diversity (spec sheets vs certs vs drawings), 30+ fields to extract per product, constitutional rules may only exist in people's heads, consistency with 8,000 existing SKUs (the 48th PC stopcock must be named like the first 47), landed cost estimation downstream.

**Our tool recommendation:** Full Custom Python (Claude). The constitutional framework is a prompt engineering and AI reasoning problem. No low-code shortcut.

---

## THE THREE IMPLEMENTATION APPROACHES

Tom wants you to evaluate each for every use case.

### n8n — Visual Workflow Automation
- Open source, self-hostable on Docker/Azure
- Visual canvas — drag nodes, connect with lines. Whole workflow visible at once.
- 400+ integrations, native AI nodes (Claude, GPT, Gemini, local models via Ollama)
- AI Agent node supports ReAct-style reasoning with tool calling
- D365 F&O: HTTP Request node with OAuth (no native F&O node). D365 CE: native node.
- Workflows export as JSON → Git version control
- $180M raised at $2.5B valuation, 45K+ GitHub stars
- **Good for:** Clear trigger → process → action workflows, visual maintainability, fast prototyping
- **Not great for:** Deeply custom AI logic, complex multi-step reasoning where tools.py + tests matter

### Power Platform — Microsoft Ecosystem
- Power Automate: visual flow builder, native D365 F&O and CE connectors (zero config)
- AI Builder: document processing for invoices, receipts, forms. OCR. Custom model training.
- Copilot Studio: conversational AI agents with knowledge sources
- Native D365 triggers, Dataverse integration, Teams approval cards
- **Killer advantage:** native D365 integration, same Azure tenant, finance team already uses it
- **Gotcha:** AI model flexibility limited (Microsoft models, not Claude). Copilot Credits licensing can get expensive at scale. Calling Claude requires HTTP connector workaround.
- **Good for:** D365 data routing, approval chains, structured document processing, Teams-integrated workflows
- **Not great for:** Complex AI reasoning, constitutional frameworks, when you need Claude specifically

### Custom Python — Maximum Flexibility
- FastAPI + LangGraph + Claude (via OpenRouter)
- Full control over agent architecture, prompting, tool design
- OpenRouter for LLM failover (Claude → GPT-4o → Gemini)
- Unit testable pure function tools, LangSmith observability
- **Good for:** Complex AI reasoning, document parsing, fuzzy matching, constitutional frameworks
- **Not great for:** Simple routing/approval workflows that don't need AI reasoning

### The Smart Play in the Interview
Don't recommend your stack for everything.
- **UC1:** Hybrid — n8n for email trigger + custom Python for AI extraction/matching
- **UC2:** Power Platform for core matching + custom Python for collections scoring
- **UC3:** Full custom Python — constitutional framework is an AI reasoning problem

"I'd actually recommend Power Platform for Use Case 2" shows more enterprise maturity than pushing custom Python for everything.

---

## OPENROUTER — LLM FAILOVER

Discussed with Tom in Round 3 interview. You referenced it in your thank-you email. Now the demos implement it.

**What it is:** Unified API gateway that routes LLM calls. Claude primary → GPT-4o fallback → Gemini fallback. If Claude's API goes down, requests auto-route to backup. ~25ms overhead.

**How it works:** OpenAI-compatible API. Swap `ChatAnthropic` for `ChatOpenAI` with OpenRouter's base URL. Tool calling, streaming, everything works. Your LangGraph agent doesn't know the difference.

```python
# Production (OpenRouter)
model = ChatOpenAI(
    model="anthropic/claude-sonnet-4-20250514",
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY"),
)

# Development (direct Claude, faster iteration)
model = ChatAnthropic(model="claude-sonnet-4-20250514")
```

**What to say:** "Remember our conversation about LLM routing for API failover? I built it. All three demos route through OpenRouter. Claude is primary, but if Anthropic's API goes down, the system automatically fails over to GPT-4o. Zero downtime. The agent, tools, and approval queue don't know or care which model is answering."

---

## THE EXISTING ROUND 3 DEMO

**Live:** https://qosina-demo-production.up.railway.app
**Repo:** https://github.com/mattyray/qosina

### What exists and is reusable:
- FastAPI with SSE streaming (the hard part — already working)
- LangGraph ReAct agent with 7 tools
- SQLite with OData-formatted JSON responses
- Approval queue: create, approve, reject, filter by type, clear resolved
- 29 real Qosina products seeded with real part numbers and specs
- 6 customers with order history
- Product compatibility relationships
- Inventory with lot numbers and expiration dates
- Tool activity panel (shows which tools agent calls in real time)
- Dashboard with alert cards and quick actions
- Data explorer (browse products, inventory, customers, compatibility)
- Docker + Railway deployment
- Unit tests for all 7 tools

### What we're adding on top:
- OpenRouter LLM provider layer
- Tab navigation (5 tabs: Dashboard, UC1, UC2, UC3, Architecture)
- 3 new agents with specialized tools and system prompts
- New database tables (vendors, POs, receipts, invoices, payments, extended product fields, naming conventions)
- New seed data with intentional edge cases
- Per-use-case UI panels
- Architecture diagrams for n8n and Power Platform versions
- Sample documents (fake POs, invoices, spec sheets)

---

## DEMO STRATEGY

**BUILD** three demos in custom Python. All FastAPI + LangGraph + OpenRouter.
**SHOW** architecture diagrams for n8n and Power Platform versions.
**TALK** through trade-offs and make a recommendation per use case.

### What each demo's UI looks like:

**UC1 Tab — Sales Order Entry:**
- Document paste/upload area (paste PO text or pick from sample POs)
- AI chat showing extraction and matching reasoning
- Structured extraction preview: customer, line items, prices — each field with green/yellow/red confidence
- Approval card: "Create Sales Order SO-001234 for ACME Medical, 3 line items, $4,500"

**UC2 Tab — AP Processing:**
- Invoice list (seeded with samples — some match perfectly, some have discrepancies)
- Three-way match view: PO vs Receipt vs Invoice side-by-side, discrepancies in red
- Tolerance indicator: "Variance $0.03 — within $0.05 threshold → Auto-approved"
- Collections tab: customers ranked by AI risk score with reasoning
- Approvals: payment applications, invoice approvals, outreach recommendations

**UC3 Tab — Product Data Entry:**
- Spec sheet paste/upload area + sample spec sheets
- Side-by-side: original doc | extracted + normalized fields
- Each field shows: raw supplier value → Qosina convention (with rule applied)
- Confidence per field, flagged uncertain ones
- "Similar Products" panel showing existing SKUs for consistency check
- Approval: "Create Item Master — 34 fields, 31 high confidence, 3 flagged"

**Architecture Tab:**
- For each use case: diagram of custom Python version (what you built), n8n version, Power Platform version
- Boxes and arrows, not running code

**All tabs share:** Approval queue sidebar (right), OpenRouter status indicator in header

---

## PRESENTATION FLOW (per use case, ~25-30 min)

1. Explain the business problem (30 sec)
2. Show architecture diagram (1 min)
3. Run the live demo (5-7 min)
4. Evaluate all three approaches with diagrams (3-5 min)
5. Give your recommendation and why (1-2 min)
6. Walk through phased rollout (2-3 min)
7. Acknowledge risks and unknowns (1-2 min)
8. Connect to other use cases — shared patterns (1 min)

---

## PHASED ROLLOUTS

### UC1 Phases:
- **Phase 0:** Analyze real PO samples. Identify top 3-5 formats. Establish accuracy baseline.
- **Phase 1:** Structured PDFs from top 10 known customers. Human reviews 100%, AI pre-fills. Measure time savings.
- **Phase 2:** Expand to all standard product customers. Confidence-based auto-routing.
- **Phase 3:** Medical device orders, handwritten forms, expanded auto-approval.

### UC2 Phases:
- **Phase 0:** Analyze one month of cash application data. What % are exact matches?
- **Phase 1:** Cash application — exact match auto-apply (~60-70% of payments). Everything else to human with AI suggestions.
- **Phase 2:** Three-way matching with tolerance rules. Start tight, widen as accuracy proves out.
- **Phase 3:** Collections prioritization. Fuzzy matching for partial payments. Expand auto-approval thresholds.

### UC3 Phases:
- **Phase 0:** Audit 20-30 existing products to codify naming conventions. Build the constitutional framework.
- **Phase 1:** Spec sheets only, top 3 categories. Human reviews 100%, AI pre-fills. Measure field accuracy.
- **Phase 2:** Certificates of analysis. All categories. Confidence-based auto-fill for high-confidence fields.
- **Phase 3:** Technical drawings, catalog pages. Landed cost integration. Feedback loop where corrections improve the framework.

---

## BUILD SCHEDULE

**Day 1 (today):** Research, plan, study guide, CLAUDE.md, questions to Tom, sign up for OpenRouter ✅

**Day 2:** Fork repo, add OpenRouter provider, verify tool calling + SSE still work, add tab navigation shell, expand DB schema, deploy skeleton to Railway

**Day 3:** UC1 — seed data, sample POs, tools (match_customer, match_products, validate_pricing), agent, UI panel, tests

**Day 4:** UC1 polish + UC2 start — seed vendors/POs/receipts/invoices/payments with edge cases, start tools

**Day 5:** UC2 — matching dashboard UI, cash application tool, collections scoring, agent, tests

**Day 6:** UC3 start — constitutional framework, expanded product fields, sample spec sheets, extraction tools

**Day 7:** UC3 finish — consistency validation, side-by-side UI, agent, tests

**Day 8:** Integration & deploy — all tabs working, Railway deployment, end-to-end testing

**Day 9:** Architecture diagrams, n8n/Power Platform comparison visuals, presentation materials, talking points

**Day 10:** Full 90-minute rehearsal with timer

**Day 11:** Buffer, final deploy, rest

---

## TERMS TO MEMORIZE

**AP** = Accounts Payable = money you OWE (paying vendors)
**AR** = Accounts Receivable = money OWED TO YOU (collecting from customers)
**PO** = Purchase Order = "I want to buy these things"
**Sales Order** = Qosina's internal record of a customer's order in D365
**Invoice** = a bill saying "pay me this amount"
**Receipt / Goods Receipt** = warehouse record of what physically showed up
**Three-Way Match** = comparing PO vs Receipt vs Invoice
**Cash Application** = matching incoming payments to open invoices
**Penny Discrepancy** = tiny rounding differences between expected and actual amounts
**Partial Payment** = customer pays less than full invoice
**Tolerance Threshold** = auto-approve if discrepancy under $X
**Write-Off** = recording a small loss to close a discrepancy
**Credit Memo** = document reducing what a customer owes
**Net 30/60** = payment terms — days until payment due
**Item Master** = central product database in D365
**SKU** = one unique product
**Spec Sheet** = supplier document describing product specifications
**CoA** = Certificate of Analysis = document certifying product quality
**Constitutional Framework** = non-negotiable rules for AI data normalization
**Fuzzy Matching** = finding best match when text doesn't exactly match
**Confidence Score** = how sure the AI is (0-100%)
**OData** = D365's API format (REST + JSON)
**ERP** = Enterprise Resource Planning = the one system running the whole business
**CRM** = Customer Relationship Management = sales pipeline
**iPaaS** = Integration Platform as a Service = middleware connecting systems (Celigo)
**HITL** = Human-in-the-Loop = human reviews AI output before it becomes real
**System of Record** = authoritative source of truth (D365)
**MVP** = smallest useful version you build first
**OCR** = Optical Character Recognition = images of text → actual text
**SSE** = Server-Sent Events = streaming data server → browser
**n8n** = open-source visual workflow automation (self-hostable, AI agent nodes, 400+ integrations)
**Power Platform** = Microsoft's low-code platform (Power Automate + AI Builder + Copilot Studio + Power Apps)
**OpenRouter** = LLM API gateway with automatic failover across providers
**LangGraph** = LangChain library for building stateful AI agents with tool calling
**ReAct** = Reason + Act pattern — agent thinks, picks a tool, observes result, repeats

---

## QUESTIONS SENT TO TOM

1. What file types do scanned/handwritten POs arrive as?
2. Besides customer, part numbers, quantities, pricing — other fields in the sales order?
3. Three-way match — line-item level, header level, or both?
4. Standard format for vendor invoices or do they vary?
5. The 30+ fields per SKU for the item master — field list or screenshot?
6. Written version of naming conventions?
7. Sample PO and sample supplier spec sheet?

---

## ANTICIPATED QUESTIONS FROM TOM/DJ

**"How does this connect to D365?"**
"Each tool queries SQLite. In production, replace the SQL query with an HTTP request to D365's OData endpoint. The tool signature stays identical. Add Azure AD OAuth for authentication and Redis caching for stable data like the product catalog."

**"How would you handle D365 authentication?"**
"Azure AD OAuth2 with client credentials flow. Register an app in Azure AD, get client ID and secret, request a token, pass as Bearer token. Standard pattern."

**"What about performance?"**
"Cache stable data (product catalog) in Redis with 15-minute TTL. SSE streaming means users see the agent thinking in real time instead of staring at a blank screen. Tool activity feed shows which data source is being queried."

**"Could this work with Power Platform instead?"**
"For simpler workflows, absolutely. Power Automate for deterministic triggers and routing, Claude for intelligent analysis. They complement each other. I'd actually recommend Power Platform for Use Case 2's core matching."

**"What if Claude's API goes down?"**
"OpenRouter handles that. Claude is primary, GPT-4o is secondary, Gemini is tertiary. Automatic failover, ~25ms overhead. The agent doesn't know or care which model is answering."

**"How do you handle edge cases?"**
"Confidence scoring. High confidence → auto-route to quick approval. Low confidence → flag specific fields for human review. Never auto-create an order or item master record with low-confidence fields. Log everything for continuous improvement."

**"What would you need to learn?"**
Be honest. "I'd need to get hands-on with D365's OData endpoints and authentication. I'd need to understand the specific fields and business rules your teams use today. I'd want to sit with each department to map their actual workflows. The AI architecture I know cold — the domain-specific D365 configuration is where I'd ramp up."
