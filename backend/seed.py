"""Seed the SQLite database with Qosina product data."""

from backend.database import init_db, get_db


def seed():
    """Create tables and populate with demo data."""
    init_db()

    with get_db() as conn:
        # Check if already seeded
        count = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count > 0:
            print(f"Database already seeded ({count} products). Skipping.")
            return

        # --- Products ---
        products = [
            # Stopcocks
            ("11195", "1-Way Stopcock, Female Luer Lock, Male Luer with Spin Lock", "Stopcocks & Manifolds",
             "Single-direction stopcock for fluid path control", "Female Luer Lock, Male Luer Lock",
             "PC, HDPE, Silicone", "0.106 inch Thru Hole (2.69 mm); 29 psi", "ISO 80369-7", 60, 36, 2.85, 100),
            ("99720", "2-Way Stopcock, 2 Female Luer Locks, Male Luer Lock", "Stopcocks & Manifolds",
             "Two-direction stopcock for multi-port fluid control", "Female Luer Lock x2, Male Luer Lock",
             "PC, HDPE", "0.106 inch Thru Hole (2.69 mm); 29 psi", "ISO 80369-7", 60, None, 3.45, 50),
            ("99722", "4-Way Stopcock, 3 Female Luer Locks, Male Luer Lock", "Stopcocks & Manifolds",
             "Four-direction stopcock manifold", "Female Luer Lock x3, Male Luer Lock",
             "PC, HDPE", "0.106 inch Thru Hole (2.69 mm); 29 psi", "ISO 80369-7", 60, None, 5.20, 25),
            ("99740", "1-Way Stopcock, Female Luer Lock, Male Luer Lock", "Stopcocks & Manifolds",
             "High-pressure single-direction stopcock", "Female Luer Lock, Male Luer Lock",
             "PC, COPE", "0.120 inch Thru Hole (3.05 mm); 43.5 psi", "ISO 80369-7", 60, None, 3.10, 100),

            # Check Valves
            ("91050", "High-Flow Check Valve, Barbed", "Valves",
             "One-way valve for barbed tubing connections", "Barbed, fits 1/4 inch ID Tubing",
             "Acrylic, Silicone", "0.075 psi Cracking Pressure", None, None, None, 4.50, 50),
            ("80071", "Check Valve, Female Luer Lock Inlet, Male Luer Lock Outlet", "Valves",
             "One-way check valve with luer lock connections", "Female Luer Lock, Male Luer Lock",
             "PC, Silicone", "0.5 psi Cracking Pressure", "ISO 80369-7", None, None, 3.95, 50),
            ("80073", "Check Valve, Barbed Inlet, Barbed Outlet", "Valves",
             "One-way check valve for barbed tubing", "Barbed, fits 3/16 inch ID Tubing",
             "PC, Silicone", "0.5 psi Cracking Pressure", None, None, None, 3.75, 50),

            # Connectors
            ("11096", "Female Luer Lock, Tubing Port, Clear", "Connectors",
             "Clear female luer lock connector with tubing port", "Female Luer Lock, Tubing Port",
             "PVC", "0.19 inch OD (4.83 mm)", "ISO 80369-7", None, None, 0.45, 500),
            ("11097", "Female Luer Lock, Tubing Port, Blue", "Connectors",
             "Blue female luer lock connector with tubing port", "Female Luer Lock, Tubing Port",
             "PVC", "0.19 inch OD (4.83 mm)", "ISO 80369-7", None, None, 0.48, 500),
            ("11102", "Male Luer Slip, Tubing Port, Clear", "Connectors",
             "Clear male luer slip connector with tubing port", "Male Luer Slip, Tubing Port",
             "PVC", "0.21 inch ID (5.33 mm)", "ISO 80369-7", None, None, 0.42, 500),
            ("11106", "Male Luer Lock, Tubing Port, Clear", "Connectors",
             "Clear male luer lock connector with tubing port", "Male Luer Lock, Tubing Port",
             "PVC", "0.212 inch ID (5.38 mm)", "ISO 80369-7", None, None, 0.50, 500),
            ("11455", "Female Luer Lock to Male Luer Lock Connector, Gamma Stable", "Connectors",
             "Gamma-stable straight connector", "Female Luer Lock, Male Luer Lock",
             "PC", "0.109-0.102 inch ID (2.76-2.59 mm)", "ISO 80369-7", None, None, 1.20, 100),
            ("65517", "Female Luer Lock Connector", "Connectors",
             "Standard female luer lock connector", "Female Luer Lock",
             "PC", "Standard bore", "ISO 80369-7", None, None, 0.85, 100),
            ("61756", "Female Luer Lock to Male Luer Slip Connector, Natural", "Connectors",
             "Luer lock to luer slip adapter", "Female Luer Lock, Male Luer Slip",
             "PP", "Standard bore", "ISO 80369-7", None, None, 0.75, 100),

            # T & Y Connectors
            ("80126", "T Connector, Male Luer with Spin Lock, Two Female Luer Locks", "Connectors",
             "T-shaped connector for splitting fluid paths", "Male Luer Lock, Female Luer Lock x2",
             "PC, COPE", "Standard bore", None, None, None, 4.25, 25),
            ("84044", "Y Connector, Male Luer with Spin Lock, Two Female Luer Lock Ports", "Connectors",
             "Y-shaped connector for splitting fluid paths", "Male Luer Lock, Female Luer Lock x2",
             "MABS, PC", "Standard bore", None, None, None, 4.50, 25),

            # Injection Sites
            ("80147", "Needleless Injection Site, Swabbable, Female Luer Lock, Male Luer Lock",
             "Injection & Sampling Ports",
             "Swabbable needleless injection site", "Female Luer Lock, Male Luer Lock",
             "PC, Silicone, COPE", "Swabbable top", None, None, None, 6.75, 25),

            # Flow Control
            ("97337", "Flow Control Switch, Female Luer Lock Inlet, Male Luer Lock Outlet, Blue", "Flow Control",
             "Rotary flow control switch", "Female Luer Lock, Male Luer Lock",
             "PC, HDPE", "Rotary switch", None, None, None, 5.90, 25),
            ("80330", "Tuohy Borst Adapter FLO 30, Male Luer Lock", "Flow Control",
             "Tuohy borst adapter with side port", "Male Luer Lock",
             "PC, Silicone", "Side port with cap", None, None, None, 8.50, 10),

            # Clamps
            ("25659", "Pinch Clamp, Ratchet-Style, White", "Clamps & Clips",
             "Ratchet-style pinch clamp for tubing", "Fits tubing 3/16-3/8 inch OD",
             "Acetal", "Ratchet mechanism", None, None, None, 0.65, 500),
            ("11498", "Slide Clamp, White", "Clamps & Clips",
             "Slide-style clamp for tubing", "Fits tubing up to 1/4 inch OD",
             "Nylon", "Slide mechanism", None, None, None, 0.35, 500),
            ("14054", "Roller Clamp, White", "Clamps & Clips",
             "Wheel-style roller clamp for precise flow regulation", "Fits tubing 0.150-0.210 inch OD",
             "ABS, Stainless Steel", "Wheel-style flow regulator", None, None, None, 0.95, 100),

            # Tubing
            ("T2004", "Silicone Tubing, 50A Durometer", "Tubing",
             "Platinum-cured silicone tubing, 50 ft coil", "1/32 inch ID x 0.065 inch OD",
             "Silicone", "50 ft coil, platinum-cured", None, None, None, 45.00, 5),
            ("T4306", "PVC Tubing, Clear", "Tubing",
             "Clear PVC tubing, 100 ft coil", "1/4 inch ID x 3/8 inch OD",
             "PVC", "100 ft coil", None, None, None, 32.00, 5),
            ("T1006", "Silicone Tubing, 50A Durometer", "Tubing",
             "Platinum-cured silicone tubing, 50 ft coil", "1/4 inch ID x 3/8 inch OD",
             "Silicone", "50 ft coil, platinum-cured", None, None, None, 65.00, 5),

            # Filters
            ("28217", "Hydrophobic Filter, Female Luer Lock Inlet, Male Luer Slip Outlet", "Filters",
             "PTFE hydrophobic filter, 0.2 micron", "Female Luer Lock, Male Luer Slip",
             "PTFE, ABS", "0.2 micron pore size", "ISO 80369-7", None, None, 3.25, 50),
            ("28213", "Hydrophilic Filter, Female Luer Lock Inlet, Male Luer Lock Outlet", "Filters",
             "PES hydrophilic filter, 0.2 micron", "Female Luer Lock, Male Luer Lock",
             "PES, ABS", "0.2 micron pore size", "ISO 80369-7", None, None, 3.50, 50),

            # Extension Lines
            ("33061", "Extension Line, Female Luer Lock to Male Luer Lock", "Extension Lines",
             "6-inch extension line", "Female Luer Lock, Male Luer Lock",
             "PVC, PC", "6 inch length, 0.050 inch ID", None, None, None, 2.10, 100),
            ("36218", "Extension Line with Slide Clamp", "Extension Lines",
             "12-inch extension line with integrated slide clamp", "Female Luer Lock, Male Luer Lock",
             "PVC, PC", "12 inch length, 0.050 inch ID", None, None, None, 2.85, 50),
        ]

        conn.executemany(
            """INSERT INTO products
               (item_id, product_name, category, description, connection_type,
                material, technical_detail, iso_compliance, shelf_life_months,
                shelf_life_post_irradiation_months, unit_price, minimum_order_qty)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            products
        )

        # --- Compatibility ---
        compatibility = [
            ("11195", "11455", "direct_fit", "Both Female/Male Luer Lock — ISO 80369-7"),
            ("11195", "80147", "direct_fit", "Stopcock Male Luer Lock to Injection Site Female Luer Lock"),
            ("11195", "80071", "direct_fit", "Stopcock to Check Valve via Luer Lock"),
            ("11195", "97337", "direct_fit", "Stopcock to Flow Control Switch via Luer Lock"),
            ("11195", "33061", "direct_fit", "Stopcock to Extension Line via Luer Lock"),
            ("11195", "28213", "direct_fit", "Stopcock to Hydrophilic Filter via Luer Lock"),
            ("80147", "99720", "direct_fit", "Injection Site to 2-Way Stopcock via Luer Lock"),
            ("80147", "99722", "direct_fit", "Injection Site to 4-Way Stopcock via Luer Lock"),
            ("80147", "11455", "direct_fit", "Injection Site to Luer Connector"),
            ("80147", "33061", "direct_fit", "Injection Site to Extension Line via Luer Lock"),
            ("80126", "11195", "direct_fit", "T Connector to Stopcock via Luer Lock"),
            ("80126", "80147", "direct_fit", "T Connector to Injection Site via Luer Lock"),
            ("84044", "11195", "direct_fit", "Y Connector to Stopcock via Luer Lock"),
            ("84044", "80147", "direct_fit", "Y Connector to Injection Site via Luer Lock"),
            ("91050", "T4306", "direct_fit", "Check Valve Barbed fits 1/4 inch ID PVC Tubing"),
            ("91050", "T1006", "direct_fit", "Check Valve Barbed fits 1/4 inch ID Silicone Tubing"),
            ("80073", "T4306", "direct_fit", "Barbed Check Valve fits 3/16-1/4 inch ID Tubing"),
            ("25659", "T4306", "direct_fit", "Pinch Clamp fits 3/16-3/8 inch OD Tubing"),
            ("25659", "T1006", "direct_fit", "Pinch Clamp fits 3/8 inch OD Silicone Tubing"),
            ("14054", "T2004", "direct_fit", "Roller Clamp fits 0.065 inch OD Tubing"),
            ("33061", "28213", "direct_fit", "Extension Line to Filter via Luer Lock"),
            ("33061", "28217", "direct_fit", "Extension Line to Hydrophobic Filter via Luer Lock"),
            ("36218", "28213", "direct_fit", "Extension Line with Clamp to Filter"),
            ("11195", "99740", "same_category_alternative", "Both 1-Way Stopcocks — 99740 has higher pressure rating (43.5 vs 29 psi)"),
            ("99720", "99722", "same_category_alternative", "2-Way vs 4-Way Stopcock — 99722 has additional port"),
            ("T2004", "T1006", "same_category_alternative", "Both Silicone Tubing — different ID/OD sizes"),
            ("28217", "28213", "same_category_alternative", "Hydrophobic vs Hydrophilic — different filter media"),
        ]

        conn.executemany(
            "INSERT INTO product_compatibility (part_a, part_b, compatibility_type, notes) VALUES (?, ?, ?, ?)",
            compatibility
        )

        # --- Inventory ---
        inventory = [
            ("11195", "LOT-2025-0892", 2450, "A-12-3", "2025-01-15", "2030-01-15", 500, 2000),
            ("11195", "LOT-2025-1104", 1200, "A-12-4", "2025-03-20", "2030-03-20", 500, 2000),
            ("99720", "LOT-2024-0445", 890, "A-13-1", "2024-06-10", "2029-06-10", 300, 1000),
            ("99722", "LOT-2025-0201", 340, "A-13-2", "2025-02-01", "2030-02-01", 200, 500),
            ("99740", "LOT-2024-0998", 1560, "A-12-5", "2024-10-05", "2029-10-05", 400, 1500),
            ("91050", "LOT-2024-0667", 45, "B-04-2", "2024-07-12", None, 100, 500),
            ("80071", "LOT-2025-0330", 620, "B-04-3", "2025-03-30", "2030-03-30", 200, 800),
            ("80073", "LOT-2024-0812", 185, "B-04-4", "2024-08-15", None, 100, 400),
            ("11096", "LOT-2023-0115", 3200, "C-01-1", "2023-01-20", "2026-07-20", 1000, 5000),
            ("11096", "LOT-2025-0601", 4800, "C-01-2", "2025-06-01", "2030-06-01", 1000, 5000),
            ("11097", "LOT-2024-0222", 1500, "C-01-3", "2024-02-22", "2027-02-22", 500, 2000),
            ("11102", "LOT-2024-0930", 2100, "C-02-1", "2024-09-30", "2029-09-30", 800, 3000),
            ("11106", "LOT-2025-0115", 1750, "C-02-2", "2025-01-15", "2030-01-15", 600, 2500),
            ("11455", "LOT-2024-0710", 920, "C-03-1", "2024-07-10", "2029-07-10", 300, 1000),
            ("65517", "LOT-2025-0405", 680, "C-03-2", "2025-04-05", "2030-04-05", 200, 800),
            ("61756", "LOT-2024-1201", 1100, "C-03-3", "2024-12-01", "2029-12-01", 400, 1500),
            ("80126", "LOT-2025-0220", 410, "C-04-1", "2025-02-20", "2030-02-20", 150, 500),
            ("84044", "LOT-2024-0815", 290, "C-04-2", "2024-08-15", "2029-08-15", 150, 500),
            ("80147", "LOT-2025-0310", 530, "D-01-1", "2025-03-10", "2030-03-10", 200, 800),
            ("97337", "LOT-2024-0505", 75, "D-02-1", "2024-05-05", "2029-05-05", 100, 400),
            ("80330", "LOT-2025-0128", 220, "D-02-2", "2025-01-28", "2030-01-28", 100, 300),
            ("25659", "LOT-2024-0301", 8500, "E-01-1", "2024-03-01", None, 2000, 10000),
            ("11498", "LOT-2025-0415", 6200, "E-01-2", "2025-04-15", None, 2000, 8000),
            ("14054", "LOT-2024-1105", 45, "E-01-3", "2024-11-05", None, 100, 500),
            ("T2004", "LOT-2025-0201", 85, "F-01-1", "2025-02-01", None, 50, 200),
            ("T4306", "LOT-2024-0620", 120, "F-01-2", "2024-06-20", None, 50, 200),
            ("T1006", "LOT-2025-0315", 62, "F-01-3", "2025-03-15", None, 30, 100),
            ("28217", "LOT-2024-0901", 340, "G-01-1", "2024-09-01", "2026-09-01", 150, 600),
            ("28213", "LOT-2025-0110", 480, "G-01-2", "2025-01-10", "2028-01-10", 150, 600),
            ("33061", "LOT-2024-1020", 1800, "H-01-1", "2024-10-20", "2029-10-20", 500, 2000),
            ("36218", "LOT-2025-0205", 950, "H-01-2", "2025-02-05", "2030-02-05", 300, 1000),
        ]

        conn.executemany(
            """INSERT INTO inventory
               (item_id, lot_number, quantity_on_hand, warehouse_location,
                received_date, expiration_date, reorder_point, reorder_quantity)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            inventory
        )

        # --- Customers ---
        customers = [
            ("CUST-001", "Acme Medical Devices", "Sarah Chen", "medical_device", "Northeast", "premium"),
            ("CUST-002", "BioFlow Systems", "James Rodriguez", "biopharma", "Southeast", "premium"),
            ("CUST-003", "MedLine Innovations", "Patricia Kim", "medical_device", "Midwest", "standard"),
            ("CUST-004", "Precision Diagnostics Inc", "Robert Taylor", "diagnostics", "West Coast", "standard"),
            ("CUST-005", "Atlantic Bioprocess", "Maria Santos", "biopharma", "Northeast", "premium"),
            ("CUST-006", "Summit Surgical Supply", "David Park", "medical_device", "Southeast", "standard"),
        ]

        conn.executemany(
            "INSERT INTO customers VALUES (?, ?, ?, ?, ?, ?)",
            customers
        )

        # --- Order History ---
        orders = [
            ("ORD-2025-0101", "CUST-001", "11195", 500, "2025-01-15", 2.85, 1425.00),
            ("ORD-2025-0201", "CUST-001", "11195", 500, "2025-02-12", 2.85, 1425.00),
            ("ORD-2025-0301", "CUST-001", "11195", 750, "2025-03-10", 2.85, 2137.50),
            ("ORD-2025-0102", "CUST-001", "99720", 200, "2025-01-20", 3.45, 690.00),
            ("ORD-2025-0202", "CUST-001", "99720", 200, "2025-02-18", 3.45, 690.00),
            ("ORD-2025-0103", "CUST-001", "11455", 300, "2025-01-25", 1.20, 360.00),
            ("ORD-2025-0104", "CUST-002", "T1006", 20, "2025-01-10", 65.00, 1300.00),
            ("ORD-2025-0204", "CUST-002", "T1006", 25, "2025-02-14", 65.00, 1625.00),
            ("ORD-2025-0105", "CUST-002", "91050", 100, "2025-01-18", 4.50, 450.00),
            ("ORD-2025-0205", "CUST-002", "28213", 200, "2025-02-20", 3.50, 700.00),
            ("ORD-2025-0305", "CUST-002", "25659", 500, "2025-03-05", 0.65, 325.00),
            ("ORD-2024-0701", "CUST-003", "80147", 300, "2024-07-15", 6.75, 2025.00),
            ("ORD-2024-1001", "CUST-003", "80147", 150, "2024-10-20", 6.75, 1012.50),
            ("ORD-2025-0106", "CUST-003", "80147", 50, "2025-01-10", 6.75, 337.50),
            ("ORD-2025-0107", "CUST-004", "28217", 100, "2025-01-22", 3.25, 325.00),
            ("ORD-2025-0207", "CUST-004", "28213", 100, "2025-02-25", 3.50, 350.00),
            ("ORD-2025-0307", "CUST-004", "33061", 200, "2025-03-15", 2.10, 420.00),
            ("ORD-2025-0108", "CUST-005", "T4306", 50, "2025-01-05", 32.00, 1600.00),
            ("ORD-2025-0208", "CUST-005", "T4306", 50, "2025-02-08", 32.00, 1600.00),
            ("ORD-2025-0308", "CUST-005", "T4306", 75, "2025-03-12", 32.00, 2400.00),
            ("ORD-2025-0109", "CUST-005", "91050", 200, "2025-01-12", 4.50, 900.00),
            ("ORD-2025-0209", "CUST-005", "80073", 150, "2025-02-15", 3.75, 562.50),
            ("ORD-2025-0309", "CUST-005", "25659", 1000, "2025-03-18", 0.65, 650.00),
            ("ORD-2025-0110", "CUST-006", "80330", 50, "2025-01-30", 8.50, 425.00),
            ("ORD-2025-0210", "CUST-006", "97337", 75, "2025-02-28", 5.90, 442.50),
        ]

        conn.executemany(
            "INSERT INTO order_history VALUES (?, ?, ?, ?, ?, ?, ?)",
            orders
        )

    print(f"Seeded database: {len(products)} products, {len(inventory)} inventory lots, "
          f"{len(customers)} customers, {len(orders)} orders, {len(compatibility)} compatibility records.")


if __name__ == "__main__":
    seed()
