# Qosina Demo Questions — One Per Document

Drop the document, then paste the question.

---

## UC1 — Sales Order Entry (6 docs)

### `po_acme_medical.pdf` — clean PDF, existing customer, all exact matches

```
Walk me through every tool you just called and what each one returned.
```

### `po_bioflow_systems.pdf` — no part numbers, only descriptions

```
No part numbers on this PO. Walk me through how match_products handled the descriptions and what confidence you returned per line.
```

### `po_email_pacific_coast.pdf` — email body, new customer

```
This came in as an email body, not a formal PO. Walk me through your extraction and what match_customer returned for a new customer.
```

### `po_handwritten_clean.png` — handwritten PO (primary demo)

```
How did you read this handwritten document and what was your field-level confidence?
```

### `po_handwritten_summit_surgical.png` — messier handwriting (backup)

```
How did you read this handwritten document and what was your field-level confidence?
```

### `po_wrong_parts_precision_diag.pdf` — bad part numbers, error detection

```
Which line items couldn't be matched? What did match_products return for parts 99999 and XXXXZ?
```

---

## UC2 — AP Processing (7 docs)

### `vendor_invoice_precision_plastics.pdf` — three-way match happy path

```
Walk me through every tool call. Did PO, receipt, and invoice all agree?
```

### `vendor_invoice_techvalve_discrepancy.pdf` — quantity variance (500 billed, 480 received)

```
What qty_variance did three_way_match return and what's the dollar impact?
```

### `vendor_invoice_sinomed_penny.pdf` — $0.03 rounding variance

```
What was the exact amount_variance and which tolerance band did it fall into? Why auto-approve?
```

### `vendor_invoice_allied_price_mismatch.pdf` — unauthorized price increase

```
What price_variance did three_way_match return? Vendor note claims Q2 2026 adjustment — should that override the flag?
```

### `vendor_invoice_unknown_po.pdf` — orphan invoice, no PO on file

```
Why couldn't you complete three-way matching and what's your recommendation?
```

### `payment_remittance_medline.pdf` — partial payment with damage deduction

```
How did you allocate this payment across invoices? Did you create a credit memo approval for the short-pay?
```

### `bank_statement_mystery_payment.pdf` — unknown sender, no remittance

```
Walk me through every match strategy you tried. Best-guess allocation, confidence, and why kick to a human?
```

---

## UC3 — Product Data Entry (5 docs)

### `spec_sheet_stopcock.pdf` — constitutional framework core

```
For each field, show me: supplier value → Qosina value → which rule you applied.
```

### `spec_sheet_filter_euroflex.pdf` — German supplier, metric, EUR, CE-marked

```
German supplier, bilingual, metric units, EUR pricing. What did your pipeline do differently — if anything?
```

### `spec_sheet_tubing_allied.pdf` — imperial fractions

```
Walk me through each imperial-to-metric conversion and show me the math.
```

### `certificate_of_analysis_stopcock.pdf` — CoA, existing product

```
What approval type did you create and why is it different from a spec sheet? List the test results you extracted.
```

### `catalog_page_techvalve.pdf` — 3 products on one page

```
How many separate approvals did you create and why? Walk me through each SKU's extraction.
```
