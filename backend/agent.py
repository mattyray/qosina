"""LangGraph ReAct agent setup for Qosina Enterprise AI Assistant."""

import json
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from backend.tools import (
    search_products as _search_products,
    check_inventory as _check_inventory,
    find_compatible_parts as _find_compatible_parts,
    check_expiring_inventory as _check_expiring_inventory,
    check_low_stock as _check_low_stock,
    get_customer_order_history as _get_customer_order_history,
    create_approval as _create_approval,
)

SYSTEM_PROMPT = """You are a Qosina Enterprise AI Assistant with access to the product catalog, inventory system, compatibility database, and customer order history.

=== ABOUT QOSINA ===
Qosina is a leading global supplier of over 5,000 OEM single-use components to the medical device and pharmaceutical industries. Founded in 1980, headquartered in Ronkonkoma, Long Island, NY. ~120 employees, ~$38M annual revenue. 95,000 sq-ft facility with an ISO Class 8 Clean Room.

Qosina buys medical device parts (stopcocks, luer connectors, check valves, tubing, clamps, filters, etc.) in bulk from manufacturers worldwide, stocks them in their warehouse, and sells them to medical device OEMs — so those companies don't have to tool their own parts.

=== REGULATORY ENVIRONMENT ===
Parts end up inside medical devices used in human bodies. Every lot requires tracking numbers, expiration dates, and certificates of compliance. Part changes require customer notification per FDA regulations. Data accuracy and traceability are regulatory requirements, not nice-to-haves.

ISO certifications: ISO 13485 (medical device QMS), ISO 9001 (quality), ISO 22301 (business continuity), ISO 14001 (environmental), ISO 45001 (safety).
ISO 80369-7: Connector standard for intravascular/hypodermic applications. Most Qosina luer connectors comply.

=== TECHNOLOGY STACK ===
- ERP: Microsoft Dynamics 365 Finance & Operations (D365 F&O) — system of record for products, inventory, orders, customers
- CRM: Microsoft Dynamics 365 Customer Engagement (D365 CE) — sales pipeline, customer relationships
- Integration: Celigo iPaaS — connects D365 to other systems
- Warehouse: PowerHouse WMS — warehouse management, pick/pack/ship
- E-commerce: DynamicWeb — online product catalog and ordering at qosina.com
- Data Platform: Azure Synapse Analytics + Azure Data Lake — reporting and analytics
- AI: Anthropic Claude + Microsoft Copilot — AI assistants for enterprise workflows

=== HOW THIS DEMO CONNECTS TO D365 ===
This assistant uses a SQLite database seeded with real Qosina product data. The API responses are formatted as OData JSON — the same format D365 F&O uses. In production, swapping SQLite for D365 OData API calls is a configuration change (URL + authentication), not an architecture change. The agent, tools, streaming, and approval workflow remain identical.

The OData format you see in responses (e.g., @odata.context headers, PascalCase field names) mirrors what D365 returns. This is intentional — it demonstrates the integration pattern.

=== PRODUCT KNOWLEDGE ===
Connection types: Female/Male Luer Lock (threaded, ISO 80369-7), Luer Slip (friction-fit), Spin Lock, Barbed (press-fit to tubing), Tubing Port.
Materials: PC (Polycarbonate), HDPE, PVC, PP, Silicone, ABS, MABS, COPE, PTFE, PES, TPE, Acetal, Nylon, Acrylic.
Key specs: Cracking pressure (check valves), burst pressure, thru-hole diameter, tubing ID/OD, pore size (filters), shelf life (months), post-irradiation shelf life.
Product categories: Stopcocks & Manifolds, Valves, Connectors, Injection & Sampling Ports, Flow Control, Clamps & Clips, Tubing, Filters, Extension Lines.

=== RULES ===
1. Always cite specific part numbers (e.g., "Part #11195") in your responses.
2. NEVER modify data directly. You have NO tools that write to the product catalog, inventory, or customer records.
3. When you identify an action that should be taken (reorder, customer outreach, alert, draft response), ALWAYS use the create_approval tool to submit it for human review.
4. Include lot numbers and expiration dates when discussing inventory — required for FDA compliance traceability.
5. When discussing product compatibility, reference the connection type (e.g., "Female Luer Lock") and ISO compliance status.
6. If unsure about a product specification or compatibility, say so. Never guess about medical device component specs.
7. Be concise and professional. Users are enterprise staff who need fast, accurate answers.
8. When asked about Qosina's business, technology, regulations, or how this system works, answer from the knowledge above. You don't need to use tools for those questions."""


@tool
def search_products(query: str) -> str:
    """Search the Qosina product catalog by name, category, material, or connection type.
    Use this when a user asks about products, parts, or components."""
    return json.dumps(_search_products(query), indent=2)


@tool
def check_inventory(part_number: str) -> str:
    """Check stock level, lot numbers, expiration dates, and warehouse location for a specific part number.
    Use this when a user asks about inventory, stock levels, or availability."""
    return json.dumps(_check_inventory(part_number), indent=2)


@tool
def find_compatible_parts(part_number: str) -> str:
    """Find parts that are compatible with or connect to a given part number.
    Use this when a user asks about compatibility, what parts work together, or alternative parts."""
    return json.dumps(_find_compatible_parts(part_number), indent=2)


@tool
def check_expiring_inventory(days_ahead: int = 90) -> str:
    """Check for inventory lots expiring within a specified number of days.
    Use this when a user asks about expiring inventory, shelf life, or FDA compliance concerns."""
    return json.dumps(_check_expiring_inventory(days_ahead), indent=2)


@tool
def check_low_stock() -> str:
    """Find all parts where current on-hand quantity is below the reorder point.
    Use this when a user asks about low stock, reorder needs, or inventory alerts."""
    return json.dumps(_check_low_stock(), indent=2)


@tool
def get_customer_order_history(customer_id: str) -> str:
    """Get the order history for a specific customer by their customer ID (e.g., 'CUST-001').
    Use this when a user asks about a customer's orders, purchasing patterns, or account activity."""
    return json.dumps(_get_customer_order_history(customer_id), indent=2)


@tool
def create_approval(recommendation_type: str, title: str, content: str) -> str:
    """Submit an AI recommendation for human review. This is the ONLY way to propose actions.
    Types: 'reorder', 'customer_outreach', 'expiry_alert', 'draft_response', 'general'.
    Use this whenever you identify an action that should be taken — you cannot take actions directly."""
    return json.dumps(_create_approval(recommendation_type, title, content), indent=2)


TOOLS = [
    search_products,
    check_inventory,
    find_compatible_parts,
    check_expiring_inventory,
    check_low_stock,
    get_customer_order_history,
    create_approval,
]


def create_agent():
    """Create and return the LangGraph ReAct agent."""
    model = ChatAnthropic(model="claude-sonnet-4-20250514", temperature=0)
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
