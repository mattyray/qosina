"""Unit tests for UC1: Sales Order Entry tools."""

import pytest
import os
from backend.database import init_db, get_db, DB_PATH
from backend.seed import seed
from backend.use_case_1.tools import (
    match_customer,
    match_products,
    validate_pricing,
    get_sample_pos,
)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    seed()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestMatchCustomer:
    def test_exact_name_match(self):
        result = match_customer(name="Acme Medical Devices")
        assert result["BestMatch"] is not None
        assert result["BestMatch"]["CustomerId"] == "CUST-001"
        assert result["BestMatch"]["ConfidenceScore"] >= 0.85

    def test_partial_name_match(self):
        result = match_customer(name="Acme")
        assert len(result["value"]) >= 1
        assert result["BestMatch"]["CustomerId"] == "CUST-001"

    def test_contact_name_match(self):
        result = match_customer(name="Sarah Chen")
        assert len(result["value"]) >= 1

    def test_no_match(self):
        result = match_customer(name="Totally Fake Company XYZ")
        assert result["value"] == []
        assert result["BestMatch"] is None

    def test_empty_search(self):
        result = match_customer()
        # Should return all customers
        assert len(result["value"]) >= 6


class TestMatchProducts:
    def test_exact_part_number(self):
        result = match_products([{"part_number": "11195", "quantity": 500}])
        assert result["TotalLines"] == 1
        line = result["value"][0]
        assert line["BestMatch"]["ItemId"] == "11195"
        assert line["BestMatch"]["ConfidenceScore"] >= 0.95
        assert line["LineStatus"] == "matched"

    def test_fuzzy_description(self):
        result = match_products([{"description": "stopcock", "quantity": 100}])
        assert result["TotalLines"] == 1
        line = result["value"][0]
        assert len(line["Matches"]) > 0
        assert line["LineStatus"] == "matched"

    def test_multiple_items(self):
        result = match_products([
            {"part_number": "11195", "quantity": 500},
            {"part_number": "99720", "quantity": 200},
            {"description": "silicone tubing", "quantity": 25},
        ])
        assert result["TotalLines"] == 3
        assert result["MatchedLines"] >= 2

    def test_no_match(self):
        result = match_products([{"description": "xyznonexistent", "quantity": 1}])
        assert result["TotalLines"] == 1
        assert result["value"][0]["BestMatch"] is None
        assert result["value"][0]["LineStatus"] == "review_needed"

    def test_empty_list(self):
        result = match_products([])
        assert result["TotalLines"] == 0


class TestValidatePricing:
    def test_contracted_price_match(self):
        result = validate_pricing("CUST-001", [
            {"item_id": "11195", "unit_price": 2.57, "quantity": 500},
        ])
        assert result["TotalLines"] == 1
        assert result["value"][0]["Status"] == "exact_match"

    def test_price_mismatch(self):
        result = validate_pricing("CUST-001", [
            {"item_id": "11195", "unit_price": 5.00, "quantity": 500},
        ])
        assert result["TotalLines"] == 1
        assert result["value"][0]["Status"] == "price_mismatch"
        assert result["PriceMismatches"] == 1

    def test_catalog_fallback(self):
        # CUST-004 has no contracted pricing for 28217
        result = validate_pricing("CUST-004", [
            {"item_id": "28217", "unit_price": 3.25, "quantity": 100},
        ])
        assert result["TotalLines"] == 1
        assert result["value"][0]["CatalogPrice"] == 3.25
        assert result["value"][0]["ContractedPrice"] is None

    def test_within_tolerance(self):
        result = validate_pricing("CUST-001", [
            {"item_id": "11195", "unit_price": 2.58, "quantity": 500},
        ])
        assert result["value"][0]["Status"] == "within_tolerance"


class TestGetSamplePOs:
    def test_returns_samples(self):
        result = get_sample_pos()
        assert result["TotalSamples"] == 3
        assert len(result["value"]) == 3
        ids = [s["id"] for s in result["value"]]
        assert "sample_po_1" in ids
        assert "sample_po_2" in ids
        assert "sample_po_3" in ids
