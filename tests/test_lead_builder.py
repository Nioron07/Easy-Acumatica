# tests/models/test_lead_builder.py

import pytest
from easy_acumatica.models.lead_builder import LeadBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        LeadBuilder()
        .first_name("Brent")
        .last_name("Edds")
        .email("test@example.com")
    )
    payload = builder.to_body()
    assert payload["FirstName"]["value"] == "Brent"
    assert payload["LastName"]["value"] == "Edds"
    assert payload["Email"]["value"] == "test@example.com"

def test_builder_set_method():
    """Tests using the generic .set() method."""
    builder = LeadBuilder().set("CompanyName", "Avante Inc.")
    payload = builder.to_body()
    assert payload["CompanyName"]["value"] == "Avante Inc."

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = LeadBuilder().first_name("Test")
    body1 = builder.to_body()
    body1["FirstName"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["FirstName"]["value"] == "Test"
