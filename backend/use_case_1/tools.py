"""Pure tool functions for UC1: Sales Order Entry. No LangGraph dependency."""

from backend.database import get_db


def match_customer(name: str = "", email: str = "", po_reference: str = "") -> dict:
    """Fuzzy match a customer name/email against the customer master."""
    with get_db() as conn:
        conditions = []
        params = []

        if name:
            conditions.append("(c.company_name LIKE ? OR c.contact_name LIKE ?)")
            params.extend([f"%{name}%", f"%{name}%"])
        if email:
            conditions.append("c.company_name LIKE ?")
            params.append(f"%{email.split('@')[0]}%")
        if po_reference:
            conditions.append("""EXISTS (
                SELECT 1 FROM order_history o
                WHERE o.customer_id = c.customer_id
            )""")

        where = " OR ".join(conditions) if conditions else "1=1"

        rows = conn.execute(f"""
            SELECT c.*,
                   COUNT(o.order_id) as total_orders,
                   COALESCE(SUM(o.total_price), 0) as total_revenue,
                   MAX(o.order_date) as last_order_date
            FROM customers c
            LEFT JOIN order_history o ON c.customer_id = o.customer_id
            WHERE {where}
            GROUP BY c.customer_id
            ORDER BY total_revenue DESC
        """, params).fetchall()

    matches = []
    for r in rows:
        # Simple confidence scoring based on match quality
        confidence = 0.5
        if name:
            if name.lower() in r["company_name"].lower():
                confidence = 0.95 if name.lower() == r["company_name"].lower() else 0.85
            elif name.lower() in (r["contact_name"] or "").lower():
                confidence = 0.75
        matches.append({
            "CustomerId": r["customer_id"],
            "CompanyName": r["company_name"],
            "ContactName": r["contact_name"],
            "Industry": r["industry"],
            "Region": r["region"],
            "AccountTier": r["account_tier"],
            "TotalOrders": r["total_orders"],
            "TotalRevenue": r["total_revenue"],
            "LastOrderDate": r["last_order_date"],
            "ConfidenceScore": confidence,
        })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#CustomerMatch",
        "SearchTerms": {"Name": name, "Email": email, "POReference": po_reference},
        "value": matches,
        "BestMatch": matches[0] if matches else None,
    }


def match_products(descriptions: list[dict]) -> dict:
    """
    Fuzzy match product descriptions/part numbers against the catalog.
    Input: list of dicts with keys like 'description', 'part_number', 'quantity'.
    """
    results = []

    with get_db() as conn:
        for item in descriptions:
            desc = item.get("description", "")
            part_num = item.get("part_number", "")
            quantity = item.get("quantity", 0)
            unit_price = item.get("unit_price", None)

            matches = []

            # Try exact part number match first
            if part_num:
                row = conn.execute(
                    "SELECT * FROM products WHERE item_id = ?", (part_num,)
                ).fetchone()
                if row:
                    matches.append({"product": dict(row), "confidence": 0.99, "match_type": "exact_part_number"})

            # Fuzzy search by description
            if desc and not matches:
                like = f"%{desc}%"
                rows = conn.execute("""
                    SELECT * FROM products
                    WHERE product_name LIKE ? OR category LIKE ?
                    OR material LIKE ? OR connection_type LIKE ?
                    OR description LIKE ?
                """, (like, like, like, like, like)).fetchall()

                for r in rows:
                    # Score based on how many search terms appear in the product name
                    terms = desc.lower().split()
                    name_lower = r["product_name"].lower()
                    term_hits = sum(1 for t in terms if t in name_lower)
                    confidence = min(0.95, 0.5 + (term_hits / max(len(terms), 1)) * 0.45)
                    matches.append({"product": dict(r), "confidence": confidence, "match_type": "fuzzy_description"})

                matches.sort(key=lambda m: m["confidence"], reverse=True)
                matches = matches[:3]  # Top 3

            best = matches[0] if matches else None
            results.append({
                "InputDescription": desc,
                "InputPartNumber": part_num,
                "RequestedQuantity": quantity,
                "RequestedUnitPrice": unit_price,
                "Matches": [
                    {
                        "ItemId": m["product"]["item_id"],
                        "ProductName": m["product"]["product_name"],
                        "Category": m["product"]["category"],
                        "Material": m["product"]["material"],
                        "CatalogUnitPrice": m["product"]["unit_price"],
                        "MinimumOrderQty": m["product"]["minimum_order_qty"],
                        "ConfidenceScore": m["confidence"],
                        "MatchType": m["match_type"],
                    }
                    for m in matches
                ],
                "BestMatch": {
                    "ItemId": best["product"]["item_id"],
                    "ProductName": best["product"]["product_name"],
                    "CatalogUnitPrice": best["product"]["unit_price"],
                    "ConfidenceScore": best["confidence"],
                } if best else None,
                "LineStatus": "matched" if best and best["confidence"] >= 0.8 else "review_needed",
            })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ProductMatch",
        "value": results,
        "TotalLines": len(results),
        "MatchedLines": sum(1 for r in results if r["LineStatus"] == "matched"),
        "ReviewNeeded": sum(1 for r in results if r["LineStatus"] == "review_needed"),
    }


def validate_pricing(customer_id: str, line_items: list[dict]) -> dict:
    """
    Validate pricing against contracted rates for a customer.
    Input line_items: list of dicts with 'item_id', 'unit_price', 'quantity'.
    """
    results = []

    with get_db() as conn:
        for item in line_items:
            item_id = item.get("item_id", "")
            requested_price = item.get("unit_price", 0)
            quantity = item.get("quantity", 0)

            # Check contracted pricing
            contracted = conn.execute("""
                SELECT * FROM customer_pricing
                WHERE customer_id = ? AND item_id = ?
                AND (expiry_date IS NULL OR expiry_date >= date('now'))
                ORDER BY effective_date DESC LIMIT 1
            """, (customer_id, item_id)).fetchone()

            # Get catalog price as fallback
            product = conn.execute(
                "SELECT unit_price, product_name FROM products WHERE item_id = ?",
                (item_id,)
            ).fetchone()

            catalog_price = product["unit_price"] if product else None
            contracted_price = contracted["contracted_price"] if contracted else None
            discount_pct = contracted["discount_pct"] if contracted else 0

            # Determine expected price
            expected_price = contracted_price or catalog_price
            price_variance = abs(requested_price - expected_price) if expected_price and requested_price else None
            price_variance_pct = (price_variance / expected_price * 100) if expected_price and price_variance else None

            # Status logic
            if price_variance is None:
                status = "no_reference_price"
            elif price_variance < 0.01:
                status = "exact_match"
            elif price_variance_pct and price_variance_pct <= 2:
                status = "within_tolerance"
            else:
                status = "price_mismatch"

            results.append({
                "ItemId": item_id,
                "ProductName": product["product_name"] if product else "Unknown",
                "RequestedPrice": requested_price,
                "CatalogPrice": catalog_price,
                "ContractedPrice": contracted_price,
                "DiscountPct": discount_pct,
                "ExpectedPrice": expected_price,
                "PriceVariance": round(price_variance, 2) if price_variance else None,
                "PriceVariancePct": round(price_variance_pct, 2) if price_variance_pct else None,
                "Quantity": quantity,
                "LineTotal": round(requested_price * quantity, 2) if requested_price else None,
                "Status": status,
            })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#PricingValidation",
        "CustomerId": customer_id,
        "value": results,
        "TotalLines": len(results),
        "ExactMatches": sum(1 for r in results if r["Status"] == "exact_match"),
        "WithinTolerance": sum(1 for r in results if r["Status"] == "within_tolerance"),
        "PriceMismatches": sum(1 for r in results if r["Status"] == "price_mismatch"),
    }


def get_sample_pos() -> dict:
    """Return sample PO documents for demo purposes."""
    samples = [
        {
            "id": "sample_po_1",
            "title": "Acme Medical Devices \u2014 Standard Reorder",
            "description": "Clean typed PO from a known premium customer with contracted pricing",
            "text": """PURCHASE ORDER

From: Acme Medical Devices
Attn: Sarah Chen, Procurement Manager
Date: March 28, 2026
PO Number: ACME-PO-2026-0412

Ship To:
Acme Medical Devices
1200 Innovation Drive
Boston, MA 02101

Bill To: Same as above

Payment Terms: Net 30

Line Items:
1. Part #11195 - 1-Way Stopcock, Female Luer Lock - Qty: 500 - Unit Price: $2.57 ea
2. Part #99720 - 2-Way Stopcock - Qty: 200 - Unit Price: $3.11 ea
3. Part #11455 - Luer Lock Connector, Gamma Stable - Qty: 300 - Unit Price: $1.08 ea

Requested Delivery: April 15, 2026

Notes: Please include Certificate of Compliance with shipment.
Contact: Sarah Chen, schen@acmemedical.com, (617) 555-0142"""
        },
        {
            "id": "sample_po_2",
            "title": "BioFlow Systems \u2014 New Product Mix",
            "description": "PO with vague descriptions instead of part numbers \u2014 tests fuzzy matching",
            "text": """Purchase Order #BFS-7891

BioFlow Systems Inc.
2500 Research Parkway
Atlanta, GA 30301

Date: March 30, 2026
Contact: James Rodriguez

Items Requested:
- 25 coils of 1/4" silicone tubing (50 ft each) @ $65.00
- 100 units barbed check valve for 1/4" tubing @ $4.50
- 200 hydrophilic filters with luer connections @ $3.50
- 500 ratchet-style pinch clamps @ $0.65

Shipping: Standard Ground
Terms: Net 30
Deliver by: April 20, 2026"""
        },
        {
            "id": "sample_po_3",
            "title": "Unknown Customer \u2014 Email PO",
            "description": "Informal email PO from a customer not in the system \u2014 tests new customer handling",
            "text": """Subject: Order Request

Hi Qosina team,

We'd like to place an order for the following items:

- 50 units of your needleless injection site (the swabbable one with luer locks) - $6.75 each
- 100 extension lines, 6 inch, luer lock both ends - $2.10 each
- 25 Y-connectors with spin lock - $4.50 each

We're a new customer - Pacific Coast Medical Supplies out of San Diego. My name is Jennifer Walsh, jwalsh@pacificcoastmed.com.

Can you send us a quote or confirm these prices? We'd need delivery by end of April.

Thanks,
Jennifer Walsh
Purchasing Director
Pacific Coast Medical Supplies
(858) 555-0199"""
        },
    ]

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#SamplePurchaseOrders",
        "value": samples,
        "TotalSamples": len(samples),
    }
