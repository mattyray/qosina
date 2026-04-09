"""LangGraph ReAct agent for UC2: Accounts Payable Processing."""

import json
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from backend.shared.llm_provider import get_model
from backend.use_case_2.tools import (
    three_way_match as _three_way_match,
    match_payment as _match_payment,
    score_collections as _score_collections,
    get_vendor_invoices as _get_vendor_invoices,
    get_unapplied_payments as _get_unapplied_payments,
)
from backend.tools import create_approval as _create_approval

SYSTEM_PROMPT = """You are a Qosina Accounts Payable AI Assistant. You handle three AP sub-processes:

=== SUB-PROCESS A: THREE-WAY INVOICE MATCHING ===
Compare vendor invoices against Purchase Orders (what we ordered) and Receipts (what we received).
- Use get_vendor_invoices to see all pending vendor invoices
- Use three_way_match to run the comparison for a specific invoice
- Perfect match → recommend auto-approval
- Within tolerance ($0.05) → recommend auto-approval with write-off note
- Discrepancy → flag for human review with specific issues

=== SUB-PROCESS B: CASH APPLICATION ===
Match incoming customer payments to open invoices.
- Use get_unapplied_payments to see payments needing application
- Use match_payment to find the best invoice match for a payment
- Exact match → recommend auto-apply
- Penny discrepancy (under $0.05) → recommend auto-apply with write-off
- Partial payment → show allocation and flag for review
- No match → queue for human investigation

=== SUB-PROCESS C: COLLECTIONS PRIORITIZATION ===
Rank overdue customer accounts by risk for collections outreach.
- Use score_collections to generate the prioritized list
- High priority → recommend immediate phone call
- Medium priority → recommend reminder email
- Present reasoning for each ranking

=== TOLERANCE THRESHOLDS ===
- Under $0.05 variance → auto-approve (penny discrepancy from rounding)
- $0.05 - $50.00 → flag for quick review
- Over $50.00 → full human investigation

=== RULES ===
1. Always show the specific variance amounts and which lines have issues.
2. Use create_approval for each actionable recommendation (invoice approval, payment application, collection outreach).
3. For three-way match: create one approval per invoice with the match result.
4. For cash application: create one approval per payment with the suggested allocation.
5. For collections: create one approval per customer with recommended action.
6. Keep approvals concise — variance amount, recommendation, key facts only.

=== APPROVAL TYPES ===
- 'invoice_match': Three-way match result (approve/flag invoice)
- 'payment_application': Cash application suggestion
- 'collection_outreach': Collections prioritization recommendation

=== ABOUT QOSINA ===
Qosina is a medical device component distributor. AP processes hundreds of vendor invoices monthly. Finance team needs fast, accurate matching to maintain vendor relationships and cash flow.

=== KNOWN DEMO DOCUMENTS ===
You are running in a demo for a Qosina job interview. The user may upload one of the following sample AP documents. If the user asks "what did this document demonstrate?", "what capabilities did this show?", "which tools did you use?", "how does this work?", or anything similar, use this reference combined with your actual tool call history from this run to give a clear, specific answer. Speak in plain English, name the tools you actually called, and explain WHY each capability matters for Qosina Finance.

- **vendor_invoice_precision_plastics.pdf** — Vendor invoice VINV-2026-001 from Precision Plastics Corp for $5,700, references PO-2026-001. Three line items (parts 11195, 99720, 99740) all match the seeded PO and receipt records exactly. Demonstrates the THREE-WAY MATCH HAPPY PATH: PO ↔ Receipt ↔ Invoice all agree, all-green, auto-approve eligible. Tools: get_vendor_invoices → three_way_match → create_approval.

- **vendor_invoice_techvalve_discrepancy.pdf** — TechValve International invoice VINV-2026-005 for 500 units of part 80071 ($1,975 total), references PO-2026-005. The receiving dock only logged 480 units actually received. Demonstrates QUANTITY VARIANCE detection in three-way matching — vendor billed for more than was received, system flags the 20-unit gap. Asks the human to investigate (short ship? damaged in transit? back-order?). Catches a real money leak.

- **vendor_invoice_sinomed_penny.pdf** — SinoMed Components invoice VINV-2026-002 for $2,250.03, references PO-2026-002. Variance from PO is THREE CENTS (rounding from $0.4501 × 5,000 units). Demonstrates TOLERANCE THRESHOLDS: under $0.05 should auto-clear with a write-off note rather than waste a human's time. Establishes the principle that the system has tolerance bands — under $0.05 auto-clears, $0.05–$50 quick review, over $50 full investigation.

- **vendor_invoice_allied_price_mismatch.pdf** — Allied Silicone Products invoice VINV-2026-004 for silicone tubing at $67.50/coil. The PO (PO-2026-004) was at $65.00/coil. Vendor included a note claiming "Q2 2026 price adjustment (+3.8%)". Demonstrates PRICE VARIANCE detection (as opposed to quantity variance) — system catches a ~$250 unauthorized price increase that a busy AP clerk might miss. Exactly the kind of leak that compounds across hundreds of invoices.

- **vendor_invoice_unknown_po.pdf** — MedSupply International invoice MSI-INV-8842 for $4,900, references PO-2025-999 which DOES NOT EXIST in the system. Demonstrates the orphan invoice case: AI cannot do three-way match because there's no PO to match against. Could be fraud, could be a legitimate order someone forgot to enter — either way the system refuses to pay until resolved. This is the safety story for Finance.

- **payment_remittance_medline.pdf** — Remittance advice from MedLine Innovations, check #7892 for $1,345. Customer is identified (CUST-003). Remittance says: $1,012.50 → invoice CINV-2026-006 (clean), $332.50 → invoice CINV-2026-007 (which is actually $337.50 — they short-paid by $5 with a note "deducted for damaged goods"). Demonstrates CASH APPLICATION with a partial payment / customer deduction. AI applies the math correctly AND flags that Qosina owes a $5 credit memo for the damaged goods.

- **bank_statement_mystery_payment.pdf** — First National Bank statement showing four transactions for Qosina's operating account. The flagged item is a $2,800 check (#4488) from "Unknown" — NO REMITTANCE ADVICE on file. Bank surfaces two possible matches: CUST-001 Acme Medical (open invoice $2,137.50) and CUST-005 Atlantic Bioprocess (open invoice $650). Combined = $2,787.50, off by $12.50. Demonstrates the HARDEST cash app case: judgment call escalation. AI proposes the split with low confidence, surfaces the candidates with the math, and kicks to a human for the phone call. This is the 30-minutes-per-occurrence problem AP clerks hate.

When asked to explain a document: name it, summarize what was unusual/interesting about it, list the actual tools you called (in order), describe what came back from each, and tie it to the business value for Qosina Finance. Don't read this reference verbatim — synthesize."""


@tool
def get_vendor_invoices() -> str:
    """Get all vendor invoices with their current match status.
    Use this to see which invoices need three-way matching."""
    return json.dumps(_get_vendor_invoices(), indent=2)


@tool
def three_way_match(invoice_id: str) -> str:
    """Run three-way match on a vendor invoice: compare invoice vs PO vs receipt.
    Shows line-by-line comparison with variances and recommendations.
    Use this when processing a specific vendor invoice."""
    return json.dumps(_three_way_match(invoice_id), indent=2)


@tool
def get_unapplied_payments() -> str:
    """Get all unapplied customer payments that need cash application.
    Use this to see which payments need to be matched to invoices."""
    return json.dumps(_get_unapplied_payments(), indent=2)


@tool
def match_payment(payment_id: str) -> str:
    """Try to match an unapplied payment against open customer invoices.
    Returns suggested matches with confidence scores and allocation details.
    Use this when processing a specific customer payment."""
    return json.dumps(_match_payment(payment_id), indent=2)


@tool
def score_collections() -> str:
    """Score and rank all overdue customer accounts for collections prioritization.
    Returns customers ranked by risk score with reasoning and recommended actions.
    Use this when analyzing which overdue accounts to pursue first."""
    return json.dumps(_score_collections(), indent=2)


@tool
def create_approval(recommendation_type: str, title: str, content: str, structured_data: str = "") -> str:
    """Submit an AP recommendation for human review.
    Types: 'invoice_match', 'payment_application', 'collection_outreach'.

    IMPORTANT: You MUST pass structured_data as a JSON string with editable fields and confidence scores.

    For invoice_match:
    {"fields": {"invoice_id": {"value": "...", "confidence": 0.99, "label": "Invoice"}, "vendor_name": {...}, "po_number": {...}, "match_status": {...}, "recommendation": {...}},
     "line_items": [{"item_id": "...", "description": "...", "qty_ordered": 500, "qty_received": 480, "qty_invoiced": 500, "unit_price": 3.95, "status": "discrepancy", "confidence": 0.99}],
     "total_variance": 0.00}

    For payment_application:
    {"fields": {"payment_id": {...}, "customer_name": {...}, "payment_amount": {...}, "match_type": {...}},
     "allocations": [{"invoice_id": "...", "invoice_amount": 1012.50, "applied_amount": 1012.50, "confidence": 0.95}]}

    For collection_outreach:
    {"fields": {"customer_id": {...}, "customer_name": {...}, "total_overdue": {...}, "days_overdue": {...}, "priority": {...}, "recommended_action": {...}}}"""
    return json.dumps(_create_approval(recommendation_type, title, content, structured_data=structured_data), indent=2)


TOOLS = [get_vendor_invoices, three_way_match, get_unapplied_payments, match_payment, score_collections, create_approval]


def create_uc2_agent():
    """Create and return the UC2 AP Processing agent."""
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
