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
Qosina is a medical device component distributor. AP processes hundreds of vendor invoices monthly. Finance team needs fast, accurate matching to maintain vendor relationships and cash flow."""


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
def create_approval(recommendation_type: str, title: str, content: str) -> str:
    """Submit an AP recommendation for human review.
    Types: 'invoice_match', 'payment_application', 'collection_outreach'.
    Keep content concise: key facts, variance, recommendation."""
    return json.dumps(_create_approval(recommendation_type, title, content), indent=2)


TOOLS = [get_vendor_invoices, three_way_match, get_unapplied_payments, match_payment, score_collections, create_approval]


def create_uc2_agent():
    """Create and return the UC2 AP Processing agent."""
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
