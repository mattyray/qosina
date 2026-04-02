"""Pure tool functions for UC3: New Product Data Entry. No LangGraph dependency."""

from backend.database import get_db


def get_naming_conventions() -> dict:
    """Return all Qosina naming convention rules (the constitutional framework)."""
    with get_db() as conn:
        rows = conn.execute("SELECT * FROM naming_conventions ORDER BY field_name").fetchall()

    rules_by_field = {}
    for r in rows:
        field = r["field_name"]
        if field not in rules_by_field:
            rules_by_field[field] = []
        rules_by_field[field].append({
            "RuleType": r["rule_type"],
            "Pattern": r["pattern"],
            "ExampleCorrect": r["example_correct"],
            "ExampleIncorrect": r["example_incorrect"],
        })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#NamingConventions",
        "value": rules_by_field,
        "TotalRules": sum(len(v) for v in rules_by_field.values()),
    }


def find_similar_products(category: str = "", material: str = "", connection_type: str = "") -> dict:
    """Find existing products similar to a new entry for consistency checking."""
    with get_db() as conn:
        conditions = []
        params = []

        if category:
            conditions.append("p.category LIKE ?")
            params.append(f"%{category}%")
        if material:
            conditions.append("p.material LIKE ?")
            params.append(f"%{material}%")
        if connection_type:
            conditions.append("p.connection_type LIKE ?")
            params.append(f"%{connection_type}%")

        where = " AND ".join(conditions) if conditions else "1=1"

        rows = conn.execute(f"""
            SELECT p.*, pe.inner_diameter_mm, pe.outer_diameter_mm, pe.length_mm,
                   pe.weight_g, pe.color, pe.sterilization_compatibility,
                   pe.country_of_origin
            FROM products p
            LEFT JOIN product_extended pe ON p.item_id = pe.item_id
            WHERE {where}
            ORDER BY p.category, p.item_id
            LIMIT 10
        """, params).fetchall()

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#SimilarProducts",
        "SearchCriteria": {
            "Category": category,
            "Material": material,
            "ConnectionType": connection_type,
        },
        "value": [
            {
                "ItemId": r["item_id"],
                "ProductName": r["product_name"],
                "Category": r["category"],
                "Material": r["material"],
                "ConnectionType": r["connection_type"],
                "TechnicalDetail": r["technical_detail"],
                "ISOCompliance": r["iso_compliance"],
                "UnitPrice": r["unit_price"],
                "InnerDiameterMm": r["inner_diameter_mm"],
                "OuterDiameterMm": r["outer_diameter_mm"],
                "LengthMm": r["length_mm"],
                "WeightG": r["weight_g"],
                "Color": r["color"],
                "SterilizationCompatibility": r["sterilization_compatibility"],
                "CountryOfOrigin": r["country_of_origin"],
            }
            for r in rows
        ],
        "TotalFound": len(rows),
    }


def validate_consistency(new_fields: dict) -> dict:
    """
    Validate a new product entry against naming conventions and existing catalog patterns.
    Input: dict with field names as keys (e.g., 'product_name', 'material', 'category', 'connection_type').
    """
    issues = []
    warnings = []
    passed = []

    with get_db() as conn:
        conventions = conn.execute("SELECT * FROM naming_conventions").fetchall()

        # Check each field against naming conventions
        for conv in conventions:
            field = conv["field_name"]
            if field not in new_fields:
                continue

            value = new_fields[field]
            correct = conv["example_correct"]
            incorrect = conv["example_incorrect"]

            if conv["rule_type"] == "full_name_with_abbrev":
                # Check material format: "Full Name (ABBREV)"
                if "(" not in str(value) and field == "material":
                    issues.append({
                        "Field": field,
                        "Value": value,
                        "Rule": conv["pattern"],
                        "Expected": correct,
                        "Severity": "error",
                        "Message": f"Material '{value}' should include full name with abbreviation, e.g., '{correct}'",
                    })
                else:
                    passed.append({"Field": field, "Value": value, "Rule": conv["rule_type"]})

            elif conv["rule_type"] == "iso_terminology":
                # Check connection type capitalization and format
                if value and value == value.lower():
                    issues.append({
                        "Field": field,
                        "Value": value,
                        "Rule": conv["pattern"],
                        "Expected": correct,
                        "Severity": "error",
                        "Message": f"Connection type '{value}' must use ISO terminology, e.g., '{correct}'",
                    })
                else:
                    passed.append({"Field": field, "Value": value, "Rule": conv["rule_type"]})

            elif conv["rule_type"] == "millimeters":
                # Check dimension units
                if value and ('"' in str(value) or "inch" in str(value).lower()):
                    issues.append({
                        "Field": field,
                        "Value": value,
                        "Rule": conv["pattern"],
                        "Expected": correct,
                        "Severity": "error",
                        "Message": f"Dimension '{value}' must be in millimeters, e.g., '{correct}'",
                    })
                else:
                    passed.append({"Field": field, "Value": value, "Rule": conv["rule_type"]})

            elif conv["rule_type"] == "qosina_taxonomy":
                # Check if category exists
                existing = conn.execute(
                    "SELECT DISTINCT category FROM products WHERE category LIKE ?",
                    (f"%{value}%",)
                ).fetchone()
                if not existing and value:
                    warnings.append({
                        "Field": field,
                        "Value": value,
                        "Rule": conv["pattern"],
                        "Expected": correct,
                        "Severity": "warning",
                        "Message": f"Category '{value}' not found in existing catalog. Closest: '{correct}'",
                    })
                else:
                    passed.append({"Field": field, "Value": value, "Rule": conv["rule_type"]})

        # Check consistency with existing similar products
        category = new_fields.get("category", "")
        material = new_fields.get("material", "")
        if category:
            similar = conn.execute("""
                SELECT DISTINCT material FROM products WHERE category LIKE ?
            """, (f"%{category}%",)).fetchall()
            existing_materials = [r["material"] for r in similar]

            if material and existing_materials:
                # Check if this material is used in this category
                if not any(material.lower() in m.lower() for m in existing_materials):
                    warnings.append({
                        "Field": "material",
                        "Value": material,
                        "Rule": "consistency_check",
                        "Expected": ", ".join(existing_materials[:3]),
                        "Severity": "warning",
                        "Message": f"Material '{material}' is uncommon for {category}. Existing materials: {', '.join(existing_materials[:3])}",
                    })

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#ConsistencyValidation",
        "InputFields": new_fields,
        "Issues": issues,
        "Warnings": warnings,
        "Passed": passed,
        "Summary": {
            "TotalChecks": len(issues) + len(warnings) + len(passed),
            "Errors": len(issues),
            "Warnings": len(warnings),
            "Passed": len(passed),
            "OverallStatus": "fail" if issues else "review" if warnings else "pass",
        },
    }


def get_sample_spec_sheets() -> dict:
    """Return sample supplier spec sheet documents for demo purposes."""
    samples = [
        {
            "id": "sample_spec_1",
            "title": "Precision Plastics \u2014 New Stopcock",
            "description": "Clean spec sheet for a new stopcock variant \u2014 tests naming convention normalization",
            "text": """SUPPLIER SPECIFICATION SHEET

Vendor: Precision Plastics Corp
Part: SP-NEW-4401
Description: 3-way valve, luer type, PC material

Specifications:
- Type: Three-way valve with luer connections
- Material: PC plastic
- Connections: M Luer Lock x F Luer Lock x F Luer Lock
- Bore Size: 0.106" (2.69mm)
- Max Pressure: 29 psi
- Handle: HDPE, white
- Seal: Silicone O-ring
- Manufacturing: Clean room (ISO Class 8)
- Sterilization: Gamma and EtO compatible
- Shelf Life: 60 months (36 months post-irradiation)
- Compliance: ISO 80369-7

Dimensions:
- Overall Length: 1.5" (38.1mm)
- OD: 0.19" (4.83mm)
- ID: 0.106" (2.69mm)
- Weight: 8.5g

Origin: China
Lead Time: 45 days
MOQ: 5,000 units
Unit Cost: $1.85
Units per case: 100"""
        },
        {
            "id": "sample_spec_2",
            "title": "Allied Silicone \u2014 Platinum-Cured Tubing",
            "description": "Tubing spec sheet with imperial measurements \u2014 tests unit conversion",
            "text": """PRODUCT DATA SHEET

Allied Silicone Products
Catalog #: ASP-T5050

Platinum-Cured Silicone Tubing, 50A Durometer

Specifications:
- Material: Medical-grade silicone rubber
- Durometer: 50A Shore
- Inner Diameter: 3/16 inch
- Outer Diameter: 5/16 inch
- Wall Thickness: 1/16 inch
- Tensile Strength: 1,200 psi
- Elongation: 400%
- Color: Translucent
- Biocompatibility: USP Class VI, ISO 10993
- Sterilization: Autoclave, Gamma, EtO
- Temperature Range: -60C to +200C
- Coil Length: 50 feet

Packaging: 50 ft coils
Country of Origin: United States
Lead Time: 14-21 days
Certification: FDA compliant, USP Class VI
Tariff Code: 3917.40"""
        },
        {
            "id": "sample_spec_3",
            "title": "EuroFlex Medical \u2014 Hydrophilic Filter",
            "description": "European supplier with metric measurements \u2014 well-formatted spec sheet",
            "text": """TECHNISCHES DATENBLATT / TECHNICAL DATA SHEET

EuroFlex Medical GmbH
Product: Hydrophilic Membrane Filter
Model: EFM-HF-022-LL

Technical Specifications:
- Filter Media: Polyethersulfone (PES)
- Pore Size: 0.22 micron
- Housing Material: ABS
- Inlet Connection: Female Luer Lock
- Outlet Connection: Male Luer Lock
- Effective Filtration Area: 4.5 cm2
- Maximum Pressure: 4.0 bar (58 psi)
- Priming Volume: 0.5 mL
- Flow Rate (water): >40 mL/min at 1 bar

Dimensions:
- Overall Length: 58.0mm
- Maximum Diameter: 22.0mm
- Weight: 16.0g

Regulatory:
- ISO 80369-7 compliant
- ISO 13485 manufactured
- CE marked (MDR 2017/745)
- Biocompatibility per ISO 10993-1

Sterilization: Gamma irradiation, EtO
Shelf Life: 60 months
Country of Origin: Germany
MOQ: 500 units
Unit Price: EUR 2.80"""
        },
    ]

    return {
        "@odata.context": "https://qosina.operations.dynamics.com/data/$metadata#SampleSpecSheets",
        "value": samples,
        "TotalSamples": len(samples),
    }
