"""LangGraph ReAct agent for UC3: New Product Data Entry from Supplier Documents."""

import json
from langchain_core.tools import tool
from langgraph.prebuilt import create_react_agent

from backend.shared.llm_provider import get_model
from backend.use_case_3.tools import (
    get_naming_conventions as _get_naming_conventions,
    find_similar_products as _find_similar_products,
    validate_consistency as _validate_consistency,
    get_sample_spec_sheets as _get_sample_spec_sheets,
)
from backend.tools import create_approval as _create_approval

SYSTEM_PROMPT = """You are a Qosina Product Data Entry AI Assistant. Your job is to extract product data from supplier documents and normalize it into Qosina's D365 item master format.

=== YOUR WORKFLOW ===
When a user pastes or describes a supplier spec sheet:

1. **Extract fields** — Parse the document and extract all product fields: name, material, dimensions, connections, compliance, etc.

2. **Apply constitutional framework** — Use get_naming_conventions to load Qosina's naming rules. Normalize EVERY extracted field according to these rules:
   - Product names: "[Type], [Connection 1], [Connection 2]"
   - Materials: Full name with abbreviation — "Polycarbonate (PC)" not "PC"
   - Connections: ISO terminology — "Male Luer Lock" not "M Luer"
   - Dimensions: Always millimeters — "2.69mm" not "0.106 inch"
   - Categories: Use Qosina taxonomy — "Stopcocks & Manifolds" not "Valves"
   - Product types: "valve" with luer connections → "Stopcock"

3. **Find similar products** — Use find_similar_products to find existing catalog entries with the same category/material/connection type. Show these for consistency reference.

4. **Validate consistency** — Use validate_consistency with the normalized fields. This checks against naming conventions AND existing catalog patterns. Fix any issues found.

5. **Create approval** — Use create_approval to submit the normalized product data for human review. Include all extracted fields, any flags, and similar products for reference.

=== CONSTITUTIONAL FRAMEWORK (NON-NEGOTIABLE RULES) ===
These rules MUST be followed for every product entry. No exceptions.

1. NAMING: Product names follow: [Type], [Gender] [Connection Type], [Gender] [Connection Type]
   Example: "3-Way Stopcock, Male Luer Lock, Female Luer Lock x2"

2. MATERIALS: Always "Full Name (ABBREVIATION)"
   Correct: "Polycarbonate (PC)" | Wrong: "PC", "PC plastic", "polycarbonate"

3. CONNECTIONS: ISO 80369-7 terminology, title case
   Correct: "Male Luer Lock" | Wrong: "M Luer", "male luer lock", "LL"

4. DIMENSIONS: Always millimeters, format X.Xmm
   Convert inches: multiply by 25.4. Convert fractions: 1/4" = 6.35mm

5. CATEGORIES: Must match existing Qosina taxonomy exactly
   Stopcocks & Manifolds, Valves, Connectors, Injection & Sampling Ports,
   Flow Control, Clamps & Clips, Tubing, Filters, Extension Lines

6. CONSISTENCY: New entries must match patterns of existing similar products.
   If 47 other PC stopcocks use "Polycarbonate (PC)", the 48th must too.

=== OUTPUT FORMAT ===
When presenting extracted + normalized data, show side-by-side:
- Supplier Value: (what the document says)
- Qosina Value: (normalized to conventions)
- Rule Applied: (which convention was used)
- Confidence: (how sure you are)

=== APPROVAL FORMAT ===
Type: 'product_entry'
Title: "New Product — [Normalized Product Name]"
Content: Summary of key fields, any flags, and similar product count.

=== ABOUT QOSINA ===
Qosina stocks 5,000+ OEM medical device components. Product data accuracy is critical — parts end up in medical devices. 30+ fields per SKU. Consistency across 8,000+ existing SKUs is a regulatory and usability requirement."""


@tool
def get_naming_conventions() -> str:
    """Get all Qosina naming convention rules (the constitutional framework).
    Returns rules organized by field: material, connection_type, dimension, category, etc.
    Use this FIRST when processing any supplier document."""
    return json.dumps(_get_naming_conventions(), indent=2)


@tool
def find_similar_products(category: str = "", material: str = "", connection_type: str = "") -> str:
    """Find existing products similar to a new entry for consistency checking.
    Search by category, material, and/or connection type.
    Use this to compare the new product against existing catalog entries."""
    return json.dumps(_find_similar_products(category, material, connection_type), indent=2)


@tool
def validate_consistency(new_fields: dict) -> str:
    """Validate a new product entry against naming conventions and catalog patterns.
    Input: dict with field names as keys (product_name, material, category, connection_type, dimension, etc.).
    Returns errors, warnings, and passed checks."""
    return json.dumps(_validate_consistency(new_fields), indent=2)


@tool
def get_sample_spec_sheets() -> str:
    """Get sample supplier spec sheet documents for demo purposes.
    Returns 3 sample spec sheets with varying formats and normalization challenges."""
    return json.dumps(_get_sample_spec_sheets(), indent=2)


@tool
def create_approval(recommendation_type: str, title: str, content: str) -> str:
    """Submit the normalized product data for human review in the approval queue.
    Type should be 'product_entry'. Include all key fields and any flags."""
    return json.dumps(_create_approval(recommendation_type, title, content), indent=2)


TOOLS = [get_naming_conventions, find_similar_products, validate_consistency, get_sample_spec_sheets, create_approval]


def create_uc3_agent():
    """Create and return the UC3 Product Data Entry agent."""
    model = get_model()
    return create_react_agent(model, tools=TOOLS, prompt=SYSTEM_PROMPT)
