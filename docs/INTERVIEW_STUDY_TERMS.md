# Interview Study Terms

Every term you might hear from Tom or DJ, organized by topic. Read this twice before the call.

---

## Accounts Payable / Finance

**Accounts Payable (AP):** Money Qosina OWES to vendors. "We bought parts from Precision Plastics, now we owe them $5,700."

**Accounts Receivable (AR):** Money customers OWE Qosina. "Acme Medical bought stopcocks, they owe us $2,137.50."

**Three-Way Match:** Comparing three documents before paying a vendor: the Purchase Order (what we ordered), the Receipt (what arrived at the warehouse), and the Invoice (what the vendor is billing). All three must agree before payment.

**Cash Application:** Matching incoming customer payments to open invoices. Hard because customers send checks with no remittance, partial payments, or combined payments covering multiple invoices.

**Remittance Advice:** The note a customer sends saying "this payment is for invoice X and invoice Y." When it's missing, you have a mystery payment.

**Collections:** Chasing customers who haven't paid on time. Prioritized by risk: amount owed, days overdue, payment history, account size.

**DSO (Days Sales Outstanding):** Average number of days it takes to collect payment after a sale. Top finance KPI. Lower = better cash flow. Tom's brief implied this is important to DJ.

**GL (General Ledger):** The master accounting record. When an invoice is approved for payment, it "posts to the GL" — meaning it gets recorded in the books (debit expense, credit AP).

**GL Posting:** Recording a transaction in the general ledger. Your agent never does this — humans approve, then the system posts.

**Write-off:** Forgiving a small variance instead of investigating it. Example: $0.03 rounding difference on an invoice → write it off instead of spending 5 minutes on it.

**Tolerance Threshold:** The dollar amount below which variances get auto-recommended for approval. Your demo: under $0.05 = auto-clear, $0.05-$50 = quick review, over $50 = full investigation.

**Aging Bucket:** How overdue accounts are grouped: 0-30 days, 31-60 days, 61-90 days, 90+ days. Risk increases sharply after 90 days.

**Credit Memo:** A document reducing what a customer owes. Example: MedLine short-paid by $5 for damaged goods → Qosina creates a $5 credit memo.

**Short-Pay:** When a customer pays less than the invoice amount, usually with a reason (damaged goods, freight deduction, early-payment discount).

---

## D365 / Microsoft Ecosystem

**D365 F&O (Finance & Operations):** Microsoft's ERP system. Handles finance, warehouse, supply chain, purchasing. This is where Qosina's transactional data lives — products, invoices, POs, inventory, payments.

**D365 CE (Customer Engagement):** Microsoft's CRM system. Handles sales, customer service, relationships. Separate from F&O but connected. Customer tier, contact history, collection activities live here.

**Dataverse:** Microsoft's low-code data platform that powers D365 CE. Has its own Web API (different from F&O's OData API).

**Dual Write:** Microsoft's built-in sync between F&O and CE. Keeps customer records consistent across both systems. Can be finicky — some companies use Celigo instead.

**OData:** REST API protocol that D365 F&O uses. Every table is a "data entity" at a URL like `/data/CustomersV3`. Your demo returns OData-shaped JSON from SQLite — same field names, same structure, so production swap is URL + auth change.

**Data Entity:** A D365 F&O concept — a read/write API endpoint for a table or view. Examples: `SalesOrderHeaders`, `VendorInvoiceLines`, `ReleasedProductsV2`.

**Entra ID (formerly Azure AD):** Microsoft's identity service. Every Qosina employee has an account. Your production plan uses it for OAuth login + AD group-based authorization.

**AD Groups:** Active Directory groups like "AP_Approver", "CX_Manager". Used for role-based access — who can approve what.

**Power Platform:** Microsoft's low-code suite: Power Automate (workflows), Power Apps (custom apps), Power BI (analytics), Copilot Studio (AI agents).

**Power Automate:** Workflow automation tool. Native D365 connectors, built-in Approvals action via Teams. Your UC2 production recommendation.

**AI Builder:** Microsoft's low-code AI service in Power Platform. Good for structured form extraction, not strong enough for fuzzy matching or constitutional framework.

**Copilot Studio:** Microsoft's no-code agent builder. Good for chatbot-style assistants, not the right runtime for multi-tool ReAct agent loops.

**Celigo iPaaS:** Integration Platform as a Service. Qosina's existing integration backbone connecting D365, CRM, ecommerce, and SaaS tools. In your architecture: trigger layer (inbox watching) + write-back layer (D365 field mappings).

**iPaaS:** Integration Platform as a Service. Cloud middleware for connecting enterprise systems. Celigo is one; others include MuleSoft, Boomi, Workato.

**MCP (Model Context Protocol):** Anthropic's standard for connecting AI to external tools/data. Microsoft released a D365 F&O MCP Server (GA February 2026) — could simplify production integration.

**StockIQ:** Inventory planning/forecasting tool in Qosina's stack. Relevant to UC3 (landed cost calculations use product data).

**DynamicWeb:** Qosina's current ecommerce platform, being migrated to Shopify. Probably out of scope for your UCs but know it exists.

---

## AI / Architecture

**LangGraph:** Framework for building AI agent workflows. Built on LangChain. Your agents use `create_react_agent`.

**ReAct Agent:** Reason → Act → Observe loop. The agent thinks about what to do, calls a tool, observes the result, then decides what to do next. Repeats until done.

**OpenRouter:** API gateway that routes LLM calls to multiple providers. Claude primary, GPT-4o failover, Gemini failover. One API key, one bill.

**HITL (Human in the Loop):** Design pattern where AI proposes, human approves. Your agent's only write tool is `create_approval`. It cannot modify the system of record.

**Constitutional Framework:** UC3's naming-convention rules stored in a database table. "PC plastic" → "Polycarbonate (PC)", "M Luer" → "Male Luer Lock", inches → mm. Rules are data, not code — new rule = INSERT, not a deployment.

**Approval Queue:** The central pattern across all three UCs. Agent creates a recommendation with structured data and confidence scores. Human reviews, edits, approves/rejects. Only after approval does anything write to D365.

**Confidence Score:** 0.0 to 1.0 rating on each extracted field. 95%+ = green (high confidence), 70-94% = yellow (medium), below 70% = red (needs review). Drives the colored borders in the review panel.

**Structured Data:** JSON attached to each approval containing the editable fields with confidence scores. What the review panel renders. Different shape per approval type.

**SSE (Server-Sent Events):** One-way streaming from server to browser. How your chat streams AI responses word-by-word. Lighter than WebSockets for this use case.

**OData-Shaped Responses:** Your tools return JSON that looks like D365 OData responses — with `@odata.context` headers and `value` arrays. Makes the production swap a config change.

**PyMuPDF:** Python library for rendering PDF pages to PNG images. How your demo turns PDFs into images for Claude Vision. No OCR involved.

**LangSmith:** LangChain's tracing/observability platform. Every LLM call and tool call is logged and replayable. Your production plan for agent auditing.

**Fuzzy Matching:** Finding approximate matches when exact matches fail. "1/4 inch silicone tubing" → matches SKU for "Silicone Tubing, 1/4 ID." Your `match_products` tool does this.

---

## Medical Device / Qosina Specific

**ISO 80369-7:** The luer connector standard for intravascular/hypodermic applications. WHY your constitutional framework enforces "Male Luer Lock" not "M Luer." Qosina's catalog is built on these connectors.

**ISO 13485:** Quality management system standard for medical devices. Qosina is certified. When a supplier has this, they meet the same quality standard Qosina does.

**ISO 10993:** Biocompatibility testing standard for medical devices. Parts touching human tissue must pass these tests. CoA test results reference this.

**CE Marking / MDR 2017/745:** European Medical Device Regulation. Required to sell in the EU. Seen on European supplier spec sheets (like EuroFlex).

**FDA Registration:** US manufacturing facility registered with the FDA for medical device production.

**USP Class VI:** Highest US Pharmacopeia biocompatibility rating for plastics used in medical devices. Seen on tubing spec sheets.

**510(k):** FDA premarket submission proving a device is substantially equivalent to a legally marketed one. Most Class II medical devices need this.

**Certificate of Analysis (CoA):** Quality document for a specific manufacturing lot. Contains lot number, test results, expiry dates. NOT a spec sheet — it's quality verification for an existing product, not evaluation of a new one. Your demo creates `quality_document` approvals for these.

**Certificate of Compliance (CoC):** Document certifying supplied goods meet specifications. Qosina provides these with orders. Different from a CoA (which is from the supplier about their manufacturing).

**Lot Number:** Unique ID for a manufacturing batch. Critical for traceability — if a defect is found, the lot number identifies exactly which products are affected.

**Shelf Life:** How long a product maintains its properties. Non-irradiated shelf life (e.g., 60 months) vs post-irradiation shelf life (e.g., 36 months after gamma sterilization).

**Luer Lock:** Threaded medical connector that locks in place. Male Luer Lock = the tapered tip. Female Luer Lock = the receiving end. Spin Lock = variant where the collar rotates freely.

**Luer Slip:** Friction-fit (push-on) medical connector. Less secure than Luer Lock, used where easy disconnect is needed.

**Barbed Connection:** Ridged connector that inserts into tubing. Sized by tubing ID (e.g., "fits 1/4 inch ID tubing").

**Polycarbonate (PC):** Transparent, strong plastic. Most common material for stopcocks and clear connectors.

**Landed Cost:** Total cost of a product delivered to the warehouse: product cost + freight + duties + insurance + handling. UC3 extracts fields (country of origin, tariff code, weight, price) that feed this calculation downstream.

**Item Master:** The central product catalog in D365 F&O. Contains all product attributes — dimensions, materials, pricing, compliance, category. What UC3's product_entry approvals write to after human approval.

**SKU:** Stock Keeping Unit. A unique product identifier. Qosina has 5,000+ active SKUs in their catalog (8,000+ total including discontinued).

---

## Your Demo — How It Works

**The Flow:** User drops a document (or types text) → FastAPI receives it → routes to the right UC agent → agent calls tools in a ReAct loop → creates an approval → human reviews in the side-by-side panel → approves or rejects.

**4 Agents, 20 Read Tools, 1 Write Tool:**

### General Agent (6 read tools)
- `search_products` — search by name, category, material, connection type
- `check_inventory` — stock levels, lot numbers, expiration dates, warehouse location
- `find_compatible_parts` — ISO 80369-7 luer compatibility (what mates with what)
- `check_expiring_inventory` — lots approaching expiry date (FDA traceability)
- `check_low_stock` — parts below reorder point threshold
- `get_customer_order_history` — purchase patterns, volume, revenue per customer

### UC1 Sales Order Agent (5 read tools)
- `match_customer(name, email)` — fuzzy-matches against customer master. Returns ranked matches with confidence scores.
- `match_products(descriptions)` — fuzzy-matches line items against 5,000+ SKU catalog. Uses part number if available (exact = 99%), falls back to description matching (lower confidence).
- `validate_pricing(customer_id, line_items)` — compares PO prices against contracted rates in `customer_pricing` table and catalog prices. Flags mismatches.
- `check_inventory(part_number)` — confirms stock availability per matched product. Returns lot-level detail.
- `get_sample_pos()` — loads demo PO text for testing.

### UC2 AP Processing Agent (5 read tools)
- `get_vendor_invoices()` — lists all pending vendor invoices needing three-way match.
- `three_way_match(invoice_id)` — the core UC2 tool. Pulls invoice lines, finds matching PO and receipt(s), compares line-by-line: ordered qty vs received qty vs invoiced qty, PO price vs invoice price. Returns per-line status (matched / within_tolerance / quantity_discrepancy / price_discrepancy).
- `get_unapplied_payments()` — lists customer payments that haven't been applied to invoices yet.
- `match_payment(payment_id)` — finds the payment, searches open invoices for that customer, proposes allocation. Handles exact match, partial payment, overpayment, unknown customer.
- `score_collections()` — ranks all overdue customers by risk score (amount + days overdue + payment trend + customer tier). Returns prioritized list with reasoning.

### UC3 Product Data Agent (4 read tools)
- `get_naming_conventions()` — loads all 16 constitutional framework rules from the `naming_conventions` table, grouped by field. Returns rule type, pattern, correct/incorrect examples.
- `find_similar_products(category, material, connection_type)` — searches existing catalog for products with similar attributes. Up to 10 matches with full field set. Used for consistency checking.
- `validate_consistency(new_fields)` — programmatic check against constitutional rules. Checks material format (has abbreviation?), connection terminology (ISO case?), dimensions (still in inches?), category (exists in catalog?). Returns errors, warnings, passed checks.
- `get_sample_spec_sheets()` — loads demo spec sheet text for testing.

### The 1 Write Tool (shared by all agents)
- `create_approval(recommendation_type, title, content, structured_data)` — adds a row to the approval queue. This is the ONLY way data gets written. Types: sales_order, invoice_match, payment_application, collection_outreach, product_entry, quality_document.

### 6 Approval Types
| Type | UC | Question it answers | Badge color |
|---|---|---|---|
| `sales_order` | UC1 | Should we create this sales order? | Blue |
| `invoice_match` | UC2 | Should we pay this vendor invoice? | Green |
| `payment_application` | UC2 | Which invoices does this payment cover? | Teal |
| `collection_outreach` | UC2 | Which overdue customer to chase first? | Amber |
| `product_entry` | UC3 | Should we add this product to the catalog? | Purple |
| `quality_document` | UC3 | Is this batch safe to receive and ship? | Rose |

### Database (17 tables)
- **Round 3 base (6):** products, product_compatibility, inventory, customers, order_history, approval_queue
- **UC1 (1):** customer_pricing — contracted rates per customer/product
- **UC2 (9):** vendors, purchase_orders, po_lines, receipts, receipt_lines, vendor_invoices, invoice_lines, customer_invoices, payments
- **UC3 (2):** product_extended (30+ fields per SKU), naming_conventions (constitutional framework rules)

### Production Recommendations Per UC
| UC | Recommendation | Why |
|---|---|---|
| UC1 | n8n + Custom Python | n8n for email triggers (400+ connectors), Python for AI vision + fuzzy matching |
| UC2 | Power Platform + Custom Python | Power Automate for D365 connectors + Teams approvals, Python for AI judgment |
| UC3 | Full Custom Python | Constitutional rules need code precision, low volume doesn't justify orchestration layer |

---

## Qosina Business Context

**Qosina:** Medical device component distributor based in Ronkonkoma, NY. ~$38M revenue, ~120 employees. Sells OEM single-use components (stopcocks, connectors, tubing, filters, clamps).

**Tom Livingston:** Director of Enterprise Applications. Your future boss. Wrote the project brief. Values extensibility and framework thinking.

**DJ Rettman:** EVP/CIO/CTO. Tom's boss. Will catch marketing fluff. Values honest assessment.

**The Brief's Key Phrase:** "We value honest assessment over polished sales pitches."

**Phase 0:** Discovery work before building anything. Team interviews, process shadowing, document audits. Non-negotiable for each phase.

**n8n:** Open-source workflow automation. 400+ connectors. Your UC1 trigger-side recommendation. Pronounced "n-eight-n."

**Celigo:** Pronounced "SELL-ih-go."
