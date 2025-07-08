# tests/test_item_warehouse_builder.py

import pytest
from easy_acumatica.models.item_warehouse_builder import ItemWarehouseBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        ItemWarehouseBuilder()
        .inventory_id("APPLES")
        .warehouse_id("RETAIL")
        .set("MaxQty", 2222)
    )
    payload = builder.to_body()
    assert payload["InventoryID"]["value"] == "APPLES"
    assert payload["WarehouseID"]["value"] == "RETAIL"
    assert payload["MaxQty"]["value"] == 2222

def test_builder_override_field():
    """Tests setting an override field."""
    builder = ItemWarehouseBuilder().override("MaxQty", True)
    payload = builder.to_body()
    assert payload["OverrideMaxQty"]["value"] is True

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = ItemWarehouseBuilder().inventory_id("Test")
    body1 = builder.to_body()
    body1["InventoryID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["InventoryID"]["value"] == "Test"