"""Pure tool functions for the Qosina AI agent. No LangGraph dependency."""

from datetime import datetime, timedelta
from backend.database import get_db


def search_products(query: str) -> dict:
    """Search the product catalog by name, category, material, or connection type."""
    with get_db() as conn:
        like = f"%{query}%"
        rows = conn.execute(
            """SELECT * FROM products
               WHERE product_name LIKE ? OR category LIKE ? OR material LIKE ?
               OR connection_type LIKE ? OR description LIKE ?""",
            (like, like, like, like, like)
        ).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#Products",
        "value": [
            {
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "Category": r["category"],
                "Description": r["description"],
                "ConnectionType": r["connection_type"],
                "Material": r["material"],
                "TechnicalDetail": r["technical_detail"],
                "ISOCompliance": r["iso_compliance"],
                "ManufacturingEnvironment": r["manufacturing_environment"],
                "ShelfLifeMonths": r["shelf_life_months"],
                "UnitPrice": r["unit_price"],
                "MinimumOrderQty": r["minimum_order_qty"],
                "Status": r["status"],
            }
            for r in rows
        ],
    }


def check_inventory(part_number: str) -> dict:
    """Check inventory for a specific part number, including lot details."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT i.*, p.product_name FROM inventory i
               JOIN products p ON i.item_id = p.item_id
               WHERE i.item_id = ?""",
            (part_number,)
        ).fetchall()

    if not rows:
        return {
            "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#InventoryOnHand",
            "value": [],
            "TotalOnHand": 0,
            "BelowReorderPoint": False,
            "Message": f"No inventory found for part {part_number}",
        }

    total = sum(r["quantity_on_hand"] for r in rows)
    reorder_point = rows[0]["reorder_point"]

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#InventoryOnHand",
        "value": [
            {
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "LotNumber": r["lot_number"],
                "QuantityOnHand": r["quantity_on_hand"],
                "WarehouseLocation": r["warehouse_location"],
                "ReceivedDate": r["received_date"],
                "ExpirationDate": r["expiration_date"],
                "ReorderPoint": r["reorder_point"],
                "ReorderQuantity": r["reorder_quantity"],
            }
            for r in rows
        ],
        "TotalOnHand": total,
        "ReorderPoint": reorder_point,
        "BelowReorderPoint": total < reorder_point,
    }


def find_compatible_parts(part_number: str) -> dict:
    """Find parts compatible with a given part number."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT pc.*,
                      pa.product_name as part_a_name, pb.product_name as part_b_name,
                      pa.connection_type as part_a_connection, pb.connection_type as part_b_connection,
                      pa.iso_compliance as part_a_iso, pb.iso_compliance as part_b_iso
               FROM product_compatibility pc
               JOIN products pa ON pc.part_a = pa.item_id
               JOIN products pb ON pc.part_b = pb.item_id
               WHERE pc.part_a = ? OR pc.part_b = ?""",
            (part_number, part_number)
        ).fetchall()

    results = []
    for r in rows:
        # Determine which part is the "other" part
        if r["part_a"] == part_number:
            other_id = r["part_b"]
            other_name = r["part_b_name"]
            other_connection = r["part_b_connection"]
            other_iso = r["part_b_iso"]
        else:
            other_id = r["part_a"]
            other_name = r["part_a_name"]
            other_connection = r["part_a_connection"]
            other_iso = r["part_a_iso"]

        results.append({
            "CompatiblePartId": other_id,
            "CompatiblePartName": other_name,
            "ConnectionType": other_connection,
            "ISOCompliance": other_iso,
            "CompatibilityType": r["compatibility_type"],
            "Notes": r["notes"],
        })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ProductCompatibility",
        "SourcePartId": part_number,
        "value": results,
    }


def check_expiring_inventory(days_ahead: int = 90) -> dict:
    """Find inventory lots expiring within the specified number of days."""
    cutoff = (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")

    with get_db() as conn:
        rows = conn.execute(
            """SELECT i.*, p.product_name FROM inventory i
               JOIN products p ON i.item_id = p.item_id
               WHERE i.expiration_date IS NOT NULL
               AND i.expiration_date <= ?
               AND i.quantity_on_hand > 0
               ORDER BY i.expiration_date ASC""",
            (cutoff,)
        ).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ExpiringInventory",
        "DaysAhead": days_ahead,
        "CutoffDate": cutoff,
        "value": [
            {
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "LotNumber": r["lot_number"],
                "QuantityOnHand": r["quantity_on_hand"],
                "WarehouseLocation": r["warehouse_location"],
                "ExpirationDate": r["expiration_date"],
                "DaysUntilExpiry": (datetime.strptime(r["expiration_date"], "%Y-%m-%d") - datetime.now()).days,
            }
            for r in rows
        ],
    }


def check_low_stock() -> dict:
    """Find parts where total on-hand quantity is below reorder point."""
    with get_db() as conn:
        rows = conn.execute(
            """SELECT i.item_id, p.product_name, p.category,
                      SUM(i.quantity_on_hand) as total_on_hand,
                      MIN(i.reorder_point) as reorder_point,
                      MIN(i.reorder_quantity) as reorder_quantity
               FROM inventory i
               JOIN products p ON i.item_id = p.item_id
               GROUP BY i.item_id
               HAVING total_on_hand < reorder_point"""
        ).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#LowStockAlert",
        "value": [
            {
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "Category": r["category"],
                "TotalOnHand": r["total_on_hand"],
                "ReorderPoint": r["reorder_point"],
                "ReorderQuantity": r["reorder_quantity"],
                "Deficit": r["reorder_point"] - r["total_on_hand"],
            }
            for r in rows
        ],
    }


def get_customer_order_history(customer_id: str) -> dict:
    """Get order history for a customer."""
    with get_db() as conn:
        customer = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()

        if not customer:
            return {
                "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#OrderHistory",
                "value": [],
                "Message": f"Customer {customer_id} not found",
            }

        rows = conn.execute(
            """SELECT o.*, p.product_name, p.category
               FROM order_history o
               JOIN products p ON o.item_id = p.item_id
               WHERE o.customer_id = ?
               ORDER BY o.order_date DESC""",
            (customer_id,)
        ).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#OrderHistory",
        "Customer": {
            "CustomerId": customer["customer_id"],
            "CompanyName": customer["company_name"],
            "ContactName": customer["contact_name"],
            "Industry": customer["industry"],
            "Region": customer["region"],
            "AccountTier": customer["account_tier"],
        },
        "value": [
            {
                "OrderId": r["order_id"],
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "Category": r["category"],
                "Quantity": r["quantity"],
                "OrderDate": r["order_date"],
                "UnitPrice": r["unit_price"],
                "TotalPrice": r["total_price"],
            }
            for r in rows
        ],
        "TotalOrders": len(rows),
        "TotalRevenue": sum(r["total_price"] for r in rows),
    }


def create_approval(recommendation_type: str, title: str, content: str, source_query: str = "") -> dict:
    """Create a new approval queue item for human review."""
    now = datetime.now().isoformat()

    with get_db() as conn:
        cursor = conn.execute(
            """INSERT INTO approval_queue (recommendation_type, title, content, source_query, ai_generated_at)
               VALUES (?, ?, ?, ?, ?)""",
            (recommendation_type, title, content, source_query, now)
        )
        approval_id = cursor.lastrowid

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ApprovalQueue",
        "Id": approval_id,
        "RecommendationType": recommendation_type,
        "Title": title,
        "Content": content,
        "Status": "pending",
        "AIGeneratedAt": now,
        "Message": f"Approval item #{approval_id} created and queued for human review.",
    }
