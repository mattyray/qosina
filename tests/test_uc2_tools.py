"""Unit tests for UC2: Accounts Payable Processing tools."""

import pytest
import os
from backend.database import init_db, get_db, DB_PATH
from backend.seed import seed
from backend.use_case_2.tools import (
    three_way_match,
    match_payment,
    score_collections,
    get_vendor_invoices,
    get_unapplied_payments,
)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    seed()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestThreeWayMatch:
    def test_perfect_match(self):
        result = three_way_match("VINV-2026-001")
        assert result["OverallStatus"] == "full_match"
        assert result["Summary"]["Discrepancies"] == 0
        assert "Auto-approve" in result["Recommendation"]

    def test_penny_discrepancy(self):
        result = three_way_match("VINV-2026-002")
        # $0.03 discrepancy should be within tolerance
        assert result["OverallStatus"] in ("within_tolerance", "full_match")
        assert result["TotalVariance"] <= 0.05

    def test_quantity_mismatch(self):
        # VINV-2026-005: invoiced 500, received 480
        result = three_way_match("VINV-2026-005")
        assert result["OverallStatus"] == "discrepancy_found"
        assert result["Summary"]["Discrepancies"] >= 1
        assert "review" in result["Recommendation"].lower()

    def test_nonexistent_invoice(self):
        result = three_way_match("FAKE-INVOICE")
        assert "not found" in result.get("Message", "").lower()

    def test_line_details(self):
        result = three_way_match("VINV-2026-001")
        for line in result["value"]:
            assert "ItemId" in line
            assert "QuantityOrdered" in line
            assert "QuantityReceived" in line
            assert "QuantityInvoiced" in line
            assert "LineStatus" in line


class TestMatchPayment:
    def test_unapplied_payment(self):
        # PAY-2026-006: $1,345 from CUST-003, doesn't exactly match either invoice
        result = match_payment("PAY-2026-006")
        assert result["PaymentAmount"] == 1345.00
        assert result["CustomerName"] == "MedLine Innovations"
        assert len(result["OpenInvoices"]) >= 1
        assert len(result["Suggestions"]) >= 1

    def test_nonexistent_payment(self):
        result = match_payment("FAKE-PAYMENT")
        assert "not found" in result.get("Message", "").lower()

    def test_applied_payment(self):
        # PAY-2026-001 is already applied
        result = match_payment("PAY-2026-001")
        assert result["CurrentStatus"] == "applied"


class TestScoreCollections:
    def test_returns_overdue_accounts(self):
        result = score_collections()
        assert result["Summary"]["TotalOverdueAccounts"] >= 1
        assert result["Summary"]["TotalOverdueAmount"] > 0

    def test_priority_ranking(self):
        result = score_collections()
        # Should be sorted by risk score descending
        scores = [r["RiskScore"] for r in result["value"]]
        assert scores == sorted(scores, reverse=True)

    def test_has_reasoning(self):
        result = score_collections()
        for account in result["value"]:
            assert "Reasoning" in account
            assert len(account["Reasoning"]) > 0
            assert "RecommendedAction" in account
            assert account["Priority"] in ("high", "medium", "low")

    def test_cust003_overdue(self):
        result = score_collections()
        cust003 = [r for r in result["value"] if r["CustomerId"] == "CUST-003"]
        assert len(cust003) == 1
        assert cust003[0]["TotalOverdue"] > 0
        assert cust003[0]["DaysOverdue"] > 30


class TestGetVendorInvoices:
    def test_returns_invoices(self):
        result = get_vendor_invoices()
        assert len(result["value"]) == 5
        for inv in result["value"]:
            assert "InvoiceId" in inv
            assert "VendorName" in inv
            assert "PONumber" in inv


class TestGetUnappliedPayments:
    def test_returns_unapplied(self):
        result = get_unapplied_payments()
        assert len(result["value"]) >= 1
        for p in result["value"]:
            assert p["Status"] == "unapplied"
