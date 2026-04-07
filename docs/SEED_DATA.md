# SEED_DATA.md — Database Schema & Seed Data (Round 4)

All product data sourced from qosina.com — real part numbers, materials, specs. Prices, inventory levels, customers, vendors, and invoices are realistic fakes for demo purposes.

## DATABASE SCHEMA — 17 TABLES

### Round 3 Tables (6)

**products** — 29 real Qosina components
```sql
products (item_id PK, product_name, category, description, connection_type, material,
          technical_detail, iso_compliance, manufacturing_environment, shelf_life_months,
          shelf_life_post_irradiation_months, unit_price, minimum_order_qty, status)
```

**product_compatibility** — 27 connection relationships
```sql
product_compatibility (id PK, part_a FK→products, part_b FK→products,
                       compatibility_type, notes)
```

**inventory** — 33 lots with expiration tracking
```sql
inventory (id PK, item_id FK, lot_number, quantity_on_hand, warehouse_location,
           received_date, expiration_date, reorder_point, reorder_quantity)
```

**customers** — 6 OEM customers
```sql
customers (customer_id PK, company_name, contact_name, industry, region, account_tier)
```

**order_history** — purchase patterns over 12+ months
```sql
order_history (order_id PK, customer_id FK, item_id FK, quantity, order_date,
               unit_price, total_price)
```

**approval_queue** — HITL queue with structured editable data
```sql
approval_queue (id PK, recommendation_type, title, content, structured_data,
                source_query, status, ai_generated_at, reviewed_by, reviewed_at)
```

The `structured_data` column stores JSON for the editable review panel form.

### UC1 Table (1)

**customer_pricing** — contracted rates per customer/product
```sql
customer_pricing (id PK, customer_id FK, item_id FK, contracted_price, discount_pct,
                  effective_date, expiry_date)
```

Seeded for premium customers like Acme Medical (10% off stopcocks) and Atlantic Bioprocess (5% off tubing).

### UC2 Tables (9)

**vendors** — 5 vendors Qosina buys from
```sql
vendors (vendor_id PK, vendor_name, contact_name, payment_terms, region)
```

**purchase_orders** + **po_lines** — what Qosina ordered
```sql
purchase_orders (po_number PK, vendor_id FK, order_date, expected_date, status, total_amount)
po_lines (id PK, po_number FK, item_id FK, quantity_ordered, unit_price, line_total)
```

**receipts** + **receipt_lines** — what the warehouse logged
```sql
receipts (receipt_id PK, po_number FK, received_date, received_by)
receipt_lines (id PK, receipt_id FK, item_id FK, quantity_received, lot_number)
```

**vendor_invoices** + **invoice_lines** — what vendors billed
```sql
vendor_invoices (invoice_id PK, vendor_id FK, po_number FK, invoice_date, due_date,
                 total_amount, status, match_status)
invoice_lines (id PK, invoice_id FK, item_id FK, quantity_invoiced, unit_price, line_total)
```

**customer_invoices** — what Qosina billed customers (AR side)
```sql
customer_invoices (invoice_id PK, customer_id FK, invoice_date, due_date,
                   total_amount, amount_paid, status)
```

**payments** — incoming customer payments
```sql
payments (payment_id PK, customer_id FK, payment_date, amount, reference,
          applied_to, status)
```

### UC3 Tables (2)

**product_extended** — 30+ fields per SKU (dimensions, materials, compliance, commercial)
```sql
product_extended (item_id PK FK, inner_diameter_mm, outer_diameter_mm, length_mm,
                  weight_g, color, tolerance, sterilization_compatibility,
                  biocompatibility, country_of_origin, supplier_part_number,
                  tariff_code, units_per_case, lead_time_days, vendor_id)
```

**naming_conventions** — constitutional framework rules
```sql
naming_conventions (id PK, field_name, rule_type, pattern, example_correct,
                    example_incorrect)
```

## SEEDED PRODUCTS — 29 SKUs

Real Qosina parts across 9 categories:

**Stopcocks & Manifolds (4):** 11195, 99720, 99722, 99740
**Valves (3):** 91050 (LOW STOCK), 80071, 80073
**Connectors (8):** 11096, 11097, 11102, 11106, 11455, 65517, 61756, plus T/Y connectors 80126, 84044
**Injection & Sampling Ports (1):** 80147
**Flow Control (2):** 97337 (LOW STOCK), 80330
**Clamps & Clips (3):** 25659, 11498, 14054 (LOW STOCK)
**Tubing (3):** T2004, T4306, T1006 (LOW after CUST-005 orders)
**Filters (2):** 28217 (EXPIRING ~36 days), 28213
**Extension Lines (2):** 33061, 36218

## DEMO SCENARIOS BUILT INTO SEED DATA

### Low Stock (UC General Agent)
- **Part #91050** — 45 units (reorder at 100)
- **Part #97337** — 75 units (reorder at 100)
- **Part #14054** — 45 units (reorder at 100)

### Expiring Inventory
- **Part #11096 LOT-2023-0115** — expires ~20 days
- **Part #28217 LOT-2024-0901** — expires ~36 days
- **Part #25659 LOT-2023-0910** — expires ~35 days

### At-Risk Customers
- **CUST-003 (MedLine)** — declining orders, 2 overdue invoices
- **CUST-006 (Summit Surgical)** — 13 months silent, 1 overdue invoice

### UC1 Customer Pricing
- **CUST-001 (Acme)** — 10% discount on stopcocks (11195, 99720, 99722, 99740, 11455)
- **CUST-005 (Atlantic Bioprocess)** — 5% discount on tubing (T4306, T1006)

### UC2 Three-Way Match Edge Cases
- **VINV-2026-001 (Precision Plastics)** — Perfect match. Auto-approve.
- **VINV-2026-002 (SinoMed)** — $0.03 penny discrepancy from rounding. Within tolerance.
- **VINV-2026-003 (EuroFlex)** — Perfect match.
- **VINV-2026-004 (Allied Silicone)** — Perfect match.
- **VINV-2026-005 (TechValve)** — Billed 500 but only 480 received. **Quantity mismatch**, flag for review.

### UC2 Cash Application Edge Case
- **PAY-2026-006** — $1,345 from CUST-003 (MedLine), no exact invoice match. Customer has $1,012.50 + $337.50 overdue invoices = $1,350 total. The AI should suggest both with a $5 variance (or detect the implied damage deduction from the remittance PDF).

### UC3 Constitutional Framework — 16 Naming Rules

**Materials:** Always "Full Name (ABBREVIATION)"
- Polycarbonate (PC), High-Density Polyethylene (HDPE), Polyvinyl Chloride (PVC), Polypropylene (PP), Silicone

**Connection Types:** ISO 80369-7 terminology, title case
- "Male Luer Lock", "Female Luer Lock", "Male Luer Slip"

**Dimensions:** Always millimeters, format "X.Xmm"
- "2.69mm" not `0.106"`

**Categories:** Qosina taxonomy
- "Stopcocks & Manifolds", "Connectors", "Clamps & Clips"

**Product Types:** Translation rules
- "valve" with luer connections → "Stopcock"
- "fitting" with luer → "Connector"

## SEEDED VENDORS (UC2)

| Vendor ID | Name | Region | Terms |
|-----------|------|--------|-------|
| VEND-001 | Precision Plastics Corp | Domestic | Net 30 |
| VEND-002 | SinoMed Components Ltd | Asia Pacific | Net 60 |
| VEND-003 | EuroFlex Medical GmbH | Europe | Net 30 |
| VEND-004 | Allied Silicone Products | Domestic | Net 45 |
| VEND-005 | TechValve International | Asia Pacific | Net 30 |

## SEEDED CUSTOMERS

| Customer ID | Name | Industry | Tier | Notes |
|-------------|------|----------|------|-------|
| CUST-001 | Acme Medical Devices | Medical Device | Premium | Heavy stopcock buyer, contracted pricing |
| CUST-002 | BioFlow Systems | Biopharma | Premium | Tubing + check valves |
| CUST-003 | MedLine Innovations | Medical Device | Standard | DECLINING — churn risk |
| CUST-004 | Precision Diagnostics | Diagnostics | Standard | Small but steady |
| CUST-005 | Atlantic Bioprocess | Biopharma | Premium | Growing tubing volume |
| CUST-006 | Summit Surgical Supply | Medical Device | Standard | DORMANT — 13 months silent |

## ODATA RESPONSE FORMAT

All tool functions return data formatted as D365 OData JSON. This is intentional — production deployment swaps SQLite for D365 OData API calls, and only the data source changes. The agent, tools, and approval workflow stay identical.

```json
{
  "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#Products",
  "value": [
    {
      "ItemId": "11195",
      "ProductName": "1-Way Stopcock, Female Luer Lock, Male Luer with Spin Lock",
      "Category": "Stopcocks & Manifolds",
      "ConnectionType": "Female Luer Lock, Male Luer Lock",
      "Material": "PC, HDPE, Silicone",
      "ISOCompliance": "ISO 80369-7",
      "UnitPrice": 2.85,
      "Status": "active"
    }
  ]
}
```
