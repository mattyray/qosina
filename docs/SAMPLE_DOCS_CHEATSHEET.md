# Sample Documents Cheat Sheet

Read this 3 times before the interview. After that the docs will feel like yours.

---

## UC1 — Sales Order Entry (6 docs)

### 1. `po_acme_medical.pdf` — THE HAPPY PATH
Clean PDF, existing customer (Acme Medical), real Qosina part numbers (11195, 99720, 11455), prices match contracted rates, all in stock.
- **Demonstrates:** baseline — clean structured PO from a known customer
- **Result:** all-green approval, one-click approve
- **Demo line:** *"This is the boring 80%. AI does it in seconds, human just confirms."*

### 2. `po_bioflow_systems.pdf` — NO PART NUMBERS, FUZZY MATCHING
New customer, **zero part numbers**, just plain-English descriptions ("1/4 inch silicone tubing", "barbed check valve", "hydrophilic filters with luer lock").
- **Demonstrates:** fuzzy product matching against the 5,000-SKU catalog
- **Result:** customer flagged as new, products fuzzy-matched with mixed confidence
- **Demo line:** *"Tom said real POs come without part numbers. Here's the answer."*

### 3. `po_email_pacific_coast.pdf` — EMAIL BODY, NOT A PO
Literally a copy-pasted email from Jennifer Walsh. New customer (Pacific Coast Medical). Mix of vague descriptions ("the swabbable one") and **one explicit part number (11096)**.
- **Demonstrates:** format-agnostic extraction — same pipeline works on unstructured text
- **Result:** processes like a PO even though it's an email
- **Demo line:** *"Doesn't even need to be a PO. Email body works the same way."*

### 4. `po_handwritten_summit_surgical.png` — HANDWRITTEN, MESSY VERSION
Hand-drawn on yellow lined paper, **wobbly** handwriting (random offsets per character — intentionally hard to read), red "RUSH" note, scribbled signature.


- **Demonstrates:** Claude vision on the *worst-case* handwriting
- **Caveat:** This is the messier of the two handwritten ones. May or may not extract cleanly depending on the run.
- **Demo line:** *Backup wow doc — only show if you want maximum drama and you're confident it'll work.*

### 5. `po_handwritten_clean.png` — HANDWRITTEN, NEATER VERSION ⭐
Same Summit Surgical Supply order but with **neater** handwriting (much smaller character offsets). This is the one you should actually demo.
- **Demonstrates:** vision capability on real-world handwriting
- **Result:** extracts part numbers (80330, 97337, 14054, 11498), quantities, RUSH flag
- **Demo line:** *"Customer scrawled this on a notepad and faxed it. Watch."* **← UC1 wow moment**

### 6. `po_wrong_parts_precision_diag.pdf` — ERROR DETECTION
Clean format BUT deliberately broken: part **99999** labeled "DISCONTINUED", part **XXXXZ** is gibberish (letters where digits go), other two parts may or may not exist.
- **Demonstrates:** the AI catches problems instead of trusting input
- **Result:** approval comes out mostly red, flags 2 of 4 line items as unresolvable
- **Demo line:** *"AI as a safety net — flags problems a busy clerk might miss."*

**Recommended live demo set for UC1:** #1 (Acme), #5 (handwritten clean), #6 (wrong parts).
Three docs, escalating from easy → wow → safety.

---

## UC2 — AP Processing (7 docs)

### 1. `vendor_invoice_precision_plastics.pdf` — HAPPY PATH (THREE-WAY MATCH)
Vendor invoice from Precision Plastics for $5,700, references PO-2026-001, line items match the seeded PO/receipt exactly.
- **Demonstrates:** clean three-way match (PO ↔ Receipt ↔ Invoice all agree)
- **Result:** all-green, auto-approve eligible
- **Demo line:** *"Three-way match passes cleanly. AI clears it in seconds."*

### 2. `vendor_invoice_techvalve_discrepancy.pdf` — QUANTITY DISCREPANCY
TechValve invoices for **500 units**, but the receiving dock only logged **480 received** for that PO.
- **Demonstrates:** quantity variance detection in three-way match
- **Result:** medium-confidence approval, flags qty mismatch, asks human to investigate (short ship? damaged?)
- **Demo line:** *"Vendor billed for 500, we only got 480. AI catches it — that's a $79 problem on every invoice this size."*

### 3. `vendor_invoice_sinomed_penny.pdf` — THE $0.03 ROUNDING TEST
SinoMed invoice for $2,250.03 — three cents off from PO due to rounding ($0.4501 × 5,000).
- **Demonstrates:** **tolerance thresholds** — under $0.05 should auto-approve
- **Result:** green, auto-approves because variance is within tolerance
- **Demo line:** *"Three cents. A human shouldn't waste 5 minutes on this. The system has tolerance bands — under $0.05 auto-clears, $0.05–$50 quick review, over $50 full review."*

### 4. `vendor_invoice_allied_price_mismatch.pdf` — PRICE INCREASE
Allied Silicone invoices at **$67.50/coil**, but PO-2026-004 was at **$65.00**. Note on invoice claims "Q2 2026 price adjustment".
- **Demonstrates:** price variance detection (not quantity)
- **Result:** flags ~$250 unauthorized price increase, asks human to approve or push back
- **Demo line:** *"Vendor snuck a 3.8% price increase into the invoice. AI catches it — exactly the kind of leak that adds up over a year."*

### 5. `vendor_invoice_unknown_po.pdf` — ORPHAN INVOICE
MedSupply International invoice references **PO-2025-999** which doesn't exist in the system.
- **Demonstrates:** invoices with no matching PO can't be paid
- **Result:** rejected/flagged for AP investigation — possibly fraud, possibly a real PO never entered
- **Demo line:** *"No PO on file. Could be fraud, could be a legit order someone forgot to enter. Either way, do not pay until resolved."*

### 6. `payment_remittance_medline.pdf` — CASH APPLICATION (PARTIAL)
MedLine sent $1,345 with a remittance advice that says: $1,012.50 → CINV-006, $332.50 → CINV-007 (which is actually $337.50; they deducted $5 for damaged goods).
- **Demonstrates:** cash application with a deduction/short-pay
- **Result:** applies most cleanly but flags the $5 deduction for credit memo creation
- **Demo line:** *"Customer paid two invoices with one check, short-paid one of them by $5 for damaged goods. AI handles the math AND flags the credit memo we owe them."*

### 7. `bank_statement_mystery_payment.pdf` — CASH APPLICATION (NO REMITTANCE) ⭐
First National Bank statement with a $2,800 check from "Unknown" — no remittance advice. Bank flagged it with two possible matches: Acme ($2,137.50) + Atlantic ($650) = $2,787.50 (off by $12.50).
- **Demonstrates:** the hardest cash app problem — **judgment call escalation**
- **Result:** AI proposes the split with low confidence, kicks to human for phone calls
- **Demo line:** *"This is the one that takes AP clerks 30 minutes per occurrence. AI does the lookup, the math, the candidate matching — human just makes the phone call."*

**Recommended live demo set for UC2:** #1 (Precision happy path), #3 (penny rounding) OR #4 (price mismatch), #7 (mystery payment).
Covers happy path, tolerance handling, hard judgment call.

---

## UC3 — Product Data Entry (5 docs)

### 1. `spec_sheet_stopcock.pdf` — THE CONSTITUTIONAL FRAMEWORK CORE ⭐
Precision Plastics spec sheet **deliberately full of wrong terminology**: "PC plastic", "M Luer Lock", "F Luer Lock", inches with mm in parens, "Three-way valve" instead of "3-Way Stopcock".
- **Demonstrates:** the constitutional framework — every wrong term gets normalized
- **Result:** "PC plastic" → "Polycarbonate (PC)", "M Luer Lock" → "Male Luer Lock", inches → mm, etc.
- **Demo line:** *"This is the heart of UC3. Every supplier writes this differently. Watch the rules normalize it into Qosina's catalog format."* **← UC3 wow moment**

### 2. `spec_sheet_filter_euroflex.pdf` — EUROPEAN / METRIC / BILINGUAL
EuroFlex Medical GmbH (Germany), bilingual header ("TECHNISCHES DATENBLATT / TECHNICAL DATA SHEET"), all metric units, EUR pricing, CE/MDR compliance fields.
- **Demonstrates:** international supplier handling — different units, different regulations, different currency
- **Result:** extracts all 30+ fields, flags CE marking + EUR currency for the buyer
- **Demo line:** *"Half of Qosina's suppliers are overseas. The framework handles metric units, currency conversion, EU regulatory fields — same pipeline."*

### 3. `spec_sheet_tubing_allied.pdf` — IMPERIAL UNITS / UNIT CONVERSION
Allied Silicone tubing, all measurements in **fractional imperial** (3/16 inch ID, 5/16 inch OD, 1/16 inch wall).
- **Demonstrates:** unit conversion (inches → mm) per the constitutional rules
- **Result:** extracted as imperial, normalized to metric, both stored
- **Demo line:** *"American suppliers send fractional inches. AI converts to mm so the catalog stays consistent."*

### 4. `certificate_of_analysis_stopcock.pdf` — QUALITY DOCUMENT (CoA)
Not a spec sheet at all — a Certificate of Analysis with **lot numbers, expiry dates, 8 test results (burst pressure, biocompatibility, endotoxin, sterility, etc.)**. Mentions "Qosina equivalent: #11195".
- **Demonstrates:** the framework handles **different document types** — CoAs create a `quality_document` approval (rose/pink badge) instead of a `product_entry` approval. Review panel shows lot tracking fields + a test results table with PASS/FAIL per test.
- **Result:** links quality data to existing Qosina SKU #11195, shows all 8 test results, captures lot/expiry for traceability
- **Demo line:** *"Same pipeline, different document type. CoA routes to quality review with lot tracking and test results — not the product catalog."*
- **Business context:** If there's a defect or recall, you can trace back to this specific lot. FDA/ISO requires this traceability for medical device components.

### 5. `catalog_page_techvalve.pdf` — MULTI-PRODUCT EXTRACTION
TechValve catalog page with **3 different products** on one page (TV-CHK-100, TV-CHK-200, TV-FLO-300).
- **Demonstrates:** extracting *multiple* products from one document
- **Result:** creates 3 separate approval cards, one per product
- **Demo line:** *"One PDF, three new SKUs. AI splits them out and creates an approval per product."*

**Recommended live demo set for UC3:** #1 (constitutional stopcock), #2 (EuroFlex international), #5 (multi-product catalog).
Constitutional framework wow → international handling → multi-extract.

---

## Total recommended live demo: 9 docs across 3 use cases

| UC | Doc | Pitch in one breath |
|---|---|---|
| 1 | Acme | Happy path baseline |
| 1 | Handwritten clean | Vision wow moment |
| 1 | Wrong parts | AI as safety net |
| 2 | Precision Plastics | Three-way match happy path |
| 2 | SinoMed penny **OR** Allied price | Tolerance bands / variance catching |
| 2 | Bank statement mystery | Hard cash app judgment call |
| 3 | Stopcock spec | Constitutional framework wow |
| 3 | EuroFlex | International supplier handling |
| 3 | TechValve catalog | Multi-product extraction |

The other 9 docs (BioFlow, messy handwritten, TechValve discrepancy, MedSupply unknown PO, MedLine remittance, Allied tubing, CoA, etc.) stay in the folder as **"and we also tested these"** — instant follow-ups if Tom asks "what about X?"
