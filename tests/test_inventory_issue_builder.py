# tests/test_inventory_issue_builder.py

import pytest
from easy_acumatica.models.inventory_issue_builder import InventoryIssueBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        InventoryIssueBuilder()
        .date("2024-12-02T00:00:00+03:00")
        .description("Descr")
        .post_period("122024")
    )
    payload = builder.to_body()
    assert payload["Date"]["value"] == "2024-12-02T00:00:00+03:00"
    assert payload["Description"]["value"] == "Descr"
    assert payload["PostPeriod"]["value"] == "122024"

def test_builder_details():
    """Tests adding detail lines."""
    builder = InventoryIssueBuilder().add_detail(
        InventoryID="APJAM08",
        Qty=1,
        Warehouse="RETAIL"
    )
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["InventoryID"]["value"] == "APJAM08"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = InventoryIssueBuilder().description("Test")
    body1 = builder.to_body()
    body1["Description"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["Description"]["value"] == "Test"