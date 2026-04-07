# DEMO_SCENARIOS.md — Round 4 Interview Walkthrough

90-minute Teams call. ~25-30 min per use case + intro/outro.

## OPENING (5 min)

1. **The setup:** "I built working demos for all three use cases. Let me show you the live URL." Open https://qosina-demo-production.up.railway.app
2. **Architecture quick tour:** Point at the header model selector. "All AI calls route through OpenRouter — Claude is primary, with automatic failover to GPT-4o and Gemini. Same routing pattern we discussed last time."
3. **Header callouts:** "Agent cannot modify records — that's enforced architecturally. The only write tool is `create_approval`. Everything else is read-only."
4. **Tab tour (15 sec each):** Dashboard, Sales Order Entry, AP Processing, Product Data Entry, General Chat, Data Explorer, Architecture.

---

## USE CASE 1 — SALES ORDER ENTRY (~25 min)

### Business problem (30 sec)
"Your CX team gets POs via email. PDFs, scans, sometimes handwritten. Someone reads each one and types it into D365 manually."

### Architecture diagram (1 min)
Click Architecture tab. Walk through the UC1 row:
- n8n for email trigger and routing
- Custom Python (Claude) for the AI extraction and matching
- Power Platform falls short here — AI Builder doesn't handle vague descriptions or fuzzy matching against 5,000 SKUs

### Live demo (8 min)

Click Sales Order Entry tab.

**Demo 1: Clean PDF (happy path)** — 2 min
1. Drag `sample_docs/uc1_sales_orders/po_acme_medical.pdf` onto the chat area
2. Watch the agent stream:
   - Extracts customer, PO number, line items, ship-to, delivery date
   - Calls `match_customer` → finds CUST-001 at 95% confidence
   - Calls `match_products` → all three parts at 99% confidence (exact part numbers)
   - Calls `validate_pricing` → $2.57 matches Acme's contracted rate (10% discount on stopcocks)
   - Calls `check_inventory` → all in stock
   - Calls `create_approval`
3. Click the inline yellow approval card OR the "Review & Edit" button in the sidebar
4. Show the review panel:
   - Left: AI Summary tab — markdown breakdown
   - Click "Original Document" tab — show the PDF
   - Right: Editable form fields, all green confidence borders
5. **Switch the LLM in the header dropdown to GPT-4o.** "Same agent, same tools, same approval queue. Only the LLM changes."
6. Process the same PO again with GPT-4o. Show identical result.
7. Switch back to Claude. Approve the original.

**Demo 2: Handwritten edge case** — 3 min
1. Drag `po_handwritten_summit_surgical.png` (the messy one) into the chat
2. "Watch what happens with handwriting that's not great."
3. Agent reads what it can, finds Summit Surgical (CUST-006) at 95%, but flags ALL line items because the handwriting is illegible
4. Open the approval — show RED confidence borders on every line item
5. "The AI doesn't guess. It flags exactly what needs human review. In a medical device supply chain, this is exactly the behavior you want."
6. Reject it (or fix the fields manually to show the editable form)

**Demo 3: New customer + email body** — 3 min
1. Drag `po_email_pacific_coast.pdf` (email-style, plain text)
2. Agent processes — finds the items, but flags the customer as **NOT in the system**
3. Open the approval — customer field is RED, items are GREEN
4. "New customers need to be set up before an order can be created. The AI catches this, doesn't create an orphan order."

### Three-platform comparison (4 min)
Architecture tab:
- **n8n:** Visual workflow, native AI nodes, but its fuzzy matching maxes out at simple string similarity. No Claude integration depth.
- **Power Platform:** AI Builder for structured forms, but POs are NOT structured. AI Builder can't reason about 5,000 SKUs.
- **Custom Python:** Full Claude reasoning, full test coverage, fuzzy matching with confidence scoring.
- **Recommendation:** Hybrid. n8n watches the email inbox and routes to Python. Python does the AI work. Power Platform handles the final approval workflow with Teams notifications.

### Phased rollout (3 min)
- **Phase 0:** Audit 50 real POs from top customers. Establish format distribution and baseline accuracy targets.
- **Phase 1:** Top 10 customers, structured PDFs only, human reviews 100% of orders. Measure time savings.
- **Phase 2:** Expand to all standard product customers. Confidence-based auto-routing (high → quick review, low → full review).
- **Phase 3:** Medical device orders with compliance fields. Handwritten form support. Expanded auto-approval thresholds.

### Risks (1 min)
- New PO formats break extraction (mitigation: add to test suite, monitor accuracy per format)
- Customer master data quality (mitigation: AI flags low-confidence customer matches)
- Pricing changes mid-quote (mitigation: validate against current contracted rates at time of order)

---

## USE CASE 2 — AP PROCESSING (~25 min)

### Business problem (30 sec)
"Three sub-problems your finance team called 'waste of human effort.' Three-way invoice matching, cash application, collections prioritization."

### Architecture (1 min)
Architecture tab → UC2 row:
- Power Platform shines here because of native D365 F&O connectors and Teams approval cards
- Custom Python adds the intelligence layer (collections risk scoring, payment pattern analysis)
- n8n could work but offers no advantage over Power Platform for this use case

### Live demo (10 min)

Click AP Processing tab.

**Demo A: Three-Way Match** — 5 min
1. Click the "Three-Way Match All" quick action
2. Agent calls `get_vendor_invoices` to list all 5 vendor invoices
3. For each invoice, calls `three_way_match`:
   - **VINV-2026-001 (Precision Plastics)** → Perfect. Auto-approve.
   - **VINV-2026-002 (SinoMed)** → $0.03 penny discrepancy. Within $0.05 tolerance. Auto-approve with write-off note.
   - **VINV-2026-003, 004** → Perfect.
   - **VINV-2026-005 (TechValve)** → 500 invoiced, only 480 received. **Quantity mismatch.** Flag for human review.
4. Open the TechValve approval. Show the line items table with the discrepancy highlighted in red.
5. "Tolerance thresholds are configurable. Under $0.05 → auto-approve. $0.05-$50 → quick review. Over $50 → full investigation. These rules live in config, not code."

**Demo B: Vendor invoice upload** — 2 min
1. "But what if the invoice is brand new and not in the system yet?"
2. Drag `vendor_invoice_unknown_po.pdf` into the chat
3. Agent reads it, extracts vendor, PO reference, line items
4. Tries `three_way_match` against PO-2025-999 → doesn't exist
5. Creates approval flagged: "References PO that doesn't exist in system"
6. "In production this would integrate with the email/EDI inbound channel. Same Claude vision pipeline as UC1."

**Demo C: Cash Application** — 3 min
1. Click "Cash Application" quick action
2. Agent calls `get_unapplied_payments` → finds PAY-2026-006, $1,345 from CUST-003
3. Calls `match_payment` → MedLine has two overdue invoices: $1,012.50 and $337.50 (total $1,350)
4. Suggests applying the $1,345 to both with a $5 variance (likely a damage deduction)
5. Open the approval — show the suggested allocation with confidence scores
6. Reviewer can edit the allocation amounts and approve

### Collections prioritization (3 min)
1. Click "Collections Priority"
2. Agent calls `score_collections`:
   - **CUST-006 (Summit Surgical)** → HIGH priority (13 months silent, $867 overdue, premium tier)
   - **CUST-003 (MedLine)** → HIGH priority (multiple overdue invoices, declining order pattern)
3. Reasoning shown for each: "Severely overdue, no payment activity, premium account = high strategic value"
4. "Risk score combines amount, age, payment trend, and account tier. The AI flags who to call first, with reasoning."

### Three-platform comparison (3 min)
- **Power Platform wins** for invoice matching (deterministic logic + native D365 connectors + Teams approvals + finance team already uses it)
- **Custom Python wins** for collections intelligence (Claude reasoning over payment history)
- **n8n** = redundant here

### Phased rollout (2 min)
- **Phase 0:** Analyze one month of cash application. What % are exact matches?
- **Phase 1:** Cash app exact-match auto-apply (~60-70% of payments).
- **Phase 2:** Three-way matching with tight tolerance ($0.05). Widen as accuracy proves out.
- **Phase 3:** Collections scoring. Fuzzy matching for partial payments. Expanded auto-approval.

---

## USE CASE 3 — PRODUCT DATA ENTRY (~25 min)

### Business problem (30 sec)
"Suppliers send spec sheets in every format imaginable. Your Product Development team manually extracts 30+ fields per SKU and types them into D365. With 8,000+ SKUs, this is enormous."

### The constitutional framework concept (1 min)
"The team mentioned needing a 'constitutional framework' — non-negotiable rules for translating supplier terminology into Qosina standards. I built that as a database table. Adding a new rule is an INSERT, not a code change. The AI loads these rules every time it processes a document."

### Architecture (1 min)
Architecture tab → UC3 row:
- Full Custom Python. The constitutional framework + consistency check against 8,000 SKUs is an AI reasoning problem.
- Power Platform AI Builder is too rigid for this — it expects standardized forms.
- n8n's AI agent could call Claude but won't enforce rules in code. Need belt + suspenders.

### Live demo (10 min)

Click Product Data Entry tab.

**Demo 1: Wrong terminology spec sheet** — 5 min
1. Drag `sample_docs/uc3_product_data/spec_sheet_stopcock.pdf` into the chat
2. Agent extracts fields, then calls `get_naming_conventions` to load rules
3. Watch the normalizations happen:
   - "PC plastic" → "Polycarbonate (PC)" (rule: full name with abbreviation)
   - "M Luer Lock" → "Male Luer Lock" (rule: ISO 80369-7 terminology)
   - `0.106"` → "2.69mm" (rule: always millimeters)
   - "3-way valve" → "3-Way Stopcock" (rule: valve with luer = Stopcock)
4. Calls `find_similar_products` → loads 4 existing PC stopcocks for consistency comparison
5. Calls `validate_consistency` → confirms field formats match catalog patterns
6. Creates approval with structured data grouped by section
7. Open the approval. Show:
   - Sections: Basic Info, Dimensions, Connections, Compliance, Commercial
   - Each field shows raw_value (strikethrough) → normalized value
   - Rule applied per field
   - Confidence color borders
8. Edit a field if needed. Approve.

**Demo 2: Imperial measurements** — 3 min
1. Drag `spec_sheet_tubing_allied.pdf`
2. Agent converts every imperial measurement to millimeters
3. "3/16 inch ID" → "4.76mm ID"
4. "5/16 inch OD" → "7.94mm OD"
5. Show the conversions in the review panel

**Demo 3: Different document type** — 2 min
1. Drag `certificate_of_analysis_stopcock.pdf`
2. "This isn't a spec sheet — it's a Certificate of Analysis. Different structure entirely."
3. Agent adapts — extracts what it can (lot number, test results, materials)
4. "The framework handles ANY supplier document type because Claude reasons about what's in the document. We don't hardcode a parser per format."

### Three-platform comparison (3 min)
- **Custom Python** is the only choice. Constitutional framework + consistency validation + 30+ dynamic fields = AI reasoning problem.
- **Power Platform AI Builder** trained for standard forms (invoices, receipts), not niche supplier specs.
- **n8n's** AI agent node works but lacks the structured tool architecture for rule enforcement.

### Phased rollout (3 min)
- **Phase 0:** Audit 20-30 existing products with Product Development team. Codify the implicit naming rules into the database.
- **Phase 1:** Spec sheets only, top 3 categories. Human reviews 100% with AI pre-fill. Measure field-level accuracy.
- **Phase 2:** Add certificate of analysis parsing. Confidence-based auto-fill for high-confidence fields.
- **Phase 3:** Catalog pages, technical drawings (vision model). Landed cost integration. Feedback loop where corrections improve the rules.

---

## CLOSING (5 min)

### What this demo shows
1. **Same architecture pattern** across all three use cases
2. **Document parsing pipeline** reused between UC1 and UC2 (different prompts, same Claude vision)
3. **Constitutional framework pattern** is the most novel — extensible, data-driven, enforceable
4. **OpenRouter** for production resilience
5. **HITL enforced architecturally** — agent has no write tools to D365

### Production path
- Replace SQLite with D365 OData API calls — same JSON format, just URL + Azure AD OAuth
- Deploy to Azure (same tenant as D365)
- File storage in Azure Blob with the approval record
- LangSmith for production tracing and observability

### What I'd need to learn
- D365 F&O specific OData endpoints and field structures
- Qosina's actual naming convention rules (work with Product Development team)
- Real PO/invoice format distribution (Phase 0 audit)
- The Celigo integration patterns already in production

### Honest assessment
- The AI architecture is what I know cold
- The D365 configuration and domain-specific business rules are where I'd ramp up on the job
- I built this in two weeks. With a few months and team support, I could productionize all three use cases through phased rollouts.

---

## DEMO TIPS

1. **Always upload an actual document.** Don't paste text — Tom needs to see the file upload pipeline working.
2. **Show the model switching at least once.** It's the OpenRouter callback to Round 3.
3. **Open the Original Document tab in at least one review.** Click expand to show the fullscreen viewer.
4. **Edit one low-confidence field manually before approving.** Shows the HITL working.
5. **Don't oversell any single platform.** Recommend Power Platform for UC2 to show maturity.
6. **Acknowledge what you'd need to learn.** Tom values honest assessment over polish.
7. **Time check at every transition.** 25-30 min per use case, hard cap.
