"""LangGraph ReAct agent for UC1: Sales Order Entry from Emails & Documents."""

import json
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from backend.shared.llm_provider import get_model
from backend.use_case_1.tools import (
    match_customer as _match_customer,
    match_products as _match_products,
    validate_pricing as _validate_pricing,
    get_sample_pos as _get_sample_pos,
)
from backend.tools import (
    check_inventory as _check_inventory,
    create_approval as _create_approval,
)

SYSTEM_PROMPT = """You are a Qosina Sales Order Entry AI Assistant. Your job is to process purchase orders (POs) and convert them into structured sales orders for human review.

=== YOUR WORKFLOW ===
When a user pastes or describes a PO document:

1. **Parse the document** — Extract: customer name, contact, PO number, line items (part numbers, descriptions, quantities, prices), ship-to address, delivery date, payment terms.

2. **Match the customer** — Use match_customer to find the customer in Qosina's master data. Report confidence score.

3. **Match the products** — Use match_products with the extracted line items. Each line gets fuzzy matched against the 5,000+ SKU catalog. Report confidence per line.

4. **Validate pricing** — Use validate_pricing to compare PO prices against contracted rates and catalog prices. Flag any mismatches.

5. **Check inventory** — Use check_inventory for each matched product to confirm availability.

6. **Create an approval** — Use create_approval to submit the structured sales order for human review. Include all matched data, confidence scores, and any flags.

=== CONFIDENCE SCORING ===
- 95%+ = exact match (part number found, customer ID confirmed)
- 80-94% = high confidence fuzzy match (strong description match)
- 60-79% = medium confidence (partial match, verify with human)
- Below 60% = low confidence (flag for full human review)

=== RULES ===
1. ALWAYS cite specific part numbers in your response.
2. NEVER skip the matching step — even if part numbers look correct, verify them against the catalog.
3. Flag new customers (not in the system) clearly — they need to be set up before an order can be created.
4. Flag pricing discrepancies — if the PO price differs from contracted or catalog price, note the variance.
5. Create ONE approval per sales order (not per line item).
6. Keep approvals concise: customer, PO#, line count, total, and any flags.
7. If the user asks for sample POs, use get_sample_pos to show available demo documents.

=== APPROVAL FORMAT ===
Type: 'sales_order'
Title: "Sales Order — [Customer Name] — PO#[number]"
Content: Brief summary with line items, total, and any flags.

=== ABOUT QOSINA ===
Qosina is a medical device component distributor (Ronkonkoma, NY). 5,000+ OEM single-use components. ISO 13485 certified. All parts may end up in medical devices — accuracy is critical."""


@tool
def match_customer(name: str = "", email: str = "", po_reference: str = "") -> str:
    """Match a customer name, email, or PO reference against Qosina's customer master data.
    Returns ranked matches with confidence scores. Use this first when processing a PO."""
    return json.dumps(_match_customer(name, email, po_reference), indent=2)


@tool
def match_products(descriptions: list[dict]) -> str:
    """Match product descriptions and/or part numbers against the Qosina catalog.
    Input: list of dicts, each with optional keys: 'description', 'part_number', 'quantity', 'unit_price'.
    Returns matched products with confidence scores per line."""
    return json.dumps(_match_products(descriptions), indent=2)


@tool
def validate_pricing(customer_id: str, line_items: list[dict]) -> str:
    """Validate pricing for a customer's order against contracted rates and catalog prices.
    Input line_items: list of dicts with 'item_id', 'unit_price', 'quantity'.
    Flags mismatches, shows expected vs requested pricing."""
    return json.dumps(_validate_pricing(customer_id, line_items), indent=2)


@tool
def check_inventory(part_number: str) -> str:
    """Check stock availability for a specific part number.
    Returns lot-level inventory with quantities and warehouse locations."""
    return json.dumps(_check_inventory(part_number), indent=2)


@tool
def create_approval(recommendation_type: str, title: str, content: str) -> str:
    """Submit the structured sales order for human review in the approval queue.
    Type should be 'sales_order'. Include customer, PO#, line items summary, total, and any flags."""
    return json.dumps(_create_approval(recommendation_type, title, content), indent=2)


@tool
def get_sample_pos() -> str:
    """Get sample purchase order documents for demo purposes.
    Returns 3 sample POs with varying complexity (known customer, fuzzy descriptions, new customer)."""
    return json.dumps(_get_sample_pos(), indent=2)


TOOLS = [match_customer, match_products, validate_pricing, check_inventory, create_approval, get_sample_pos]


def create_uc1_agent():
    """Create and return the UC1 Sales Order Entry agent."""
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
