# Qosina Round 4: Complete Deep Dive & Build Plan

**Candidate:** Matt Raynor
**Interview Format:** 90-minute Microsoft Teams call with Tom Livingston (Director, Enterprise Applications) and likely DJ Rettman (EVP/CIO/CTO)
**Deadline:** ~April 11, 2026 (next Friday)
**What they asked for:** Architectural thinking, tool evaluation, and implementation plans for 3 use cases
**What we're delivering:** All of that PLUS live working demos for each use case

---

## PART 1: QOSINA — EVERYTHING WE KNOW

### The Business
Qosina is a medical device component distributor (not manufacturer) founded in 1980, headquartered in Ronkonkoma, Long Island, NY. ~120 employees, ~$38M revenue, privately held (Herskovitz family — Stuart founded it, Scott is now President/Chairman, Lee Pochter is CEO). They stock 5,000+ OEM single-use components (stopcocks, luer connectors, check valves, tubing, clamps, syringes, filters, bioprocessing components) and sell to medical device OEMs globally. Think of them as the McMaster-Carr of medical device parts.

### Why Regulation Matters
These parts end up inside medical devices in human bodies. Every lot requires tracking numbers, expiration dates, and certificates of compliance. Part changes require customer notification per FDA regulations. Data accuracy and traceability aren't nice-to-haves — they're regulatory requirements. ISO certifications: 13485 (medical device QMS), 9001 (quality), 22301 (business continuity), 14001 (environmental), 45001 (safety). 95,000 sq-ft facility with ISO Class 8 Clean Room. ISO 80369-7 connector standard compliance for intravascular/hypodermic applications.

### Their Complete Technology Stack

| System | Platform | Role |
|--------|----------|------|
| ERP | Microsoft Dynamics 365 Finance & Operations (F&O) | System of record — products, inventory, orders, purchasing, warehouse, supply chain, financials |
| CRM | Dynamics 365 Customer Engagement (CE) | Sales pipeline, customer service, Power Platform access |
| Integration | Celigo iPaaS | Connects ERP, CRM, ecommerce, and third-party systems. Handles EDI, order sync, invoice automation |
| Data/Analytics | Azure Synapse Analytics + Azure Data Lake + SQL Server + Power BI | Reporting, analytics, data warehousing |
| Warehouse | PowerHouse WMS | Warehouse management, pick/pack/ship |
| Ecommerce | DynamicWeb (being migrated to Shopify) | Online product catalog and ordering at qosina.com |
| Inventory Planning | StockIQ | Demand forecasting and inventory optimization |
| AI | Anthropic Claude (development/automation) + Microsoft Copilot (M365 productivity) | Multi-model approach — Claude for custom automation, Copilot for daily productivity |
| LLM Routing | OpenRouter (recommended addition) | Unified API gateway for multi-model failover — Claude primary, GPT-4o/Gemini fallback. ~25ms overhead. Discussed with Tom in Round 3 interview |
| Cloud | Microsoft Azure | Infrastructure, identity (Azure AD), Synapse, Data Lake |

### Key People in This Interview

**Tom Livingston — Director of Enterprise Applications (your future boss)**
Tom is the person who wrote this brief. He's the one living with these pain points daily. He and DJ previously worked together at D'Addario (guitar strings) and Perfumania before joining Qosina. Tom is execution-focused — he wants to know HOW you'd build it, what the real blockers are, and whether you can actually deliver. He's the one who said he hadn't seen that level of effort in a long time after your first demo.

**DJ Rettman — EVP/CIO/CTO (PhD, enterprise transformation veteran)**
DJ came from Fortune 500 consulting and enterprise IT. He joined a 120-person company because he saw an opportunity to build modern infrastructure from scratch. He's governance and security-focused — he cares about human-in-the-loop, audit trails, data integrity, and the "why" behind architectural decisions. The fact that your first demo's agent couldn't write to the system of record was exactly what he wanted to hear.

### What They're Really Testing
This brief isn't a coding test. It's a "can this person think like an enterprise architect" test. They want to see:

1. **Can you decompose a business problem before jumping to code?** (Start with the business pain, not the tech)
2. **Do you understand trade-offs?** (Not everything needs custom Python)
3. **Can you be honest about complexity?** (Say "this is harder than it looks" when it is)
4. **Do you understand enterprise governance?** (HITL, audit trails, data integrity)
5. **Can you phase a rollout?** (MVP first, not boil the ocean)
6. **Can you connect patterns across use cases?** (Shared architecture, reusable components)

---

## PART 2: THE THREE IMPLEMENTATION APPROACHES

### Option A: n8n (Workflow Automation Platform)

**What it is:** Open-source, self-hostable workflow automation platform with 400+ pre-built integrations and native AI/LLM capabilities. Visual node-based builder where you connect triggers → processing → actions. Can be self-hosted on Docker for full data control or used as cloud SaaS. SOC 2 Type II compliant. Recently raised $180M at $2.5B valuation, 45,000+ GitHub stars.

**AI Capabilities (strong in 2026):**
- Native AI Agent node — supports ReAct-style reasoning with tool calling loops
- Built-in nodes for all major LLM providers (OpenAI, Anthropic Claude, Google Gemini, local models via Ollama)
- RAG pipeline support with document loaders, text splitters, and vector store integrations (Pinecone, Qdrant, Supabase)
- Memory nodes for multi-turn conversation context
- Full parameter control on LLM calls
- Native LangChain integration
- MCP server support — can expose n8n workflows as MCP tools for other AI systems
- Code nodes for JavaScript or Python anywhere in a workflow

**D365 Integration:**
- Native Microsoft Dynamics CRM node for D365 CE (create, update, delete, get accounts)
- HTTP Request node with Microsoft OAuth for D365 F&O OData endpoints
- CData Connect AI provides managed MCP connections to D365 F&O from n8n
- No native D365 F&O node — requires HTTP Request or third-party connector

**Strengths for Qosina:**
- Visual workflow builder means non-developers (business analysts, power users) can understand and maintain automations
- Self-hosting on Azure gives full data control — critical for medical device compliance
- AI agent workflows with human-in-the-loop checkpoints at any point
- Git-based version control for workflows — audit trail for changes
- Execution logs and monitoring dashboard for compliance
- Fast prototyping — build an automation in hours, not days
- Cost-effective — self-hosted has no execution limits

**Weaknesses:**
- D365 F&O integration requires HTTP Request node with custom OData calls (no native node)
- Complex document parsing (OCR, handwritten forms) may need external services
- Less flexible than pure Python for deeply custom AI logic
- Another system for IT to maintain and monitor
- Learning curve for the team, though lower than custom code

**Best fit for:** Workflows with clear trigger → process → action patterns, especially where business users need to understand and modify the flow. Good for: email routing, approval workflows, data sync between systems, scheduled reports, notifications.

### Option B: Custom Python (FastAPI + LangGraph + Claude)

**What it is:** Building from scratch using Python. FastAPI for service endpoints, LangGraph/LangChain for AI agent orchestration, direct Claude API calls, standard Python libraries for document parsing. Full control, full flexibility, full maintenance burden.

**What Matt already has in production:**
- ToteTaxi: LangGraph ReAct agent with 6 tools, SSE streaming, HMAC webhook validation, 310+ tests, 22-parameter booking handoff, human-in-the-loop confirmation flow
- Qosina Round 3 demo: FastAPI + LangGraph + SQLite + 7 tools + approval queue + SSE streaming, deployed to Railway
- Photo store: LangChain shopping agent, pgvector semantic search
- Deep experience with: Claude API, LangSmith tracing, tool-calling patterns, pure function tool architecture (business logic in tools.py, orchestration in agent.py)

**AI Capabilities (maximum flexibility):**
- Full control over agent architecture, prompting, tool design
- Can implement complex multi-step reasoning chains
- Constitutional AI patterns (prompt-level guardrails for naming conventions, data standards)
- Custom confidence scoring, fuzzy matching, entity extraction
- Can use any combination of models (Claude for reasoning, specialized models for OCR)
- LangSmith for production-grade tracing and observability
- **OpenRouter integration for LLM failover** — route through a unified API gateway with Claude as primary, automatic failover to GPT-4o or Gemini if Claude's API is down or rate-limited. OpenAI-compatible API means LangChain/LangGraph work with zero code changes — swap `ChatAnthropic` for `ChatOpenAI` with OpenRouter's base URL. Supports tool calling, streaming, and model fallbacks natively. Only ~25ms routing overhead. Data policy controls let you restrict to providers that don't store/train on your data (critical for medical device compliance).

**D365 Integration:**
- Python requests library + Azure AD OAuth2 for D365 OData endpoints
- Full control over API call patterns, caching, error handling
- Can implement Redis caching for frequently-accessed data
- Can handle complex OData queries ($filter, $expand, $select)

**Strengths for Qosina:**
- Maximum flexibility for complex AI logic (document parsing, constitutional frameworks, confidence scoring)
- Matt's proven architecture — same patterns already running in production
- Can be deployed to Azure (their cloud) as a containerized service
- Unit testable — pure function tools with business logic separated from orchestration
- Production-grade observability through LangSmith
- Human-in-the-loop enforced architecturally (no write tools to system of record)
- **Production resilience via OpenRouter** — zero-downtime LLM failover. Claude primary → GPT-4o → Gemini fallback chain. Single API key, unified billing, provider-level data policy controls. This was specifically discussed with Tom in the Round 3 interview as a pattern for enterprise reliability.

**Weaknesses:**
- Requires a developer to maintain, modify, and extend
- Higher initial development time than n8n
- Matt is the single point of knowledge until team is trained
- No visual builder for non-technical users
- More infrastructure to manage (Docker, CI/CD, monitoring)
- OpenRouter adds a third-party dependency (mitigated: can fall back to direct Claude API by changing one env var)

**Best fit for:** Use cases requiring complex AI reasoning, multi-step document processing, custom matching algorithms, constitutional AI patterns, or anything where the AI logic is the hard part and standard workflow tools can't handle the nuance.

### Option C: Microsoft Power Platform (Power Automate + Copilot Studio + AI Builder)

**What it is:** Microsoft's low-code/no-code platform. Power Automate for workflow orchestration, Copilot Studio for AI agent capabilities, AI Builder for document processing and AI models. Native integration with D365 and the entire Microsoft ecosystem.

**AI Capabilities (evolving rapidly):**
- AI Builder: Document processing models for invoices, receipts, ID documents. OCR with high accuracy even on low-quality scanned images. Custom document processing models trainable on specific formats
- Copilot Studio: Conversational AI agents with generative answers from knowledge sources, generative actions that dynamically select plugins, multi-channel deployment (Teams, web, WhatsApp)
- Power Automate: Cloud flows, desktop flows (RPA), process mining. 2026 Wave 1 introduces AI agent authoring, self-healing desktop flows, and Copilot Studio-powered actions in flows
- GPT-5 Smart Mode in Copilot Studio adaptively selects the best AI model per task
- Advanced approvals with native HITL experiences
- MCP support coming (connects to external AI systems)

**D365 Integration (native — this is the killer advantage):**
- Power Automate has native D365 F&O and CE connectors — no HTTP configuration needed
- Triggers directly from D365 events (new record, status change, field update)
- Dataverse integration for D365 CE data
- Power Apps for custom UI directly on D365 data
- Process mining can analyze existing D365 workflows to identify bottlenecks
- Everything runs in the same Azure tenant — single auth, single security boundary

**Licensing (important gotcha):**
- AI Builder and Copilot Studio features consume "Copilot Credits"
- Microsoft is transitioning from AI Builder credits to Copilot Credits (2025-2026)
- Each AI action (document processing, prompt execution) consumes credits
- Can get expensive at scale without proper capacity planning
- Qosina likely already has Power Platform licenses through their D365 subscription

**Strengths for Qosina:**
- Native D365 integration — zero configuration for data access
- Already in their Microsoft ecosystem — no new vendor, no new security review
- Business users can build and modify flows with minimal IT support
- Built-in approval workflows with Teams integration
- AI Builder document processing is production-ready for invoices and structured forms
- Compliance-friendly — everything stays in their Azure tenant
- Microsoft support and enterprise SLAs

**Weaknesses:**
- AI model flexibility is limited — you're using Microsoft's models, not Claude (ironic given Qosina standardized on Claude for development)
- Custom AI logic is constrained by what Copilot Studio and AI Builder support
- Complex document parsing (handwritten forms, varied supplier spec sheets) may hit accuracy limits
- Licensing costs can escalate with high-volume AI operations
- Less transparent than custom code — harder to debug and audit AI decisions
- Vendor lock-in to Microsoft ecosystem
- Cannot easily use Claude as the reasoning engine within Power Platform flows (you'd need to call Claude API via HTTP connector, adding complexity)

**Best fit for:** Workflows that are primarily about routing, approval, and data movement between D365 and other Microsoft tools. Good for: simple document processing, approval chains, scheduled tasks, notifications, basic AI classification. Less good for complex AI reasoning or when you need Claude specifically.

---

## PART 3: USE CASE DEEP DIVE

### Use Case 1: Automate Sales Order Entry from Emails & Documents

**The Business Problem:**
The CX team receives purchase orders via email in wildly different formats — PDFs, typed email bodies, scanned documents, occasionally handwritten forms. Each order must be manually read, interpreted, and keyed into D365 F&O as a sales order with correct customer, part numbers, quantities, and pricing. This is slow, error-prone, and doesn't scale.

**Why It's Hard:**
- Document format diversity — PDFs, scans, typed emails, handwritten. Each needs different parsing strategies.
- Fuzzy matching — customer might write "stopcock 3-way" and mean Part #11195. Part numbers might have typos. Customer names might not exactly match the master data.
- Pricing validation — does the quoted price match the customer's contracted pricing? Volume discounts? Special pricing agreements?
- Edge cases — partial orders, ambiguous items, new customers not in the system, pricing discrepancies.
- Medical device orders have additional compliance requirements (lot tracking, certs) — Phase 1 should focus on standard products.

**The Architecture:**

```
Email arrives (Outlook/Exchange)
    │
    ▼
Email trigger (Power Automate or n8n watches mailbox)
    │
    ▼
Document extraction
    ├── PDF attachment → Claude vision or AI Builder OCR
    ├── Email body text → Direct text parsing by Claude
    ├── Scanned image → OCR (AI Builder or Textract) → Claude
    └── Handwritten → OCR with low confidence → always routes to human
    │
    ▼
Claude AI Agent (LangGraph)
    ├── Tool: match_customer(name, email, PO reference) → fuzzy match against D365 customer master
    ├── Tool: match_products(descriptions, part_numbers) → fuzzy match against product catalog
    ├── Tool: validate_pricing(customer_id, items) → check against contracted pricing
    ├── Tool: check_inventory(items) → verify stock availability
    └── Tool: create_order_approval(structured_order) → send to approval queue
    │
    ▼
Confidence scoring
    ├── HIGH confidence (all fields matched, known customer, standard parts) → auto-route to approval
    ├── MEDIUM confidence (some fuzzy matches, minor discrepancies) → flag specific fields for human review
    └── LOW confidence (new customer, ambiguous items, pricing mismatch) → full human review
    │
    ▼
Human-in-the-Loop Review UI
    ├── Side-by-side: original document | extracted & matched data
    ├── Flagged fields highlighted in yellow/red
    ├── One-click approve, reject, or edit individual fields
    └── On approve → create sales order in D365 F&O via OData API
```

**Phased Rollout:**
- Phase 0 (Week 1-2): Parse a sample of real PO emails/documents. Establish baseline accuracy. Identify the 3-5 most common formats.
- Phase 1 (Month 1): Standard product orders from top 10 customers (known formats, known pricing). Human reviews 100% of orders, AI pre-fills the form. Measure time savings.
- Phase 2 (Month 2-3): Expand to all standard product customers. Introduce confidence-based auto-routing (high confidence → auto-approve under $X threshold, everything else → human review).
- Phase 3 (Month 4+): Add medical device order support (lot tracking, compliance fields). Add handwritten form parsing. Expand auto-approval thresholds based on accuracy data.

**Tool Recommendation:**
HYBRID: n8n for the email trigger and routing workflow + Custom Python (Claude) for the document parsing and fuzzy matching logic.

Why not pure Power Platform? AI Builder's document processing is good for structured invoices but struggles with the diverse, unstructured formats described here. Claude's vision capabilities and reasoning are better suited for interpreting varied PO formats. Plus, Qosina standardized on Claude — use it.

Why not pure custom Python? The email monitoring, routing, and basic orchestration don't need custom code. n8n handles that cleanly with its email trigger → webhook → routing pattern. Save the custom code for where it adds value: the AI reasoning.

Why not pure n8n? The fuzzy matching against 5,000+ SKUs and the confidence scoring logic benefit from purpose-built Python tools with proper test coverage.

**What they might ask:**
- "How do you handle a PO format you've never seen?" → Claude's reasoning handles novel formats naturally. Log it, learn from it, add to test suite.
- "What's the accuracy target?" → Start measuring immediately. 95%+ field-level accuracy for known formats in Phase 1. Track per-field accuracy to identify weak spots.
- "How does this interact with Celigo?" → Celigo already handles EDI order processing. This handles the non-EDI channel (email POs). They complement each other.

---

### Use Case 2: Automate Accounts Payable Processing

**The Business Problem:**
Three sub-problems that finance leadership called "waste of human effort":
1. **Cash application** — matching incoming payments to open invoices. Sounds simple, but: penny discrepancies from rounding, partial payments, one payment covering multiple invoices, credits and adjustments.
2. **Three-way invoice matching** — verifying that the vendor invoice matches the PO (what we ordered) and the receipt (what we received). Discrepancies = manual investigation.
3. **Collections prioritization** — which overdue accounts to chase first. Currently manual analysis of payment patterns.

**Why It's Hard:**
- The "long tail" of edge cases: penny rounding discrepancies, partial payments, credits applied, early payment discounts taken, payments applied to wrong invoices.
- Three-way matching at scale requires tolerance rules (e.g., allow $0.05 variance on rounding, flag anything >$X).
- Collections prioritization requires pattern analysis across historical payment data — who pays late, who's trending toward non-payment, who's worth the effort.

**The Architecture:**

```
CASH APPLICATION FLOW:
Bank payment file (or Celigo sync)
    │
    ▼
Parse payment details (amount, reference, payer)
    │
    ▼
Matching engine
    ├── Exact match (invoice # + exact amount) → auto-apply
    ├── Fuzzy match (amount matches, reference close) → suggest match
    ├── Partial payment (amount < invoice total) → flag + suggest allocation
    ├── Overpayment → flag for credit memo
    └── No match → queue for human investigation
    │
    ▼
Threshold-based HITL
    ├── Auto-approve: exact matches under $5,000
    ├── Quick review: fuzzy matches (show match reasoning)
    └── Full review: no matches, partial payments, large amounts

THREE-WAY MATCHING FLOW:
Vendor invoice received
    │
    ▼
AI Builder or Claude extracts invoice data (vendor, items, quantities, amounts)
    │
    ▼
Match against D365 data
    ├── Find PO by PO number or vendor + date range
    ├── Find receipt by PO + item
    ├── Compare: PO quantity vs receipt quantity vs invoice quantity
    ├── Compare: PO unit price vs invoice unit price
    └── Flag variances outside tolerance
    │
    ▼
Variance classification
    ├── Within tolerance ($0.05 rounding) → auto-approve
    ├── Quantity mismatch → flag with specific discrepancy
    ├── Price mismatch → flag with contract reference
    └── Missing receipt → hold until goods received

COLLECTIONS PRIORITIZATION:
Scheduled job (daily or weekly)
    │
    ▼
Analyze D365 AR aging data
    ├── Payment history patterns (average days to pay, trend direction)
    ├── Account value (total annual spend, strategic importance)
    ├── Current exposure (total overdue amount)
    └── Risk scoring (combine factors into priority rank)
    │
    ▼
Generate prioritized collections list
    ├── High priority: large amounts, worsening payment trends
    ├── Medium: overdue but historically reliable
    └── Low: small amounts, good history, likely coming
    │
    ▼
Create outreach recommendations in approval queue
```

**Phased Rollout:**
- Phase 0 (Week 1-2): Analyze a month of actual cash application data. How many are exact matches? What % are the "hard" ones? Establish baseline.
- Phase 1 (Month 1): Cash application only — exact match auto-apply (which is likely 60-70% of payments). Everything else goes to human with AI-suggested matches. Measure time savings.
- Phase 2 (Month 2-3): Add three-way invoice matching with tolerance rules. Start with a narrow tolerance and widen as accuracy is proven.
- Phase 3 (Month 4+): Add collections prioritization. Add fuzzy matching for cash application (partial payments, credits). Expand auto-approval thresholds.

**Tool Recommendation:**
POWER PLATFORM for the core workflow + Custom Python for collections intelligence.

Why Power Platform here? This is the one use case where it genuinely shines. The invoice matching logic is mostly deterministic (compare numbers, apply tolerance rules). Power Automate has native D365 F&O connectors for reading POs, receipts, and invoices. AI Builder can handle structured invoice parsing. The approval workflow integrates natively with Teams. And critically — the finance team already uses Microsoft tools daily. They could own this workflow.

Why custom Python for collections? The payment pattern analysis and risk scoring benefit from Claude's reasoning capabilities. Analyzing 12+ months of payment history, identifying trends, and generating prioritized recommendations is an AI reasoning task, not a rule-based task.

Why not n8n? It could work, but it doesn't add value over Power Platform here since the D365 integration is native in Power Platform and would require HTTP configuration in n8n. Don't add a tool just to add a tool.

**What they might ask:**
- "What about the penny discrepancies?" → Define tolerance rules in configuration, not code. Start tight ($0.05), widen based on data. Log every auto-approved variance for audit.
- "How does this interact with their existing Celigo flows?" → Celigo likely handles some of the invoice/payment sync already. This layer sits on top — it's the intelligence, not the plumbing.
- "What if the three-way match can't find the PO?" → Queue for human with best-guess suggestions. Never auto-approve without a match. Log the failure for pattern analysis.

---

### Use Case 3: New Product Data Entry from Supplier Documents

**The Business Problem:**
Suppliers send spec sheets, certificates of analysis, catalogs, and technical drawings. Product Development staff manually extract 30+ data fields per SKU (dimensions, materials, tolerances, certifications, descriptions) and enter them into the D365 F&O item master. With 8,000+ SKUs and regular new additions, this is enormous time investment. The team specifically mentioned that AI needs a "constitutional framework" for interpreting supplier data according to Qosina naming conventions and product standards.

**Why It's Hard (and the most interesting use case):**
- **Document diversity:** Spec sheets come in every format — some are clean PDFs with structured tables, others are scanned catalogs, others are technical drawings with callouts. A certificate of analysis has completely different structure than a spec sheet.
- **30+ fields per SKU:** Not just "name and price." Dimensions (ID, OD, length), materials (polycarbonate, polypropylene, ABS), tolerances, sterilization compatibility, connection types (Male Luer Lock, Female Luer Slip), ISO compliance, shelf life, manufacturing environment requirements.
- **The constitutional framework:** This is the most interesting technical challenge. Qosina has specific naming conventions and product standards. A supplier might call a part a "3-way valve with Luer connections" but Qosina's convention might be "3-Way Stopcock, Male Luer Lock x Female Luer Lock x Female Luer Lock." The AI needs to translate supplier terminology into Qosina's standardized vocabulary — consistently, every time.
- **Consistency with 8,000+ existing SKUs:** A new product entry must be consistent with how similar products are already cataloged. If all other polycarbonate stopcocks list the material as "Polycarbonate (PC)" then the new one can't say "PC plastic."
- **Landed cost estimation:** Extracted product data feeds downstream cost calculations (weight, dimensions, country of origin, tariff classification).

**The Architecture:**

```
Supplier document received
    │
    ▼
Document type classification
    ├── Spec sheet → structured field extraction
    ├── Certificate of analysis → compliance field extraction
    ├── Catalog page → product identification + field extraction
    └── Technical drawing → dimension extraction (vision model)
    │
    ▼
Claude AI Agent with Constitutional Framework
    │
    ├── SYSTEM PROMPT includes "Qosina Product Data Constitution":
    │   ├── Naming conventions (e.g., "3-Way Stopcock" not "Three Way Valve")
    │   ├── Material naming standards (e.g., "Polycarbonate (PC)" not "PC plastic")
    │   ├── Connection type vocabulary (Male/Female Luer Lock/Slip per ISO 80369-7)
    │   ├── Unit standards (dimensions in mm, weights in g)
    │   ├── Category taxonomy (Stopcocks & Manifolds, Tubing, Connectors, etc.)
    │   └── Description format templates per category
    │
    ├── Tool: extract_fields(document) → extract raw data from supplier doc
    ├── Tool: normalize_to_conventions(raw_fields) → apply naming conventions
    ├── Tool: find_similar_products(category, material, connection_type) → find existing SKUs for consistency check
    ├── Tool: validate_consistency(new_fields, similar_products) → flag deviations from catalog patterns
    ├── Tool: estimate_landed_cost(dimensions, weight, origin_country) → preliminary cost estimate
    └── Tool: create_item_approval(normalized_fields, confidence_scores, similar_products) → send to review queue
    │
    ▼
Human Review UI
    ├── Left panel: original supplier document (rendered or OCR'd)
    ├── Right panel: extracted + normalized fields with confidence scores per field
    ├── Similar existing products shown for reference ("here's how we catalog similar items")
    ├── Flagged fields where AI confidence is low or convention match is uncertain
    ├── Edit individual fields, approve, or reject
    └── On approve → create item master record in D365 F&O
```

**The Constitutional Framework (this is the key innovation):**

This is where you show you understood what the Product Development team actually meant. The "constitution" is a set of rules embedded in the system prompt and validation logic:

```
QOSINA PRODUCT DATA CONSTITUTION

1. NAMING: Product names follow the pattern:
   [Type], [Gender] [Connection Type] x [Gender] [Connection Type]
   Example: "3-Way Stopcock, Male Luer Lock x Female Luer Lock x Female Luer Lock"

2. MATERIALS: Always use full name with abbreviation in parentheses.
   Correct: "Polycarbonate (PC)"
   Wrong: "PC", "Polycarbonate plastic", "PC plastic"

3. CONNECTIONS: Use ISO 80369-7 terminology.
   Correct: "Male Luer Lock", "Female Luer Slip"
   Wrong: "M Luer", "luer lock female", "LL"

4. DIMENSIONS: Always in millimeters. Format: X.Xmm
   Inner diameter = "ID", Outer diameter = "OD", Length = "L"

5. CATEGORIES: Use existing Qosina taxonomy.
   Products must be assigned to an existing category from the catalog.

6. DESCRIPTIONS: Follow category-specific templates.
   Stopcocks: "[Material] [type] stopcock with [connection description]. [Special features]."

7. CONSISTENCY: New entries must match patterns of existing similar products.
   If 47 other PC stopcocks all list material as "Polycarbonate (PC)", the 48th must too.
```

This is enforceable in code through validation functions that compare extracted fields against the existing catalog patterns. It's also enforceable through the system prompt, giving Claude the rules to follow during extraction. Belt and suspenders.

**Phased Rollout:**
- Phase 0 (Week 1-2): Audit 20-30 existing product entries to codify the implicit naming conventions and standards. Build the constitutional framework document.
- Phase 1 (Month 1): Spec sheets only (most structured format). Top 3 product categories. Human reviews 100% with AI pre-fill. Measure field-level accuracy and time savings.
- Phase 2 (Month 2-3): Add certificate of analysis parsing. Expand to all product categories. Introduce confidence-based auto-fill for high-confidence fields.
- Phase 3 (Month 4+): Add catalog page and technical drawing parsing. Integrate landed cost estimation. Build feedback loop where human corrections improve the constitutional framework.

**Tool Recommendation:**
CUSTOM PYTHON (Claude) — this is the most clear-cut case for it.

Why custom Python? The constitutional framework concept is a prompt engineering and AI reasoning problem. This requires Claude's full reasoning capabilities, not a workflow tool's AI wrapper. The consistency validation against 8,000+ existing SKUs requires vector similarity search or structured queries that benefit from purpose-built tools. And the document diversity demands the kind of flexible parsing that Claude's vision and text capabilities handle best.

Why not Power Platform? AI Builder's document processing models are trained on common document types (invoices, receipts, ID documents). Supplier spec sheets for medical device components are a niche format. You'd need to train custom models, which is possible but slower and less flexible than Claude.

Why not n8n? The AI reasoning here is the entire value proposition. n8n's AI agent node is good for simpler flows, but the constitutional framework + consistency validation + multi-document-type parsing is complex enough to warrant custom code with full test coverage.

**What they might ask:**
- "How do you build the constitutional framework?" → Start by auditing existing entries to extract the implicit rules. Work with Product Development to validate and refine. Embed in system prompt + validation code.
- "What about documents in other languages?" → Claude handles multilingual documents natively. Add a translation/normalization step.
- "How do you handle ambiguous specs?" → Flag for human review with AI's best guess. Never auto-create an item master record with low-confidence fields.

---

## PART 4: CROSS-CUTTING THEMES

### Shared Architecture Across All Three Use Cases

The demos should show that these aren't three separate systems — they share a common foundation:

1. **Common AI agent backbone:** FastAPI + LangGraph + Claude (via OpenRouter). Same architecture, different tools per use case.
2. **Common LLM resilience layer:** All agents route through OpenRouter with Claude as primary and automatic failover to GPT-4o → Gemini. The agent, tools, and approval workflow are model-agnostic — they don't know or care which LLM is answering. This is the API failover pattern you discussed with Tom in Round 3.
3. **Common approval queue pattern:** Every use case routes AI recommendations through human review before touching the system of record. Same UI component, different approval types.
4. **Common D365 integration layer:** Mock OData responses in demo, real OData calls in production. Same abstraction layer.
5. **Common confidence scoring:** Every extraction/matching result has a confidence score that determines routing (auto-approve, quick review, full review).
6. **Common observability:** LangSmith tracing across all use cases. Every AI decision is logged and auditable.

### The LLM Resilience Layer (OpenRouter)

This deserves its own section because it's a direct callback to the Round 3 interview conversation with Tom about LLM routing for API failover.

**The Problem:** Enterprise systems can't go down. If your AI automation depends on a single LLM provider and that provider has an outage or rate-limits you, your entire workflow stops. For a medical device distributor processing orders and invoices, downtime means lost revenue and compliance risk.

**The Solution:** Route all LLM calls through OpenRouter, a unified API gateway that handles provider selection and failover transparently.

**How it works in our architecture:**

```python
# backend/shared/llm_provider.py

import os
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic

def get_model(temperature: float = 0):
    """
    Factory function for LLM provider.
    
    In production (USE_OPENROUTER=true): Routes through OpenRouter with 
    automatic failover. Claude primary → GPT-4o → Gemini.
    
    In development (USE_OPENROUTER=false): Direct Claude API for faster 
    iteration and no routing overhead.
    """
    if os.getenv("USE_OPENROUTER", "true").lower() == "true":
        return ChatOpenAI(
            model=os.getenv("PRIMARY_MODEL", "anthropic/claude-sonnet-4-20250514"),
            base_url="https://openrouter.ai/api/v1",
            api_key=os.getenv("OPENROUTER_API_KEY"),
            temperature=temperature,
            default_headers={
                "HTTP-Referer": "https://qosina-demo-production.up.railway.app",
                "X-Title": "Qosina Enterprise AI Assistant"
            },
            # OpenRouter model fallback config via extra_body when supported
        )
    else:
        return ChatAnthropic(
            model="claude-sonnet-4-20250514",
            api_key=os.getenv("ANTHROPIC_API_KEY"),
            temperature=temperature,
        )
```

**What this gives Qosina:**
- **Zero-downtime AI:** If Anthropic's API goes down at 2 AM, the system automatically fails over to GPT-4o. Orders keep processing. Invoices keep matching.
- **Rate limit protection:** If Claude hits rate limits during a high-volume period, overflow routes to backup models automatically.
- **Single billing:** One OpenRouter dashboard tracks spend across all providers. No juggling multiple API accounts.
- **Data policy controls:** OpenRouter lets you restrict to providers that don't store or train on your data — critical for medical device data containing part specifications and customer information.
- **Model experimentation:** Want to test whether GPT-4o handles invoice parsing better than Claude for a specific format? Change one string. The tools and approval workflow don't change.

**What to say in the interview:**
"Remember our conversation about LLM routing for API failover? I built it. All three demos route through OpenRouter — Claude is primary, but if Anthropic's API goes down or hits rate limits, the system automatically fails over to GPT-4o, then Gemini. Zero downtime. The agent, tools, and approval workflow don't know or care which model is answering. The routing is transparent. In development I call Claude directly for speed. In production I route through OpenRouter for resilience. It's a one-line configuration change."

### How This Connects to Celigo

Celigo is already handling system-to-system integration (EDI, order sync, invoice data movement). The AI layer sits on top — it handles the intelligent parts that Celigo can't: reading unstructured documents, fuzzy matching, reasoning about data quality, making recommendations. They're complementary, not competing.

### The n8n + Custom Python + Power Platform Sweet Spot

The mature answer isn't "use my stack for everything." It's:
- **Power Platform** for workflows that are primarily about D365 data routing, approval chains, and structured document processing within the Microsoft ecosystem.
- **n8n** for workflows that connect multiple systems, need visual maintainability for the team, and have clear trigger → process → action patterns.
- **Custom Python + Claude** for workflows where the AI reasoning IS the value — complex document parsing, constitutional frameworks, pattern analysis, fuzzy matching.

Real enterprise environments use all three. Show that you understand when each is appropriate.

---

## PART 5: THE BUILD PLAN

### Strategy: Build Demos in Python, Talk About n8n and Power Platform

You are NOT building demos in three different platforms. You don't have time and you don't need to. The brief says "you do not need to build anything." You're already going beyond by building working demos.

**What you BUILD:** Three custom Python demos (FastAPI + LangGraph + OpenRouter), one app, one Railway URL.
**What you SHOW as diagrams:** For each use case, a simple architecture diagram of what the n8n version and Power Platform version would look like. Boxes and arrows. You talk through them, explain trade-offs, make your recommendation.
**What you SAY:** "I built the custom Python version because I wanted to demonstrate the full AI reasoning. Here's what the n8n version would look like [show diagram]. Here's what the Power Platform version would look like [show diagram]. My recommendation for this use case is X, and here's why."

### Foundation: Fork the Round 3 Demo

You already have a working demo deployed to Railway from the last interview:
- **Live:** https://qosina-demo-production.up.railway.app
- **Repo:** https://github.com/mattyray/qosina
- **Code export:** qosina_code_export.txt in project knowledge

What already exists and can be reused:
- FastAPI app with SSE streaming endpoint ✅
- LangGraph ReAct agent with tool calling ✅
- SQLite database with OData-formatted JSON responses ✅
- Approval queue (create, approve, reject, filter by type) ✅
- Seeded Qosina product data — real part numbers, specs, compatibility maps, customers, orders ✅
- Single HTML frontend with Tailwind CSS, vanilla JS, EventSource for SSE ✅
- Tool activity panel showing which tools the agent calls in real time ✅
- Railway deployment with Docker ✅
- 7 tools: search_products, check_inventory, find_compatible_parts, check_expiring_inventory, check_low_stock, get_customer_order_history, create_approval ✅

What you ADD on top:
- OpenRouter LLM provider layer (swap ChatAnthropic for ChatOpenAI with OpenRouter base URL)
- Tab navigation between three use cases
- Per-use-case agents with specialized tools and system prompts
- New seed data: vendors, POs, receipts, invoices, payments (UC2); expanded item master fields, naming conventions (UC3)
- New UI panels per use case (document upload for UC1/UC3, matching dashboard for UC2)
- Sample documents (fake POs, vendor invoices, supplier spec sheets)
- Architecture diagrams for n8n and Power Platform versions (embedded in the UI as an "Architecture" tab or as images)
- Tests per use case

### What Each Demo's UI Looks Like

All three share: the approval queue panel (right side), the LLM provider status bar (top: "🟢 Claude via OpenRouter | Fallbacks: GPT-4o → Gemini"), and tab navigation.

**Use Case 1 Tab — Sales Order Entry:**
- Left: document upload/paste area (paste PO text, upload PDF/image, or pick from sample POs)
- Center: AI agent chat showing the extraction and matching reasoning in real time
- Right: structured extraction preview — customer name, line items (part#, qty, price), delivery date, PO reference — each field has a green/yellow/red confidence indicator
- Below extraction: "Create Sales Order" approval card showing the complete order ready for human review
- On approve: "Sales order SO-001234 created in D365" (simulated)

**Use Case 2 Tab — AP Processing:**
- Left: incoming invoices list (seeded with sample vendor invoices, some matching perfectly, some with discrepancies)
- Center: three-way match view — side-by-side comparison of PO vs Receipt vs Invoice with discrepancies highlighted red, matches green
- Tolerance indicator: "Variance: $0.03 — within $0.05 threshold → Auto-approved" or "Variance: $47.50 — exceeds threshold → Flagged for review"
- Collections tab: customers ranked by risk score with AI reasoning ("Customer DEF: payment trend worsening — 5 days late → 30 days → 60 days")
- Approval queue shows: payment applications, invoice approvals, collection outreach recommendations

**Use Case 3 Tab — Product Data Entry:**
- Left: document upload area + sample spec sheets to pick from
- Center: side-by-side view — original document on left, extracted + normalized fields on right
- Each extracted field shows: raw value from supplier doc → normalized Qosina value (with constitutional rule applied)
- Confidence scores per field. Flagged fields where the AI is unsure or the convention match is uncertain
- "Similar Products" panel showing 2-3 existing SKUs with the same category/material for consistency reference
- Approval queue shows: "Create Item Master record — 34 fields extracted, 31 high confidence, 3 flagged"

### Architecture (expanded from Round 3)

```
qosina-round4/                   # Fork of github.com/mattyray/qosina
├── CLAUDE.md                    # Updated master context for Claude Code
├── backend/
│   ├── main.py                  # FastAPI app — expanded with tab routing, per-UC endpoints
│   ├── shared/
│   │   ├── database.py          # SQLite setup — expanded schema for all 3 use cases
│   │   ├── models.py            # Pydantic models — expanded
│   │   ├── approval.py          # Approval queue logic (reuse from Round 3, add new types)
│   │   └── llm_provider.py      # NEW: OpenRouter factory with failover config
│   ├── use_case_1/              # Sales Order Entry
│   │   ├── agent.py             # LangGraph agent with UC1 tools + system prompt
│   │   ├── tools.py             # parse_document, match_customer, match_products, validate_pricing
│   │   └── seed.py              # Customer master, pricing tiers, sample POs
│   ├── use_case_2/              # AP Processing
│   │   ├── agent.py             # LangGraph agent with UC2 tools + system prompt
│   │   ├── tools.py             # parse_invoice, three_way_match, match_payment, score_collections
│   │   └── seed.py              # Vendors, POs, receipts, invoices, payments (with intentional discrepancies)
│   └── use_case_3/              # Product Data Entry
│       ├── agent.py             # LangGraph agent with UC3 tools + constitutional framework in prompt
│       ├── tools.py             # extract_fields, normalize_conventions, validate_consistency, find_similar
│       ├── constitution.py      # Qosina naming rules as structured data (used by tools + prompt)
│       └── seed.py              # Expanded product catalog (30+ fields), naming rules, sample spec sheets
├── static/
│   └── index.html               # Expanded: tab navigation, per-UC panels, architecture diagram tab
├── sample_docs/                 # Fake POs, vendor invoices, supplier spec sheets (text + images)
├── tests/
│   ├── test_uc1_tools.py
│   ├── test_uc2_tools.py
│   └── test_uc3_tools.py
├── requirements.txt             # Add: langchain-openai (for OpenRouter)
├── Dockerfile
├── railway.toml
└── .env                         # OPENROUTER_API_KEY, USE_OPENROUTER=true, ANTHROPIC_API_KEY (fallback)
```

### Day-by-Day Build Schedule

**Day 1 (Tue Apr 1 — today):** RESEARCH & PLAN ← you are here
- Deep dive on all technologies (done)
- Read and understand the project brief (done)
- Build deep dive document (done)
- Build study guide (done)
- Send clarifying questions to Tom (done)
- Sign up for OpenRouter, add credits (~$20), get API key

**Day 2 (Wed Apr 2):** FORK & EXPAND FOUNDATION
- Fork the Round 3 repo
- Add llm_provider.py — swap ChatAnthropic for OpenRouter ChatOpenAI
- Test that tool calling and SSE streaming still work through OpenRouter
- Add tab navigation to the frontend (3 tabs + Architecture tab)
- Expand the database schema for UC2 and UC3 data
- Add new approval types (sales_order, invoice_match, payment_apply, item_master)
- Deploy expanded skeleton to Railway to confirm everything still works

**Day 3 (Thu Apr 3):** USE CASE 1 — SALES ORDER ENTRY
- New seed data: customer master with pricing tiers
- Create 3-4 sample PO documents (text pastes, maybe a fake PDF)
- Build tools: match_customer, match_products, validate_pricing
- Build UC1 agent with specialized system prompt
- Build document paste/upload UI panel + extraction preview with confidence indicators
- Write tests

**Day 4 (Fri Apr 4):** USE CASE 1 POLISH + USE CASE 2 START
- Morning: test UC1 end-to-end, fix bugs
- Afternoon: seed data for UC2 — vendors, purchase orders, receipts, invoices, payments (with penny discrepancies and partial payments)
- Build tools: parse_invoice, three_way_match, check_discrepancies

**Day 5 (Sat Apr 5):** USE CASE 2 — AP PROCESSING
- Build matching dashboard UI (green/yellow/red, tolerance indicators)
- Build cash application matching tool
- Build collections scoring tool
- Build UC2 agent with specialized system prompt
- Write tests, test end-to-end

**Day 6 (Sun Apr 6):** USE CASE 3 — PRODUCT DATA ENTRY (START)
- Build constitution.py — Qosina naming rules as structured data
- Expand product catalog seed data with all 30+ fields per SKU
- Create 2-3 sample supplier spec sheets (text-based for demo)
- Build tools: extract_fields, normalize_to_conventions, find_similar_products

**Day 7 (Mon Apr 7):** USE CASE 3 — PRODUCT DATA ENTRY (FINISH)
- Build tools: validate_consistency, estimate_landed_cost
- Build UC3 agent with system prompt containing constitutional framework
- Build side-by-side UI (original doc | normalized fields with confidence scores)
- Write tests, test end-to-end

**Day 8 (Tue Apr 8):** INTEGRATION & DEPLOY
- Make sure all three tabs work together cleanly
- Deploy to Railway
- Test every demo scenario on the live URL
- Fix SSE streaming bugs, UI glitches, agent edge cases
- Performance check — responses need to be fast enough for a live demo

**Day 9 (Wed Apr 9):** ARCHITECTURE DIAGRAMS & PRESENTATION
- Build architecture diagrams for each use case:
  - Custom Python version (what you built)
  - n8n version (boxes and arrows showing the visual workflow)
  - Power Platform version (boxes and arrows showing Power Automate + AI Builder + Teams)
- These can be a tab in the app itself or images you screen share
- Write your recommendation talking points per use case
- Write phased rollout timelines
- Write "risks and unknowns" notes

**Day 10 (Thu Apr 10):** REHEARSAL
- Full 90-minute run-through with timer
- 25-30 minutes per use case: problem → demo → architecture comparison → recommendation → phased rollout → risks
- Practice transitions between use cases
- Practice answering anticipated questions
- Time yourself — if you're running long, cut the demo scenarios

**Day 11 (Fri Apr 11):** BUFFER
- Fix anything that broke
- Final deploy and smoke test
- One more rehearsal pass
- Rest

---

## PART 6: WHAT SUCCESS LOOKS LIKE

You pull up one URL on the Teams screen share. Three tabs: Sales Orders, AP Processing, Product Data. The status bar shows: `🟢 Primary: Claude Sonnet 4 (via OpenRouter) | Fallbacks: GPT-4o → Gemini 2.0 Flash`. Tom sees that and immediately remembers the conversation. For each use case, you:

1. **Explain the business problem** (30 seconds — you understand their pain)
2. **Show the architecture diagram** (1 minute — you think in systems)
3. **Run the live demo** (5-7 minutes — you can actually build it)
4. **Explain your tool recommendation** (3-5 minutes — n8n vs. custom vs. Power Platform, with honest trade-offs)
5. **Walk through the phased rollout** (2-3 minutes — you think in phases, not big bangs)
6. **Acknowledge risks and unknowns** (1-2 minutes — you're honest about what you don't know)
7. **Connect to the other use cases** (1 minute — shared patterns, reusable architecture)

The demo is the differentiator. Tom said "you don't need to build anything." You show up with three working applications seeded with their actual product data, using their AI platform (Claude), with the governance pattern (HITL) they care about, the LLM failover pattern Tom specifically discussed with you, deployed to a live URL they can click after the call.

Last time, Tom said he hadn't seen that level of effort in a long time. This time, multiply by three — and you built the thing he was thinking about into every one of them.
