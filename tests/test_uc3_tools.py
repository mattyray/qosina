"""Unit tests for UC3: Product Data Entry tools."""

import pytest
import os
from backend.database import init_db, get_db, DB_PATH
from backend.seed import seed
from backend.use_case_3.tools import (
    get_naming_conventions,
    find_similar_products,
    validate_consistency,
    get_sample_spec_sheets,
)


@pytest.fixture(autouse=True, scope="module")
def setup_db():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    seed()
    yield
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)


class TestGetNamingConventions:
    def test_returns_rules(self):
        result = get_naming_conventions()
        assert result["TotalRules"] > 0
        assert "material" in result["value"]
        assert "connection_type" in result["value"]
        assert "dimension" in result["value"]
        assert "category" in result["value"]

    def test_material_rules(self):
        result = get_naming_conventions()
        material_rules = result["value"]["material"]
        assert len(material_rules) >= 1
        # All material rules should have correct/incorrect examples
        for rule in material_rules:
            assert rule["ExampleCorrect"] is not None
            assert rule["ExampleIncorrect"] is not None


class TestFindSimilarProducts:
    def test_by_category(self):
        result = find_similar_products(category="Stopcocks")
        assert result["TotalFound"] >= 1
        for p in result["value"]:
            assert "Stopcock" in p["Category"]

    def test_by_material(self):
        result = find_similar_products(material="PC")
        assert result["TotalFound"] >= 1

    def test_by_connection_type(self):
        result = find_similar_products(connection_type="Male Luer Lock")
        assert result["TotalFound"] >= 1

    def test_combined_search(self):
        result = find_similar_products(category="Stopcocks", material="PC")
        assert result["TotalFound"] >= 1

    def test_no_match(self):
        result = find_similar_products(category="Nonexistent Category XYZ")
        assert result["TotalFound"] == 0

    def test_includes_extended_fields(self):
        result = find_similar_products(category="Stopcocks")
        # Some stopcocks have extended data
        has_extended = any(p["InnerDiameterMm"] is not None for p in result["value"])
        assert has_extended


class TestValidateConsistency:
    def test_correct_entry_passes(self):
        result = validate_consistency({
            "material": "Polycarbonate (PC)",
            "connection_type": "Male Luer Lock",
            "category": "Stopcocks & Manifolds",
        })
        assert result["Summary"]["Errors"] == 0

    def test_bad_material_format(self):
        result = validate_consistency({
            "material": "PC",
        })
        assert result["Summary"]["Errors"] >= 1
        assert any("material" in i["Field"].lower() for i in result["Issues"])

    def test_bad_connection_case(self):
        result = validate_consistency({
            "connection_type": "male luer lock",
        })
        assert result["Summary"]["Errors"] >= 1

    def test_inch_dimensions_flagged(self):
        result = validate_consistency({
            "dimension": '0.106"',
        })
        assert result["Summary"]["Errors"] >= 1
        assert any("millimeters" in i["Message"].lower() for i in result["Issues"])

    def test_unknown_category_warned(self):
        result = validate_consistency({
            "category": "Widgets",
        })
        assert result["Summary"]["Warnings"] >= 1

    def test_overall_status(self):
        # Pass
        r1 = validate_consistency({"material": "Polycarbonate (PC)"})
        assert r1["Summary"]["OverallStatus"] in ("pass", "review")

        # Fail
        r2 = validate_consistency({"material": "PC"})
        assert r2["Summary"]["OverallStatus"] == "fail"


class TestGetSampleSpecSheets:
    def test_returns_samples(self):
        result = get_sample_spec_sheets()
        assert result["TotalSamples"] == 3
        assert len(result["value"]) == 3

    def test_sample_content(self):
        result = get_sample_spec_sheets()
        for s in result["value"]:
            assert "id" in s
            assert "title" in s
            assert "text" in s
            assert len(s["text"]) > 100
