# tests/test_case_builder.py

import pytest
from easy_acumatica.models.case_builder import CaseBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        CaseBuilder()
        .class_id("JREPAIR")
        .business_account("ABAKERY")
        .contact_id("100211")
        .subject("Some Subject")
    )
    payload = builder.to_body()
    assert payload["ClassID"]["value"] == "JREPAIR"
    assert payload["BusinessAccount"]["value"] == "ABAKERY"
    assert payload["ContactID"]["value"] == "100211"
    assert payload["Subject"]["value"] == "Some Subject"

def test_builder_related_cases():
    """Tests adding related cases."""
    builder = CaseBuilder().add_related_case("000004")
    payload = builder.to_body()
    assert "RelatedCases" in payload
    assert payload["RelatedCases"][0]["CaseID"]["value"] == "000004"

def test_builder_custom_fields():
    """Tests setting custom fields."""
    builder = CaseBuilder().set_custom_field(
        "Case", "AttributeMODEL", "JUICER15:Commercial juicer with a prod rate of 1.5 l per min"
    )
    payload = builder.to_body()
    assert "custom" in payload
    assert payload["custom"]["Case"]["AttributeMODEL"]["value"] == "JUICER15:Commercial juicer with a prod rate of 1.5 l per min"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = CaseBuilder().subject("Test")
    body1 = builder.to_body()
    body1["Subject"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["Subject"]["value"] == "Test"