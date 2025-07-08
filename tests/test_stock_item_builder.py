# tests/test_stock_item_builder.py

import pytest
from easy_acumatica.models.stock_item_builder import StockItemBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        StockItemBuilder()
        .inventory_id("BASESERV1")
        .description("Baseline level of performance")
        .item_class("STOCKITEM")
    )
    payload = builder.to_body()
    assert payload["InventoryID"]["value"] == "BASESERV1"
    assert payload["Description"]["value"] == "Baseline level of performance"
    assert payload["ItemClass"]["value"] == "STOCKITEM"
    
def test_builder_note():
    """Tests setting a note."""
    builder = StockItemBuilder().note("My note")
    payload = builder.to_body()
    assert payload["note"]["value"] == "My note"

def test_builder_attributes():
    """Tests adding attributes."""
    builder = (
        StockItemBuilder()
        .add_attribute("Operation System", "Windows")
        .add_attribute("SOFTVER", "Server 2012 R2")
    )
    payload = builder.to_body()
    assert "Attributes" in payload
    assert len(payload["Attributes"]) == 2
    assert payload["Attributes"][0]["AttributeID"]["value"] == "Operation System"
    assert payload["Attributes"][1]["Value"]["value"] == "Server 2012 R2"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = StockItemBuilder().inventory_id("Test")
    body1 = builder.to_body()
    body1["InventoryID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["InventoryID"]["value"] == "Test"