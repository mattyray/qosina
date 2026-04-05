# Qosina Interview: The Complete Study Guide
## Everything You Need to Know, Explained Simply

---

# SECTION 1: THE BIG PICTURE

## What Is an ERP?

ERP stands for Enterprise Resource Planning. It's one giant software system that runs an entire company. Instead of having separate spreadsheets for inventory, separate software for accounting, separate databases for customers — an ERP puts it all in one place. When a sale happens, the inventory updates, the invoice generates, the revenue records, and the shipping triggers — all from one system.

Qosina uses Microsoft Dynamics 365 Finance & Operations (D365 F&O) as their ERP. It's the source of truth for everything: what products they sell, how much inventory they have, who their customers are, what they've ordered, what vendors they owe money to, and what their financials look like.

When people say "system of record" they mean the ERP. It's the one place where the real data lives.

## What Is D365 F&O Specifically?

D365 F&O is Microsoft's ERP for mid-to-large companies. The "F&O" stands for Finance & Operations. It handles:

- **Finance:** General ledger, accounts payable, accounts receivable, budgeting
- **Supply chain:** Purchasing, inventory, warehouse management, production
- **Sales:** Sales orders, customer management, pricing, delivery scheduling

It runs in the cloud on Microsoft Azure. It exposes data through OData APIs (basically REST endpoints that return JSON). That's how external systems read and write data to it.

## What Is D365 CE?

D365 Customer Engagement is the CRM (Customer Relationship Management) side. It tracks the sales pipeline — which potential customers are you talking to, what stage are the deals at, who's the sales rep, what's the follow-up plan. It's separate from F&O but they talk to each other.

## What Is Celigo?

Celigo is their iPaaS — Integration Platform as a Service. Think of it as the plumbing between all their systems. When an order comes in through the website (DynamicWeb), Celigo pushes it into D365. When D365 creates an invoice, Celigo might sync it to their accounting reports. It connects systems that don't natively talk to each other. It's middleware — it sits in the middle.

## What Is OData?

OData is how D365 F&O serves data through its API. It's basically REST + JSON with some extra features. When your Python code needs to read Qosina's product catalog from D365, it makes an HTTP GET request to an OData endpoint and gets back JSON. When it needs to create a sales order, it POSTs JSON to an OData endpoint.

The responses look like this:
```json
{
  "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#SalesOrders",
  "value": [
    {
      "SalesOrderNumber": "SO-001234",
      "CustomerAccount": "ACME-001",
      "TotalAmount": 4500.00
    }
  ]
}
```

In your demos, you're using SQLite but formatting the responses like OData — so in production, you'd just swap the SQLite query for an HTTP call to D365 and the rest of your code stays the same.

---

# SECTION 2: USE CASE 1 — SALES ORDER ENTRY

## The Current Process (What Happens Today)

1. A customer wants to buy parts from Qosina
2. They send a purchase order (PO) to the CX team via email
3. The PO might be a clean PDF, a typed email, a scanned document, or sometimes even handwritten
4. A CX team member opens the email, reads the PO, and manually types all the information into D365 to create a sales order
5. This takes time and is error-prone

## Key Terms

**Purchase Order (PO):** A document from a CUSTOMER saying "I want to buy these things." It's their formal request. It typically contains:
- Who they are (company name, account number)
- What they want (part numbers, descriptions)
- How many of each (quantities)
- What they expect to pay (unit prices)
- Where to ship it (ship-to address)
- When they need it (requested delivery date)
- Their internal reference number (PO number — this is THEIR number, not Qosina's)

**Sales Order:** The record that gets created INSIDE D365 when Qosina accepts a customer's PO. It's Qosina's internal version of "yes, we're going to fulfill this order." A sales order contains:
- Customer account (Qosina's ID for this customer, like ACME-001)
- Line items (each product being ordered — part number, quantity, unit price)
- PO reference (the customer's PO number, for their records)
- Delivery date
- Ship-to address
- Payment terms (Net 30, Net 60 — how many days the customer has to pay)
- Warehouse/Site (which Qosina facility ships it)
- Shipping method
- Possibly: special instructions, lot requirements, compliance notes

**Customer Master Data:** The database of all Qosina's customers in D365. Each customer has an account number, company name, addresses, contacts, payment terms, pricing agreements, order history. When the AI extracts a customer name from a PO, it needs to match it against this master data.

**Product Catalog / Item Master:** The database of all 5,000+ products Qosina sells. Each product has a part number (Item ID), name, description, category, pricing, dimensions, materials, connection types, etc. When the AI extracts "3-way stopcock" from a PO, it needs to match it to the correct Item ID.

**Fuzzy Matching:** When a customer writes "3 way stopcock luer lock" on their PO and the actual product name in D365 is "3-Way Stopcock, Male Luer Lock x Female Luer Lock x Female Luer Lock, Part #11195" — the AI needs to figure out that's what they mean. This isn't an exact text match, it's a fuzzy match. The AI looks at the description, compares it against the catalog, and picks the best match with a confidence score.

**Confidence Score:** A number (usually 0-100% or 0-1.0) that represents how sure the AI is about a match or extraction. "I'm 95% sure they mean Part #11195" vs "I'm 40% sure — this could be any of three parts." High confidence → auto-route. Low confidence → flag for human review.

## What the Automation Does

Instead of a human reading the PO and typing everything in:

1. **Email arrives** → system detects it has a PO attached
2. **Document parsing** → AI reads the document (whether it's a PDF, image, or email text) and extracts the structured data: customer name, part numbers, quantities, prices
3. **Master data matching** → AI matches the extracted customer to the customer master, matches the extracted parts to the product catalog, validates pricing against the customer's contracted rates
4. **Confidence scoring** → each field gets a confidence score
5. **Routing** → high confidence goes to quick approval, low confidence goes to full human review
6. **Human-in-the-loop** → a person reviews what the AI extracted, fixes any errors, and approves
7. **Order creation** → on approval, the sales order is created in D365

## What Makes This Hard

- Documents come in every format. A clean PDF table is easy to parse. A photo of a handwritten form on a napkin is not.
- Part numbers might have typos. Customer names might be abbreviated. Descriptions might be vague.
- Some customers have special pricing agreements — the AI needs to know that ACME gets 10% off on stopcocks.
- Medical device orders have extra compliance requirements (lot tracking, certificates). That's why Tom said start with standard product orders in Phase 1.

---

# SECTION 3: USE CASE 2 — ACCOUNTS PAYABLE PROCESSING

## The Current Process (What Happens Today)

This is about PAYING Qosina's vendors — the companies that supply the parts Qosina buys and resells. The finance team deals with three sub-problems:

### Sub-Problem A: Three-Way Invoice Matching

Here's the story of one purchase:

**Step 1: Qosina orders parts from a vendor.**
The purchasing team creates a Purchase Order (PO) in D365: "We want 500 units of Part X from Vendor ABC at $2.00 each. Total: $1,000."

**Step 2: The parts arrive at the warehouse.**
The warehouse team receives the shipment and creates a Product Receipt in D365: "We received 480 units of Part X from Vendor ABC." (Note: they ordered 500, got 480. This happens all the time — vendor shipped short, some units damaged, etc.)

**Step 3: The vendor sends an invoice.**
Vendor ABC emails an invoice: "Please pay $1,000 for 500 units of Part X."

**Step 4: The finance team needs to match all three.**
This is three-way matching:
- PO said: 500 units × $2.00 = $1,000
- Receipt said: 480 units received
- Invoice said: 500 units × $2.00 = $1,000

Problem: The invoice says 500 but you only got 480. Do you pay $1,000 or $960? This discrepancy needs to be investigated. Someone has to pull up the PO, pull up the receipt, compare them to the invoice, and decide what to do. Multiply this by hundreds of invoices per month.

**Line-item level vs header level matching:**
- **Line-item level:** Compare each product line individually. "Line 1: PO says 500, receipt says 480, invoice says 500 — mismatch on line 1."
- **Header level:** Compare the totals. "PO total: $1,000. Invoice total: $1,000. Receipt total: $960. Mismatch."
- In practice, you usually need both. The header-level check catches big problems fast, the line-item check finds exactly where the discrepancy is.

### Sub-Problem B: Cash Application

This is about INCOMING money — when Qosina's customers pay their invoices.

**The scenario:**
Qosina sent Customer XYZ three invoices:
- Invoice #1001: $5,000 (due March 1)
- Invoice #1002: $3,200 (due March 15)
- Invoice #1003: $1,800 (due April 1)

A payment for $8,200 hits Qosina's bank account from Customer XYZ. The finance team needs to figure out: which invoices does this $8,200 cover?

Simple case: $8,200 = $5,000 + $3,200. They're paying invoices #1001 and #1002. Easy.

Hard case: The payment is $7,995. That's... almost $5,000 + $3,200 = $8,200 but $5 short. Is that a rounding difference? Did they take an early payment discount? Did they short-pay intentionally? Now someone has to investigate.

**Remittance advice:** Some customers send a document with their payment that says "this payment covers Invoice #1001 and Invoice #1002." That makes cash application easy — you just match the numbers. But many customers don't send remittance, so the finance team is staring at a dollar amount and trying to figure out which invoices it applies to.

**Penny discrepancies in more detail:**
These crop up constantly because of rounding in unit prices, currency conversion, tax calculations, and early payment discounts. Example:
- Invoice says $10,472.37
- Payment is $10,472.38 (one cent off)

Nobody cares about one cent. But the system shows invoice #1001 as "not fully paid" because it's off by $0.01. Someone has to manually write off the penny or adjust the record. Do this 200 times a month and it's real labor.

The automation would say: "Discrepancy is $0.01, under the $0.05 tolerance threshold → auto-apply, write off the difference." No human needed.

**Partial payments:**
Customer sends $3,000 but owes $5,000 on Invoice #1001. That's a partial payment. The system needs to record that $3,000 was received against Invoice #1001, and $2,000 is still outstanding. This gets complicated when there are multiple open invoices and the customer doesn't specify which one they're paying against.

### Sub-Problem C: Collections Prioritization

When customers owe Qosina money and haven't paid on time, someone needs to chase them. But you can't call everyone — you have limited time. The question is: who do you call first?

**Accounts Receivable (AR) Aging:** A report showing all money owed to Qosina, grouped by how overdue it is:
- Current (not due yet)
- 1-30 days overdue
- 31-60 days overdue
- 61-90 days overdue
- 90+ days overdue

The AI would analyze payment patterns: "Customer ABC usually pays 10 days late but always pays. Customer DEF has gone from 5 days late to 30 days late to 60 days late over the past year — they're trending toward non-payment. Customer GHI owes $50,000 and is 45 days late — that's a big number, prioritize it."

## Key Terms

**Accounts Payable (AP):** Money Qosina OWES to their vendors. You bought stuff, now you have to pay for it.

**Accounts Receivable (AR):** Money OWED TO Qosina by their customers. You sold stuff, now you're waiting to get paid.

**Purchase Order (PO):** In this context, it's what QOSINA sent to THEIR vendor. (In Use Case 1, the PO is what Qosina's CUSTOMER sent to Qosina. Same document type, opposite direction.)

**Product Receipt / Goods Receipt:** The warehouse's record of what physically arrived. Created when someone at the loading dock counts the boxes and logs them in D365.

**Invoice (vendor invoice):** The bill from the vendor saying "pay me." Contains: vendor name, invoice number, invoice date, due date, line items (product, quantity, unit price), total amount, payment terms.

**Three-Way Match:** Comparing PO (what you ordered) vs Receipt (what you got) vs Invoice (what they're charging). If all three agree: approve. If they don't: investigate.

**Cash Application:** The process of matching incoming payments to open invoices. "This $8,200 payment covers invoices #1001 and #1002."

**Tolerance Threshold:** A rule that says "if the discrepancy is less than $X, don't bother a human — auto-approve." Example: variance under $0.05 → auto-approve. Variance between $0.05 and $50 → flag for quick review. Variance over $50 → full investigation.

**Net 30 / Net 60:** Payment terms. "Net 30" means the customer has 30 days from the invoice date to pay. If the invoice is dated March 1 and terms are Net 30, payment is due by March 31.

**Write-off:** When you decide a small amount isn't worth chasing. "They underpaid by $0.02. Write it off." The system records the $0.02 as a loss and closes the invoice.

**Credit Memo:** A document that reduces what a customer owes. "We overcharged you $200 on the last invoice. Here's a credit memo for $200 that you can apply against your next payment." This complicates cash application because now payments might be offset by credits.

---

# SECTION 4: USE CASE 3 — NEW PRODUCT DATA ENTRY

## The Current Process (What Happens Today)

1. Qosina's Product Development team finds a new part from a supplier they want to add to the catalog
2. The supplier sends documentation: spec sheets, certificates of analysis, catalog pages, technical drawings
3. A person on the Product Development team reads through all these documents and manually extracts 30+ data fields
4. They type all those fields into the D365 item master to create a new product record
5. This takes significant time per SKU, and they're constantly adding new products to a catalog of 8,000+

## Key Terms

**SKU (Stock Keeping Unit):** A unique identifier for each product. Basically, one SKU = one product = one item in the catalog. Qosina has 8,000+ SKUs.

**Item Master:** The central product database in D365 F&O. Every product Qosina sells has a record here. The item master record contains ALL the information about that product — everything from its name to its dimensions to what material it's made of to which ISO standards it complies with. When someone says "enter into the item master," they mean "create a new product record in D365 with all 30+ fields filled in."

**The 30+ Fields (our best guess until Tom confirms):**

Here's what a Qosina product record likely contains, based on their website, their catalog, and standard D365 item master fields:

*Basic identification:*
- Item ID / Part Number (e.g., "11195")
- Product Name (e.g., "3-Way Stopcock, Male Luer Lock x Female Luer Lock x Female Luer Lock")
- Short Description
- Long Description
- Category (e.g., "Stopcocks & Manifolds")
- Sub-category
- Status (active, discontinued, pending)

*Physical specifications:*
- Material (e.g., "Polycarbonate (PC)")
- Color
- Inner Diameter (mm)
- Outer Diameter (mm)
- Length (mm)
- Weight (g)
- Volume
- Tolerance specifications

*Connection/compatibility:*
- Connection Type 1 (e.g., "Male Luer Lock")
- Connection Type 2 (e.g., "Female Luer Lock")
- Connection Type 3 (for multi-port parts)
- ISO 80369-7 compliance (yes/no)
- Compatible part numbers

*Regulatory/compliance:*
- ISO certifications
- Manufacturing environment (e.g., "ISO Class 8 Clean Room")
- Sterilization compatibility (gamma, EtO, autoclave)
- Shelf life (months)
- Shelf life post-irradiation (months)
- Biocompatibility certifications
- Country of origin

*Commercial:*
- Unit price
- Minimum order quantity
- Units per case/bag
- Lead time
- Supplier / Vendor

*Supply chain:*
- Default warehouse
- Reorder point
- Reorder quantity
- Lot tracking enabled (yes/no)
- Serial tracking enabled (yes/no)
- Tariff code (for import/export)
- Weight for shipping

That's probably 30-40 fields. The exact list depends on Qosina's D365 configuration (they may have custom fields beyond the standard ones).

**Spec Sheet:** A document from the supplier describing a product's specifications. Usually a PDF with a mix of text, tables, and diagrams. Might say: "Model XYZ-100, Material: Polycarbonate, ID: 3.2mm, OD: 4.8mm, Length: 52mm, Connection: Female Luer Lock..." The challenge is that every supplier formats these differently.

**Certificate of Analysis (CoA):** A document certifying that a batch of product meets quality specifications. Common in medical device supply chains. It lists test results: dimensions within tolerance, material composition verified, sterility confirmed. It's more about quality assurance than product specs, but it contains data fields the team needs.

**Technical Drawing:** An engineering diagram with dimensions, tolerances, and callouts. Think of a blueprint. These are visual — the data is embedded in the drawing itself, not in text tables. Extracting data from these requires AI that can interpret images, not just read text.

**Catalog Page:** A page from the supplier's product catalog. Usually has multiple products per page, with photos, brief specs, and ordering information. Less detailed than a spec sheet but covers more products.

## The Constitutional Framework

This is the most interesting concept in the whole brief. Here's what it means:

When a supplier sends a spec sheet, they use THEIR terminology. When Qosina enters it into D365, they need to use QOSINA'S terminology. These don't always match.

Supplier says: "3-way valve, luer type connections, PC material"
Qosina's standard: "3-Way Stopcock, Male Luer Lock x Female Luer Lock x Female Luer Lock, Polycarbonate (PC)"

The "constitutional framework" is a set of rules that govern how the AI translates supplier language into Qosina language. It's called "constitutional" because these are non-negotiable rules — the AI must follow them every time, like a constitution. It can't just freestyle.

**Examples of constitutional rules:**
- Product types: "valve" → "Stopcock" (when it has luer connections). "Fitting" → "Connector." "Tube" → "Tubing."
- Materials: Always write the full name with abbreviation: "Polycarbonate (PC)" never just "PC" or "polycarbonate plastic"
- Connections: Use ISO terminology: "Male Luer Lock" never "M Luer" or "male luer lock" (capitalization matters) or "LL"
- Dimensions: Always millimeters. Always format as "X.Xmm"
- Naming pattern: "[Material] [Type], [Connection 1] x [Connection 2] x [Connection 3]"
- Descriptions: Follow the category template. Stopcocks get one format, tubing gets another.

The Product Development team said the AI needs this framework because without it, you'd get inconsistent data. One person enters "PC" another enters "Polycarbonate" another enters "Polycarbonate (PC)." With 8,000+ SKUs, consistency matters — especially when customers search the catalog.

**How you'd implement it:**
The rules go into the AI agent's system prompt AND into validation code. The system prompt tells Claude "when you see this, translate it to that." The validation code checks Claude's output against the rules before it goes to the approval queue. Belt and suspenders — two layers of enforcement.

## What Makes This Hard

- Every supplier formats documents differently. No standard.
- Technical drawings require image interpretation, not just text extraction.
- 30+ fields means a lot of things to get right per product.
- Consistency with 8,000 existing products is critical. You can't have the 48th polycarbonate stopcock use different naming than the first 47.
- The constitutional rules may not be written down anywhere — they might exist only in the heads of the Product Development team. Building the framework means interviewing people and codifying tribal knowledge.

---

# SECTION 5: THE THREE PLATFORMS

## n8n — Visual Workflow Automation

**What it is in one sentence:** An open-source tool where you build automations by connecting visual blocks (nodes) on a canvas — like a flowchart that actually runs.

**Think of it like:** If you could draw a flowchart on a whiteboard and it just... worked. "Email arrives" → "Extract attachment" → "Send to AI" → "Create approval" → "On approve, create record in D365."

**Key things to know:**
- Open source — you can self-host it on your own servers (important for medical device data privacy)
- 400+ pre-built connectors (Gmail, Slack, databases, APIs)
- Has native AI nodes — you can drop in a Claude or GPT node and it handles the API calls
- Supports the AI Agent pattern — a node that reasons, calls tools, and loops until it has an answer
- Supports code nodes — if you need custom JavaScript or Python logic, you drop in a code block
- Workflows export as JSON — you can store them in Git, version control them, review changes
- Recently raised $180M at $2.5B valuation — this isn't a hobby project

**When it's good:** Workflows that are about connecting systems, routing data, triggering actions. When you want non-developers to be able to see and understand what the automation does. When you need to build something fast.

**When it's not great:** When the AI reasoning itself is the complex part. n8n's AI nodes are powerful but less flexible than writing pure Python with LangGraph. If you need very custom tool-calling logic, confidence scoring, or complex multi-step reasoning, you'll outgrow the visual builder.

**D365 connection:** n8n has a native node for D365 Customer Engagement (the CRM). For D365 F&O (the ERP), you use the HTTP Request node with Microsoft OAuth. It works but requires more configuration than a native connector.

## Microsoft Power Platform — The Microsoft Ecosystem Play

**What it is in one sentence:** Microsoft's own low-code/no-code platform for building automations, apps, and AI agents — and it plugs directly into D365 because Microsoft makes both.

**The pieces:**
- **Power Automate:** Build automated workflows (called "flows"). "When a new invoice arrives in D365, check if it matches a PO, if yes approve it, if no flag it."
- **Power Apps:** Build simple business apps without coding. Think custom forms, dashboards, data entry screens that connect to D365.
- **AI Builder:** Microsoft's AI tools — pre-trained models for document processing, OCR, text classification. Can extract data from invoices, receipts, and forms.
- **Copilot Studio:** Build AI chatbots/agents. Like building a conversational assistant that can answer questions about your D365 data.
- **Power BI:** Dashboards and data visualization. (Qosina already uses this.)

**The killer advantage:** Native D365 integration. Power Automate has built-in connectors for D365 F&O and CE. No API configuration, no OAuth setup, no HTTP headers. You just select "D365 Finance & Operations" and pick the table you want. It runs in the same Azure tenant as their D365, so security and authentication are already handled.

**When it's good:** Approval workflows, simple document processing, anything that routes data between D365 and other Microsoft tools. When the finance team or CX team needs to build and manage their own automations. When you want everything in one ecosystem.

**When it's not great:** When you need Claude specifically (Power Platform uses Microsoft's AI models, not Claude — and Qosina standardized on Claude). When the AI logic is complex and needs full flexibility. When you hit licensing costs at scale (AI Builder actions consume "Copilot Credits" and these add up).

## Custom Python — Maximum Power, Maximum Responsibility

**What it is in one sentence:** Build everything from scratch with Python code — you control every aspect but you maintain every aspect.

**Your stack specifically:**
- **FastAPI** for the web server / API endpoints
- **LangGraph** for the AI agent orchestration (ReAct pattern — reason, act, observe, repeat)
- **Claude API** (via OpenRouter) for the LLM calls
- **SQLite** (demo) → D365 OData (production) for data
- **SSE** for streaming responses to the frontend
- **LangSmith** for tracing and debugging AI decisions

**When it's good:** When the AI reasoning is the hard part. Complex document parsing, fuzzy matching, constitutional frameworks, confidence scoring, multi-step analysis. When you need full test coverage. When you need production-grade observability.

**When it's not great:** When the problem is really just about routing data between systems — you don't need custom Python for "when invoice status changes, send a Teams notification." That's a 5-minute Power Automate flow, not a coding project.

---

# SECTION 6: ENTERPRISE CONCEPTS

## Human-in-the-Loop (HITL)

The AI never writes directly to the system of record. It makes recommendations that a human reviews and approves. This is non-negotiable in regulated industries like medical devices.

Why: If the AI creates a wrong sales order, Qosina ships wrong parts that end up in a medical device in someone's body. If the AI pays the wrong invoice amount, the books are wrong. If the AI enters wrong product specs, a customer might order incompatible parts.

How: The AI puts everything in an approval queue. A human looks at it, says yes or no. Only on "yes" does the data get written to D365.

In your demo: the agent has 6 read-only tools (query data) and 1 write tool (create approval queue item). It physically cannot modify the system of record. Enforced in code, not policy.

## Phased Rollout / MVP

Never build everything at once. Build the smallest useful version first, prove it works, then expand.

Phase 0: Understand the problem. Look at real data. Talk to the people doing the work.
Phase 1: Solve the easiest 60-70% of cases. Human reviews 100% but AI pre-fills the data. Measure time savings.
Phase 2: Expand scope. Introduce auto-approval for high-confidence cases. Handle more edge cases.
Phase 3: Full coverage. Harder formats, more automation, wider rollout.

Tom and DJ want to hear you think in phases. "I'd start with just the structured PDFs from known customers in Phase 1" is 10x better than "I'd build a system that handles all formats from day one."

## API Failover / LLM Routing (OpenRouter)

You discussed this with Tom in Round 3. The concept: don't depend on a single AI provider. Route all LLM calls through OpenRouter, which acts as a switchboard. If Claude's API goes down, requests automatically route to GPT-4o. If that's down too, route to Gemini.

Your code doesn't change. The tools don't change. The approval workflow doesn't change. Only the model answering changes — and it's transparent.

This is a production resilience pattern. Enterprise systems can't go down because a third-party API is having a bad day.

---

# SECTION 7: QUICK REFERENCE — TERMS TO MEMORIZE

**AP** = Accounts Payable = money you OWE (paying vendors)
**AR** = Accounts Receivable = money OWED TO YOU (collecting from customers)
**PO** = Purchase Order = "I want to buy these things" (could be from Qosina's customer OR from Qosina to their vendor, depending on context)
**Sales Order** = Qosina's internal record of a customer's order
**Invoice** = a bill saying "pay me this amount"
**Receipt / Goods Receipt / Product Receipt** = warehouse record of what physically showed up
**Three-Way Match** = comparing PO vs Receipt vs Invoice to make sure they agree
**Cash Application** = matching incoming payments to open invoices
**Penny Discrepancy** = tiny rounding differences between expected and actual amounts
**Partial Payment** = customer pays less than the full invoice amount
**Tolerance Threshold** = "if the discrepancy is under $X, auto-approve"
**Write-Off** = recording a small loss to close out a discrepancy
**Credit Memo** = a document reducing what a customer owes
**Net 30/60** = payment terms — days until payment is due
**Item Master** = central product database in D365
**SKU** = one unique product in the catalog
**Spec Sheet** = supplier document describing product specifications
**CoA (Certificate of Analysis)** = document certifying product quality
**Constitutional Framework** = non-negotiable rules for how AI translates supplier data into Qosina's standards
**Fuzzy Matching** = finding the best match when text doesn't exactly match
**Confidence Score** = how sure the AI is about a match/extraction (0-100%)
**OData** = D365's API format (REST + JSON with extra features)
**ERP** = Enterprise Resource Planning = the one system that runs the whole business
**CRM** = Customer Relationship Management = tracks sales pipeline and customer relationships
**iPaaS** = Integration Platform as a Service = middleware that connects systems (Celigo)
**HITL** = Human-in-the-Loop = human reviews AI output before it becomes real
**System of Record** = the one authoritative source of truth (D365 for Qosina)
**MVP** = Minimum Viable Product = the smallest useful version you can build first
**OCR** = Optical Character Recognition = turning images of text into actual text data
**SSE** = Server-Sent Events = streaming data from server to browser in real time
