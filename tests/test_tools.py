"""Unit tests for tool functions."""

import pytest
from backend.database import init_db, get_db, DB_PATH
from backend.seed import seed
from backend.tools import (
    search_products,
    check_inventory,
    find_compatible_parts,
    check_expiring_inventory,
    check_low_stock,
    get_customer_order_history,
    create_approval,
)
import os


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    """Seed database once for all tests."""
    # Remove existing DB to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    seed()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestSearchProducts:
    def test_search_by_name(self):
        result = search_products("stopcock")
        assert len(result["value"]) >= 4
        assert result["@odata.context"].endswith("#Products")

    def test_search_by_material(self):
        result = search_products("Silicone")
        assert len(result["value"]) > 0
        for p in result["value"]:
            assert "Silicone" in p["Material"] or "Silicone" in p.get("Description", "")

    def test_search_by_connection_type(self):
        result = search_products("Barbed")
        assert len(result["value"]) > 0

    def test_search_no_results(self):
        result = search_products("xyznonexistent")
        assert result["value"] == []


class TestCheckInventory:
    def test_existing_part(self):
        result = check_inventory("11195")
        assert result["TotalOnHand"] == 3650  # 2450 + 1200
        assert len(result["value"]) == 2
        assert not result["BelowReorderPoint"]

    def test_low_stock_part(self):
        result = check_inventory("91050")
        assert result["TotalOnHand"] == 45
        assert result["BelowReorderPoint"] is True

    def test_nonexistent_part(self):
        result = check_inventory("FAKE123")
        assert result["TotalOnHand"] == 0
        assert result["value"] == []


class TestFindCompatibleParts:
    def test_compatible_parts_exist(self):
        result = find_compatible_parts("80147")
        assert len(result["value"]) > 0
        assert result["SourcePartId"] == "80147"

    def test_compatibility_includes_details(self):
        result = find_compatible_parts("11195")
        part_ids = [p["CompatiblePartId"] for p in result["value"]]
        assert "80147" in part_ids  # Stopcock compatible with injection site

    def test_no_compatible_parts(self):
        result = find_compatible_parts("FAKE123")
        assert result["value"] == []


class TestCheckExpiringInventory:
    def test_expiring_within_180_days(self):
        result = check_expiring_inventory(180)
        assert result["@odata.context"].endswith("#ExpiringInventory")
        # LOT-2023-0115 for part 11096 expires 2026-07-20

    def test_expiring_within_30_days(self):
        result = check_expiring_inventory(30)
        # Probably nothing expiring in 30 days from test date
        assert isinstance(result["value"], list)


class TestCheckLowStock:
    def test_finds_low_stock(self):
        result = check_low_stock()
        low_ids = [item["ItemId"] for item in result["value"]]
        assert "91050" in low_ids  # 45 on hand, reorder at 100
        assert "97337" in low_ids  # 75 on hand, reorder at 100
        assert "14054" in low_ids  # 45 on hand, reorder at 100

    def test_includes_deficit(self):
        result = check_low_stock()
        for item in result["value"]:
            assert item["Deficit"] > 0


class TestGetCustomerOrderHistory:
    def test_existing_customer(self):
        result = get_customer_order_history("CUST-001")
        assert result["Customer"]["CompanyName"] == "Acme Medical Devices"
        assert result["TotalOrders"] == 6
        assert result["TotalRevenue"] > 0

    def test_nonexistent_customer(self):
        result = get_customer_order_history("CUST-999")
        assert result["value"] == []
        assert "not found" in result["Message"]

    def test_declining_customer(self):
        result = get_customer_order_history("CUST-003")
        assert result["TotalOrders"] == 3
        # Orders should be in descending date order
        dates = [o["OrderDate"] for o in result["value"]]
        assert dates == sorted(dates, reverse=True)


class TestCreateApproval:
    def test_create_approval(self):
        result = create_approval("reorder", "Reorder Part #91050", "Stock is low at 45 units.")
        assert result["Status"] == "pending"
        assert result["Id"] is not None
        assert "queued for human review" in result["Message"]

    def test_approval_types(self):
        for atype in ["reorder", "customer_outreach", "expiry_alert", "draft_response", "general"]:
            result = create_approval(atype, f"Test {atype}", "Test content")
            assert result["RecommendationType"] == atype
