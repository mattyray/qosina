"""Pure tool functions for UC2: Accounts Payable Processing. No LangGraph dependency."""

from datetime import datetime
from backend.database import get_db


def three_way_match(invoice_id: str) -> dict:
    """Run three-way match: compare vendor invoice vs PO vs receipt."""
    with get_db() as conn:
        # Get invoice
        invoice = conn.execute(
            "SELECT * FROM vendor_invoices WHERE invoice_id = ?", (invoice_id,)
        ).fetchone()
        if not invoice:
            return {
                "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ThreeWayMatch",
                "value": [], "Message": f"Invoice {invoice_id} not found",
            }

        po_number = invoice["po_number"]
        vendor = conn.execute(
            "SELECT * FROM vendors WHERE vendor_id = ?", (invoice["vendor_id"],)
        ).fetchone()

        # Get invoice lines
        inv_lines = conn.execute(
            "SELECT * FROM invoice_lines WHERE invoice_id = ?", (invoice_id,)
        ).fetchall()

        # Get PO lines
        po_lines = conn.execute(
            "SELECT * FROM po_lines WHERE po_number = ?", (po_number,)
        ).fetchall()

        # Get receipt and receipt lines
        receipt = conn.execute(
            "SELECT * FROM receipts WHERE po_number = ?", (po_number,)
        ).fetchone()
        rec_lines = []
        if receipt:
            rec_lines = conn.execute(
                "SELECT * FROM receipt_lines WHERE receipt_id = ?", (receipt["receipt_id"],)
            ).fetchall()

        # Build lookup dicts by item_id
        po_by_item = {r["item_id"]: dict(r) for r in po_lines}
        rec_by_item = {r["item_id"]: dict(r) for r in rec_lines}

        line_results = []
        total_variance = 0.0

        for inv_line in inv_lines:
            item_id = inv_line["item_id"]
            po_line = po_by_item.get(item_id)
            rec_line = rec_by_item.get(item_id)

            product = conn.execute(
                "SELECT product_name FROM products WHERE item_id = ?", (item_id,)
            ).fetchone()

            qty_ordered = po_line["quantity_ordered"] if po_line else None
            qty_received = rec_line["quantity_received"] if rec_line else None
            qty_invoiced = inv_line["quantity_invoiced"]

            po_unit_price = po_line["unit_price"] if po_line else None
            inv_unit_price = inv_line["unit_price"]

            po_line_total = po_line["line_total"] if po_line else None
            inv_line_total = inv_line["line_total"]

            # Calculate variances
            qty_variance = None
            price_variance = None
            receipt_variance = None
            issues = []

            if qty_ordered is not None:
                qty_variance = qty_invoiced - qty_ordered
                if qty_variance != 0:
                    issues.append(f"Quantity: invoiced {qty_invoiced} vs ordered {qty_ordered} (diff: {qty_variance:+d})")

            if qty_received is not None:
                receipt_variance = qty_invoiced - qty_received
                if receipt_variance != 0:
                    issues.append(f"Receipt: invoiced {qty_invoiced} vs received {qty_received} (diff: {receipt_variance:+d})")

            if po_unit_price is not None:
                price_variance = round(inv_unit_price - po_unit_price, 4)
                if abs(price_variance) > 0.001:
                    issues.append(f"Unit price: invoiced ${inv_unit_price:.4f} vs PO ${po_unit_price:.4f} (diff: ${price_variance:+.4f})")

            amount_variance = round(inv_line_total - (po_line_total or inv_line_total), 2)
            total_variance += abs(amount_variance)

            # Determine line status
            if not issues:
                status = "match"
            elif all(abs(v) < 0.05 for v in [amount_variance, price_variance or 0] if v is not None):
                status = "within_tolerance"
            else:
                status = "discrepancy"

            line_results.append({
                "ItemId": item_id,
                "ProductName": product["product_name"] if product else "Unknown",
                "QuantityOrdered": qty_ordered,
                "QuantityReceived": qty_received,
                "QuantityInvoiced": qty_invoiced,
                "POUnitPrice": po_unit_price,
                "InvoiceUnitPrice": inv_unit_price,
                "POLineTotal": po_line_total,
                "InvoiceLineTotal": inv_line_total,
                "AmountVariance": amount_variance,
                "QuantityVariance": qty_variance,
                "ReceiptVariance": receipt_variance,
                "PriceVariance": price_variance,
                "Issues": issues,
                "LineStatus": status,
            })

        # Overall status
        discrepancies = [l for l in line_results if l["LineStatus"] == "discrepancy"]
        tolerances = [l for l in line_results if l["LineStatus"] == "within_tolerance"]
        matches = [l for l in line_results if l["LineStatus"] == "match"]

        if not discrepancies and not tolerances:
            overall_status = "full_match"
            recommendation = "Auto-approve — all lines match perfectly."
        elif not discrepancies and tolerances:
            overall_status = "within_tolerance"
            recommendation = f"Auto-approve — {len(tolerances)} line(s) within $0.05 tolerance threshold."
        else:
            overall_status = "discrepancy_found"
            recommendation = f"Requires review — {len(discrepancies)} line(s) with discrepancies."

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ThreeWayMatch",
        "InvoiceId": invoice_id,
        "PONumber": po_number,
        "VendorName": vendor["vendor_name"] if vendor else "Unknown",
        "InvoiceTotal": invoice["total_amount"],
        "POTotal": sum(pl["line_total"] for pl in po_lines),
        "TotalVariance": round(total_variance, 2),
        "OverallStatus": overall_status,
        "Recommendation": recommendation,
        "value": line_results,
        "Summary": {
            "TotalLines": len(line_results),
            "PerfectMatches": len(matches),
            "WithinTolerance": len(tolerances),
            "Discrepancies": len(discrepancies),
        },
    }


def match_payment(payment_id: str) -> dict:
    """Try to match an unapplied payment against open customer invoices."""
    with get_db() as conn:
        payment = conn.execute(
            "SELECT * FROM payments WHERE payment_id = ?", (payment_id,)
        ).fetchone()
        if not payment:
            return {
                "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#PaymentMatch",
                "value": [], "Message": f"Payment {payment_id} not found",
            }

        customer_id = payment["customer_id"]
        amount = payment["amount"]

        customer = conn.execute(
            "SELECT * FROM customers WHERE customer_id = ?", (customer_id,)
        ).fetchone()

        # Get all open/overdue invoices for this customer
        open_invoices = conn.execute("""
            SELECT * FROM customer_invoices
            WHERE customer_id = ? AND status IN ('open', 'overdue')
            ORDER BY due_date ASC
        """, (customer_id,)).fetchall()

        suggestions = []

        # 1. Try exact single-invoice match
        for inv in open_invoices:
            remaining = inv["total_amount"] - inv["amount_paid"]
            diff = abs(amount - remaining)
            if diff < 0.01:
                suggestions.append({
                    "Type": "exact_match",
                    "Invoices": [{"InvoiceId": inv["invoice_id"], "Amount": remaining}],
                    "TotalApplied": remaining,
                    "Remainder": round(amount - remaining, 2),
                    "Confidence": 0.99,
                    "Description": f"Exact match to {inv['invoice_id']} (${remaining:.2f})",
                })

        # 2. Try multi-invoice combinations (simple: oldest first)
        if not suggestions:
            running_total = 0.0
            combo = []
            for inv in open_invoices:
                remaining = inv["total_amount"] - inv["amount_paid"]
                if running_total + remaining <= amount + 0.05:
                    combo.append({"InvoiceId": inv["invoice_id"], "Amount": remaining})
                    running_total += remaining

            if combo:
                diff = abs(amount - running_total)
                if diff < 0.05:
                    confidence = 0.95
                    desc = f"Exact multi-invoice match: {', '.join(c['InvoiceId'] for c in combo)}"
                elif diff < 50:
                    confidence = 0.70
                    desc = f"Partial match (${diff:.2f} variance): {', '.join(c['InvoiceId'] for c in combo)}"
                else:
                    confidence = 0.40
                    desc = f"Best guess allocation (${diff:.2f} unmatched)"

                suggestions.append({
                    "Type": "multi_invoice" if len(combo) > 1 else "partial_payment",
                    "Invoices": combo,
                    "TotalApplied": round(running_total, 2),
                    "Remainder": round(amount - running_total, 2),
                    "Confidence": confidence,
                    "Description": desc,
                })

        # 3. Check for penny discrepancy on any single invoice
        for inv in open_invoices:
            remaining = inv["total_amount"] - inv["amount_paid"]
            diff = abs(amount - remaining)
            if 0.01 <= diff <= 0.05:
                suggestions.append({
                    "Type": "penny_discrepancy",
                    "Invoices": [{"InvoiceId": inv["invoice_id"], "Amount": remaining}],
                    "TotalApplied": remaining,
                    "Remainder": round(amount - remaining, 2),
                    "Confidence": 0.90,
                    "Description": f"Penny discrepancy (${diff:.2f}) on {inv['invoice_id']} — recommend auto-apply and write off",
                })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#PaymentMatch",
        "PaymentId": payment_id,
        "CustomerName": customer["company_name"] if customer else "Unknown",
        "PaymentAmount": amount,
        "PaymentDate": payment["payment_date"],
        "Reference": payment["reference"],
        "CurrentStatus": payment["status"],
        "OpenInvoices": [
            {
                "InvoiceId": inv["invoice_id"],
                "DueDate": inv["due_date"],
                "TotalAmount": inv["total_amount"],
                "AmountPaid": inv["amount_paid"],
                "Remaining": round(inv["total_amount"] - inv["amount_paid"], 2),
                "Status": inv["status"],
            }
            for inv in open_invoices
        ],
        "Suggestions": suggestions,
        "BestSuggestion": suggestions[0] if suggestions else None,
    }


def score_collections() -> dict:
    """Score and rank overdue customer accounts for collections prioritization."""
    with get_db() as conn:
        now = datetime.now()

        # Get all customers with overdue invoices
        customers = conn.execute("""
            SELECT c.*,
                   COUNT(ci.invoice_id) as overdue_count,
                   SUM(ci.total_amount - ci.amount_paid) as total_overdue,
                   MIN(ci.due_date) as oldest_due_date,
                   MAX(ci.due_date) as newest_due_date
            FROM customers c
            JOIN customer_invoices ci ON c.customer_id = ci.customer_id
            WHERE ci.status = 'overdue'
            GROUP BY c.customer_id
            ORDER BY total_overdue DESC
        """).fetchall()

        results = []
        for cust in customers:
            customer_id = cust["customer_id"]

            # Get payment history for trend analysis
            payment_history = conn.execute("""
                SELECT * FROM payments
                WHERE customer_id = ?
                ORDER BY payment_date DESC
            """, (customer_id,)).fetchall()

            # Get all invoices for aging
            all_invoices = conn.execute("""
                SELECT * FROM customer_invoices
                WHERE customer_id = ?
                ORDER BY due_date
            """, (customer_id,)).fetchall()

            # Calculate days overdue for oldest
            oldest_due = datetime.strptime(cust["oldest_due_date"], "%Y-%m-%d")
            days_overdue = (now - oldest_due).days

            # Score components (0-100)
            # Amount factor: higher overdue = higher priority
            amount_score = min(40, cust["total_overdue"] / 50)  # max 40 points at $2000+

            # Age factor: older = more urgent
            age_score = min(30, days_overdue / 3)  # max 30 points at 90+ days

            # Trend factor: worsening payment = more urgent
            recent_payments = len(payment_history)
            if recent_payments == 0:
                trend_score = 20  # No payments at all = bad
                trend = "no_payment_history"
            elif days_overdue > 90:
                trend_score = 20
                trend = "severely_delinquent"
            elif days_overdue > 30:
                trend_score = 15
                trend = "worsening"
            else:
                trend_score = 5
                trend = "recently_overdue"

            # Account tier factor
            tier_score = 10 if cust["account_tier"] == "premium" else 0

            total_score = round(amount_score + age_score + trend_score + tier_score, 1)
            priority = "high" if total_score >= 50 else "medium" if total_score >= 25 else "low"

            # Generate reasoning
            reasoning = []
            if days_overdue > 60:
                reasoning.append(f"Severely overdue: {days_overdue} days past oldest due date")
            elif days_overdue > 30:
                reasoning.append(f"Significantly overdue: {days_overdue} days")
            if cust["total_overdue"] > 1000:
                reasoning.append(f"Large outstanding balance: ${cust['total_overdue']:,.2f}")
            if cust["overdue_count"] > 1:
                reasoning.append(f"Multiple overdue invoices: {cust['overdue_count']}")
            if trend == "no_payment_history":
                reasoning.append("No recent payment activity")
            if cust["account_tier"] == "premium":
                reasoning.append("Premium account — high strategic value")

            recommended_action = "Immediate phone call" if priority == "high" else "Send reminder email" if priority == "medium" else "Monitor"

            results.append({
                "CustomerId": customer_id,
                "CompanyName": cust["company_name"],
                "ContactName": cust["contact_name"],
                "AccountTier": cust["account_tier"],
                "TotalOverdue": round(cust["total_overdue"], 2),
                "OverdueInvoices": cust["overdue_count"],
                "DaysOverdue": days_overdue,
                "OldestDueDate": cust["oldest_due_date"],
                "PaymentTrend": trend,
                "RiskScore": total_score,
                "Priority": priority,
                "Reasoning": reasoning,
                "RecommendedAction": recommended_action,
            })

        results.sort(key=lambda r: r["RiskScore"], reverse=True)

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#CollectionsPriority",
        "AnalysisDate": now.strftime("%Y-%m-%d"),
        "value": results,
        "Summary": {
            "TotalOverdueAccounts": len(results),
            "TotalOverdueAmount": round(sum(r["TotalOverdue"] for r in results), 2),
            "HighPriority": sum(1 for r in results if r["Priority"] == "high"),
            "MediumPriority": sum(1 for r in results if r["Priority"] == "medium"),
            "LowPriority": sum(1 for r in results if r["Priority"] == "low"),
        },
    }


def get_vendor_invoices() -> dict:
    """Get all vendor invoices with their match status."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT vi.*, v.vendor_name
            FROM vendor_invoices vi
            JOIN vendors v ON vi.vendor_id = v.vendor_id
            ORDER BY vi.invoice_date DESC
        """).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#VendorInvoices",
        "value": [
            {
                "InvoiceId": r["invoice_id"],
                "VendorName": r["vendor_name"],
                "PONumber": r["po_number"],
                "InvoiceDate": r["invoice_date"],
                "DueDate": r["due_date"],
                "TotalAmount": r["total_amount"],
                "Status": r["status"],
                "MatchStatus": r["match_status"],
            }
            for r in rows
        ],
    }


def get_unapplied_payments() -> dict:
    """Get all unapplied payments that need cash application."""
    with get_db() as conn:
        rows = conn.execute("""
            SELECT p.*, c.company_name
            FROM payments p
            JOIN customers c ON p.customer_id = c.customer_id
            WHERE p.status = 'unapplied'
            ORDER BY p.payment_date DESC
        """).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#UnappliedPayments",
        "value": [
            {
                "PaymentId": r["payment_id"],
                "CustomerName": r["company_name"],
                "PaymentDate": r["payment_date"],
                "Amount": r["amount"],
                "Reference": r["reference"],
                "Status": r["status"],
            }
            for r in rows
        ],
    }
