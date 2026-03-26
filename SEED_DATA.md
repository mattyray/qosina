# SEED_DATA.md — Qosina Demo Database Seed Data

All product data is sourced from qosina.com. Part numbers, names, materials, and specs are real. Prices, inventory levels, lot numbers, and customers are realistic fakes for demo purposes.

## DATABASE SCHEMA

### products
```sql
CREATE TABLE products (
    item_id TEXT PRIMARY KEY,
    product_name TEXT NOT NULL,
    category TEXT NOT NULL,
    description TEXT,
    connection_type TEXT,
    material TEXT,
    technical_detail TEXT,
    iso_compliance TEXT,
    manufacturing_environment TEXT DEFAULT 'ISO Class 8 / 100,000 / Grade D',
    shelf_life_months INTEGER,
    shelf_life_post_irradiation_months INTEGER,
    unit_price REAL,
    minimum_order_qty INTEGER DEFAULT 1,
    status TEXT DEFAULT 'active'
);
```

### product_compatibility
```sql
CREATE TABLE product_compatibility (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    part_a TEXT NOT NULL REFERENCES products(item_id),
    part_b TEXT NOT NULL REFERENCES products(item_id),
    compatibility_type TEXT NOT NULL,
    notes TEXT
);
```

### inventory
```sql
CREATE TABLE inventory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    item_id TEXT NOT NULL REFERENCES products(item_id),
    lot_number TEXT NOT NULL,
    quantity_on_hand INTEGER NOT NULL,
    warehouse_location TEXT,
    received_date TEXT,
    expiration_date TEXT,
    reorder_point INTEGER DEFAULT 100,
    reorder_quantity INTEGER DEFAULT 500
);
```

### customers
```sql
CREATE TABLE customers (
    customer_id TEXT PRIMARY KEY,
    company_name TEXT NOT NULL,
    contact_name TEXT,
    industry TEXT,
    region TEXT,
    account_tier TEXT DEFAULT 'standard'
);
```

### order_history
```sql
CREATE TABLE order_history (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL REFERENCES customers(customer_id),
    item_id TEXT NOT NULL REFERENCES products(item_id),
    quantity INTEGER NOT NULL,
    order_date TEXT NOT NULL,
    unit_price REAL,
    total_price REAL
);
```

### approval_queue
```sql
CREATE TABLE approval_queue (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recommendation_type TEXT NOT NULL,
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    source_query TEXT,
    status TEXT DEFAULT 'pending',
    ai_generated_at TEXT NOT NULL,
    reviewed_by TEXT,
    reviewed_at TEXT
);
```

---

## PRODUCTS TO SEED

### Stopcocks (category: "Stopcocks & Manifolds")

| item_id | product_name | connection_type | material | technical_detail | iso_compliance | shelf_life | price |
|---------|-------------|-----------------|----------|-----------------|----------------|------------|-------|
| 11195 | 1-Way Stopcock, Female Luer Lock, Male Luer with Spin Lock | Female Luer Lock, Male Luer Lock | PC, HDPE, Silicone | 0.106 inch Thru Hole (2.69 mm); 29 psi | ISO 80369-7 | 60 (36 post-irrad) | 2.85 |
| 99720 | 2-Way Stopcock, 2 Female Luer Locks, Male Luer Lock | Female Luer Lock x2, Male Luer Lock | PC, HDPE | 0.106 inch Thru Hole (2.69 mm); 29 psi | ISO 80369-7 | 60 | 3.45 |
| 99722 | 4-Way Stopcock, 3 Female Luer Locks, Male Luer Lock | Female Luer Lock x3, Male Luer Lock | PC, HDPE | 0.106 inch Thru Hole (2.69 mm); 29 psi | ISO 80369-7 | 60 | 5.20 |
| 99740 | 1-Way Stopcock, Female Luer Lock, Male Luer Lock | Female Luer Lock, Male Luer Lock | PC, COPE | 0.120 inch Thru Hole (3.05 mm); 43.5 psi | ISO 80369-7 | 60 | 3.10 |

### Check Valves (category: "Valves")

| item_id | product_name | connection_type | material | technical_detail | iso_compliance | price |
|---------|-------------|-----------------|----------|-----------------|----------------|-------|
| 91050 | High-Flow Check Valve, Barbed | Barbed, fits 1/4 inch ID Tubing | Acrylic, Silicone | 0.075 psi Cracking Pressure | None | 4.50 |
| 80071 | Check Valve, Female Luer Lock Inlet, Male Luer Lock Outlet | Female Luer Lock, Male Luer Lock | PC, Silicone | 0.5 psi Cracking Pressure | ISO 80369-7 | 3.95 |
| 80073 | Check Valve, Barbed Inlet, Barbed Outlet | Barbed, fits 3/16 inch ID Tubing | PC, Silicone | 0.5 psi Cracking Pressure | None | 3.75 |

### Connectors — Luers (category: "Connectors")

| item_id | product_name | connection_type | material | technical_detail | iso_compliance | price |
|---------|-------------|-----------------|----------|-----------------|----------------|-------|
| 11096 | Female Luer Lock, Tubing Port, Clear | Female Luer Lock, Tubing Port | PVC | 0.19 inch OD (4.83 mm) | ISO 80369-7 | 0.45 |
| 11097 | Female Luer Lock, Tubing Port, Blue | Female Luer Lock, Tubing Port | PVC | 0.19 inch OD (4.83 mm) | ISO 80369-7 | 0.48 |
| 11102 | Male Luer Slip, Tubing Port, Clear | Male Luer Slip, Tubing Port | PVC | 0.21 inch ID (5.33 mm) | ISO 80369-7 | 0.42 |
| 11106 | Male Luer Lock, Tubing Port, Clear | Male Luer Lock, Tubing Port | PVC | 0.212 inch ID (5.38 mm) | ISO 80369-7 | 0.50 |
| 11455 | Female Luer Lock to Male Luer Lock Connector, Gamma Stable | Female Luer Lock, Male Luer Lock | PC | 0.109-0.102 inch ID (2.76-2.59 mm) | ISO 80369-7 | 1.20 |
| 65517 | Female Luer Lock Connector | Female Luer Lock | PC | Standard bore | ISO 80369-7 | 0.85 |
| 61756 | Female Luer Lock to Male Luer Slip Connector, Natural | Female Luer Lock, Male Luer Slip | PP | Standard bore | ISO 80369-7 | 0.75 |

### T & Y Connectors (category: "Connectors")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| 80126 | T Connector, Male Luer with Spin Lock, Two Female Luer Locks | Male Luer Lock, Female Luer Lock x2 | PC, COPE | Standard bore | 4.25 |
| 84044 | Y Connector, Male Luer with Spin Lock, Two Female Luer Lock Ports | Male Luer Lock, Female Luer Lock x2 | MABS, PC | Standard bore | 4.50 |

### Injection & Sampling Ports (category: "Injection & Sampling Ports")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| 80147 | Needleless Injection Site, Swabbable, Female Luer Lock, Male Luer Lock | Female Luer Lock, Male Luer Lock | PC, Silicone, COPE | Swabbable top | 6.75 |

### Flow Control (category: "Flow Control")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| 97337 | Flow Control Switch, Female Luer Lock Inlet, Male Luer Lock Outlet, Blue | Female Luer Lock, Male Luer Lock | PC, HDPE | Rotary switch | 5.90 |
| 80330 | Tuohy Borst Adapter FLO 30, Male Luer Lock | Male Luer Lock | PC, Silicone | Side port with cap | 8.50 |

### Clamps & Clips (category: "Clamps & Clips")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| 25659 | Pinch Clamp, Ratchet-Style, White | Fits tubing 3/16-3/8 inch OD | Acetal | Ratchet mechanism | 0.65 |
| 11498 | Slide Clamp, White | Fits tubing up to 1/4 inch OD | Nylon | Slide mechanism | 0.35 |
| 14054 | Roller Clamp, White | Fits tubing 0.150-0.210 inch OD | ABS, Stainless Steel | Wheel-style flow regulator | 0.95 |

### Tubing (category: "Tubing")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| T2004 | Silicone Tubing, 50A Durometer | 1/32 inch ID x 0.065 inch OD | Silicone | 50 ft coil, platinum-cured | 45.00 |
| T4306 | PVC Tubing, Clear | 1/4 inch ID x 3/8 inch OD | PVC | 100 ft coil | 32.00 |
| T1006 | Silicone Tubing, 50A Durometer | 1/4 inch ID x 3/8 inch OD | Silicone | 50 ft coil, platinum-cured | 65.00 |

### Filters (category: "Filters")

| item_id | product_name | connection_type | material | technical_detail | iso_compliance | price |
|---------|-------------|-----------------|----------|-----------------|----------------|-------|
| 28217 | Hydrophobic Filter, Female Luer Lock Inlet, Male Luer Slip Outlet | Female Luer Lock, Male Luer Slip | PTFE, ABS | 0.2 micron pore size | ISO 80369-7 | 3.25 |
| 28213 | Hydrophilic Filter, Female Luer Lock Inlet, Male Luer Lock Outlet | Female Luer Lock, Male Luer Lock | PES, ABS | 0.2 micron pore size | ISO 80369-7 | 3.50 |

### Extension Lines (category: "Extension Lines")

| item_id | product_name | connection_type | material | technical_detail | price |
|---------|-------------|-----------------|----------|-----------------|-------|
| 33061 | Extension Line, Female Luer Lock to Male Luer Lock | Female Luer Lock, Male Luer Lock | PVC, PC | 6 inch length, 0.050 inch ID | 2.10 |
| 36218 | Extension Line with Slide Clamp | Female Luer Lock, Male Luer Lock | PVC, PC | 12 inch length, 0.050 inch ID | 2.85 |

---

## COMPATIBILITY MAP

Compatibility is based on connection types. Parts with matching luer connections are compatible. Barbed parts fit specific tubing sizes.

### Luer Lock Compatibility (all ISO 80369-7 compliant luers connect to each other)

```
# Stopcocks connect to luer connectors, filters, injection sites, flow control, extension lines
(11195, 11455, "direct_fit", "Both Female/Male Luer Lock — ISO 80369-7")
(11195, 80147, "direct_fit", "Stopcock Male Luer Lock to Injection Site Female Luer Lock")
(11195, 80071, "direct_fit", "Stopcock to Check Valve via Luer Lock")
(11195, 97337, "direct_fit", "Stopcock to Flow Control Switch via Luer Lock")
(11195, 33061, "direct_fit", "Stopcock to Extension Line via Luer Lock")
(11195, 28213, "direct_fit", "Stopcock to Hydrophilic Filter via Luer Lock")

# 80147 Injection Site connects to stopcocks, connectors, extension lines
(80147, 99720, "direct_fit", "Injection Site to 2-Way Stopcock via Luer Lock")
(80147, 99722, "direct_fit", "Injection Site to 4-Way Stopcock via Luer Lock")
(80147, 11455, "direct_fit", "Injection Site to Luer Connector")
(80147, 33061, "direct_fit", "Injection Site to Extension Line via Luer Lock")

# T/Y Connectors to stopcocks and injection sites
(80126, 11195, "direct_fit", "T Connector to Stopcock via Luer Lock")
(80126, 80147, "direct_fit", "T Connector to Injection Site via Luer Lock")
(84044, 11195, "direct_fit", "Y Connector to Stopcock via Luer Lock")
(84044, 80147, "direct_fit", "Y Connector to Injection Site via Luer Lock")

# Barbed connections — check valve to tubing
(91050, T4306, "direct_fit", "Check Valve Barbed fits 1/4 inch ID PVC Tubing")
(91050, T1006, "direct_fit", "Check Valve Barbed fits 1/4 inch ID Silicone Tubing")
(80073, T4306, "direct_fit", "Barbed Check Valve fits 3/16-1/4 inch ID Tubing")

# Clamps to tubing
(25659, T4306, "direct_fit", "Pinch Clamp fits 3/16-3/8 inch OD Tubing")
(25659, T1006, "direct_fit", "Pinch Clamp fits 3/8 inch OD Silicone Tubing")
(14054, T2004, "direct_fit", "Roller Clamp fits 0.065 inch OD Tubing")

# Extension lines to filters
(33061, 28213, "direct_fit", "Extension Line to Filter via Luer Lock")
(33061, 28217, "direct_fit", "Extension Line to Hydrophobic Filter via Luer Lock")
(36218, 28213, "direct_fit", "Extension Line with Clamp to Filter")

# Same-category alternatives
(11195, 99740, "same_category_alternative", "Both 1-Way Stopcocks — 99740 has higher pressure rating (43.5 vs 29 psi)")
(99720, 99722, "same_category_alternative", "2-Way vs 4-Way Stopcock — 99722 has additional port")
(T2004, T1006, "same_category_alternative", "Both Silicone Tubing — different ID/OD sizes")
(28217, 28213, "same_category_alternative", "Hydrophobic vs Hydrophilic — different filter media")
```

---

## INVENTORY TO SEED

Format: (item_id, lot_number, quantity_on_hand, warehouse_location, received_date, expiration_date, reorder_point, reorder_quantity)

```python
inventory_data = [
    # Stopcocks — healthy stock
    ("11195", "LOT-2025-0892", 2450, "A-12-3", "2025-01-15", "2030-01-15", 500, 2000),
    ("11195", "LOT-2025-1104", 1200, "A-12-4", "2025-03-20", "2030-03-20", 500, 2000),
    ("99720", "LOT-2024-0445", 890, "A-13-1", "2024-06-10", "2029-06-10", 300, 1000),
    ("99722", "LOT-2025-0201", 340, "A-13-2", "2025-02-01", "2030-02-01", 200, 500),
    ("99740", "LOT-2024-0998", 1560, "A-12-5", "2024-10-05", "2029-10-05", 400, 1500),

    # Check Valves — one is LOW STOCK (demo scenario)
    ("91050", "LOT-2024-0667", 45, "B-04-2", "2024-07-12", None, 100, 500),  # BELOW REORDER POINT
    ("80071", "LOT-2025-0330", 620, "B-04-3", "2025-03-30", "2030-03-30", 200, 800),
    ("80073", "LOT-2024-0812", 185, "B-04-4", "2024-08-15", None, 100, 400),

    # Connectors — high volume, some EXPIRING SOON (demo scenario)
    ("11096", "LOT-2023-0115", 3200, "C-01-1", "2023-01-20", "2026-07-20", 1000, 5000),  # EXPIRES IN ~4 MONTHS
    ("11096", "LOT-2025-0601", 4800, "C-01-2", "2025-06-01", "2030-06-01", 1000, 5000),
    ("11097", "LOT-2024-0222", 1500, "C-01-3", "2024-02-22", "2027-02-22", 500, 2000),
    ("11102", "LOT-2024-0930", 2100, "C-02-1", "2024-09-30", "2029-09-30", 800, 3000),
    ("11106", "LOT-2025-0115", 1750, "C-02-2", "2025-01-15", "2030-01-15", 600, 2500),
    ("11455", "LOT-2024-0710", 920, "C-03-1", "2024-07-10", "2029-07-10", 300, 1000),
    ("65517", "LOT-2025-0405", 680, "C-03-2", "2025-04-05", "2030-04-05", 200, 800),
    ("61756", "LOT-2024-1201", 1100, "C-03-3", "2024-12-01", "2029-12-01", 400, 1500),

    # T/Y Connectors
    ("80126", "LOT-2025-0220", 410, "C-04-1", "2025-02-20", "2030-02-20", 150, 500),
    ("84044", "LOT-2024-0815", 290, "C-04-2", "2024-08-15", "2029-08-15", 150, 500),

    # Injection Sites
    ("80147", "LOT-2025-0310", 530, "D-01-1", "2025-03-10", "2030-03-10", 200, 800),

    # Flow Control
    ("97337", "LOT-2024-0505", 75, "D-02-1", "2024-05-05", "2029-05-05", 100, 400),  # BELOW REORDER POINT
    ("80330", "LOT-2025-0128", 220, "D-02-2", "2025-01-28", "2030-01-28", 100, 300),

    # Clamps — one LOW STOCK
    ("25659", "LOT-2024-0301", 8500, "E-01-1", "2024-03-01", None, 2000, 10000),
    ("11498", "LOT-2025-0415", 6200, "E-01-2", "2025-04-15", None, 2000, 8000),
    ("14054", "LOT-2024-1105", 45, "E-01-3", "2024-11-05", None, 100, 500),  # BELOW REORDER POINT

    # Tubing
    ("T2004", "LOT-2025-0201", 85, "F-01-1", "2025-02-01", None, 50, 200),
    ("T4306", "LOT-2024-0620", 120, "F-01-2", "2024-06-20", None, 50, 200),
    ("T1006", "LOT-2025-0315", 62, "F-01-3", "2025-03-15", None, 30, 100),

    # Filters
    ("28217", "LOT-2024-0901", 340, "G-01-1", "2024-09-01", "2026-09-01", 150, 600),
    ("28213", "LOT-2025-0110", 480, "G-01-2", "2025-01-10", "2028-01-10", 150, 600),

    # Extension Lines
    ("33061", "LOT-2024-1020", 1800, "H-01-1", "2024-10-20", "2029-10-20", 500, 2000),
    ("36218", "LOT-2025-0205", 950, "H-01-2", "2025-02-05", "2030-02-05", 300, 1000),
]
```

**Low stock items (for demo):** 91050 (45 on hand, reorder at 100), 97337 (75 on hand, reorder at 100), 14054 (45 on hand, reorder at 100)

**Expiring soon (for demo):** 11096 LOT-2023-0115 (expires 2026-07-20 — ~4 months from interview date of March 2026)

---

## CUSTOMERS TO SEED

```python
customers_data = [
    ("CUST-001", "Acme Medical Devices", "Sarah Chen", "medical_device", "Northeast", "premium"),
    ("CUST-002", "BioFlow Systems", "James Rodriguez", "biopharma", "Southeast", "premium"),
    ("CUST-003", "MedLine Innovations", "Patricia Kim", "medical_device", "Midwest", "standard"),
    ("CUST-004", "Precision Diagnostics Inc", "Robert Taylor", "diagnostics", "West Coast", "standard"),
    ("CUST-005", "Atlantic Bioprocess", "Maria Santos", "biopharma", "Northeast", "premium"),
    ("CUST-006", "Summit Surgical Supply", "David Park", "medical_device", "Southeast", "standard"),
]
```

---

## ORDER HISTORY TO SEED

Design these to create interesting patterns the agent can identify:

```python
order_history_data = [
    # CUST-001 (Acme Medical) — Regular stopcock buyer, NEVER orders compatible tubing (cross-sell opportunity)
    ("ORD-2025-0101", "CUST-001", "11195", 500, "2025-01-15", 2.85, 1425.00),
    ("ORD-2025-0201", "CUST-001", "11195", 500, "2025-02-12", 2.85, 1425.00),
    ("ORD-2025-0301", "CUST-001", "11195", 750, "2025-03-10", 2.85, 2137.50),
    ("ORD-2025-0102", "CUST-001", "99720", 200, "2025-01-20", 3.45, 690.00),
    ("ORD-2025-0202", "CUST-001", "99720", 200, "2025-02-18", 3.45, 690.00),
    ("ORD-2025-0103", "CUST-001", "11455", 300, "2025-01-25", 1.20, 360.00),

    # CUST-002 (BioFlow) — Heavy bioprocess buyer, orders tubing + connectors + filters
    ("ORD-2025-0104", "CUST-002", "T1006", 20, "2025-01-10", 65.00, 1300.00),
    ("ORD-2025-0204", "CUST-002", "T1006", 25, "2025-02-14", 65.00, 1625.00),
    ("ORD-2025-0105", "CUST-002", "91050", 100, "2025-01-18", 4.50, 450.00),
    ("ORD-2025-0205", "CUST-002", "28213", 200, "2025-02-20", 3.50, 700.00),
    ("ORD-2025-0305", "CUST-002", "25659", 500, "2025-03-05", 0.65, 325.00),

    # CUST-003 (MedLine) — Declining orders (churn risk)
    ("ORD-2024-0701", "CUST-003", "80147", 300, "2024-07-15", 6.75, 2025.00),
    ("ORD-2024-1001", "CUST-003", "80147", 150, "2024-10-20", 6.75, 1012.50),
    ("ORD-2025-0106", "CUST-003", "80147", 50, "2025-01-10", 6.75, 337.50),
    # No orders since January — declining pattern

    # CUST-004 (Precision Diagnostics) — Small but steady
    ("ORD-2025-0107", "CUST-004", "28217", 100, "2025-01-22", 3.25, 325.00),
    ("ORD-2025-0207", "CUST-004", "28213", 100, "2025-02-25", 3.50, 350.00),
    ("ORD-2025-0307", "CUST-004", "33061", 200, "2025-03-15", 2.10, 420.00),

    # CUST-005 (Atlantic Bioprocess) — Large volume, regular
    ("ORD-2025-0108", "CUST-005", "T4306", 50, "2025-01-05", 32.00, 1600.00),
    ("ORD-2025-0208", "CUST-005", "T4306", 50, "2025-02-08", 32.00, 1600.00),
    ("ORD-2025-0308", "CUST-005", "T4306", 75, "2025-03-12", 32.00, 2400.00),
    ("ORD-2025-0109", "CUST-005", "91050", 200, "2025-01-12", 4.50, 900.00),
    ("ORD-2025-0209", "CUST-005", "80073", 150, "2025-02-15", 3.75, 562.50),
    ("ORD-2025-0309", "CUST-005", "25659", 1000, "2025-03-18", 0.65, 650.00),

    # CUST-006 (Summit Surgical) — Occasional buyer
    ("ORD-2025-0110", "CUST-006", "80330", 50, "2025-01-30", 8.50, 425.00),
    ("ORD-2025-0210", "CUST-006", "97337", 75, "2025-02-28", 5.90, 442.50),
]
```

**Interesting patterns for the agent to identify:**
- **CUST-001** buys stopcocks and connectors monthly but never orders tubing → cross-sell opportunity
- **CUST-003** orders are declining (300 → 150 → 50 → none since January) → churn risk
- **CUST-005** is increasing order volume (50 → 50 → 75 tubing) → growing account, upsell opportunity
- **CUST-002** buys check valves (91050) which are now low stock → proactive notification

---

## ODATA RESPONSE FORMAT

Tool functions should return data formatted like D365 OData responses. Example:

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
            "TechnicalDetail": "0.106 inch Thru Hole (2.69 mm); 29 psi",
            "ISOCompliance": "ISO 80369-7",
            "ManufacturingEnvironment": "ISO Class 8 / 100,000 / Grade D",
            "ShelfLifeMonths": 60,
            "UnitPrice": 2.85,
            "Status": "active"
        }
    ]
}
```

Inventory OData format:
```json
{
    "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#InventoryOnHand",
    "value": [
        {
            "ItemId": "11195",
            "LotNumber": "LOT-2025-0892",
            "QuantityOnHand": 2450,
            "WarehouseLocation": "A-12-3",
            "ReceivedDate": "2025-01-15",
            "ExpirationDate": "2030-01-15",
            "ReorderPoint": 500,
            "ReorderQuantity": 2000
        }
    ]
}
```
