# tests/models/tax_category_builder.py

import pytest
from easy_acumatica.models.tax_category_builder import TaxCategoryBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        TaxCategoryBuilder()
        .active(True)
        .description("Test")
        .exclude_listed_taxes(False)
        .tax_category_id("Test_ID")
    )
    payload = builder.to_body()
    assert payload["Active"]["value"] == True
    assert payload["Description"]["value"] == "Test"
    assert payload["ExcludeListedTaxes"]["value"] == False
    assert payload["TaxCategoryID"]["value"] == "Test_ID"

def test_builder_set_method():
    """Tests using the generic .set() method."""
    builder = TaxCategoryBuilder().set("Description", "Test")
    payload = builder.to_body()
    assert payload["Description"]["value"] == "Test"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = TaxCategoryBuilder().description("Test")
    body1 = builder.to_body()
    body1["Description"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["Description"]["value"] == "Test"
