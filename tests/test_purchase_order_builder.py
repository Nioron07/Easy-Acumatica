# tests/test_purchase_order_builder.py

import pytest
from easy_acumatica.models.purchase_order_builder import PurchaseOrderBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        PurchaseOrderBuilder()
        .vendor_id("GOODFRUITS")
        .location("MAIN")
        .hold(False)
    )
    payload = builder.to_body()
    assert payload["VendorID"]["value"] == "GOODFRUITS"
    assert payload["Location"]["value"] == "MAIN"
    assert payload["Hold"]["value"] is False

def test_builder_details():
    """Tests adding detail lines."""
    builder = PurchaseOrderBuilder().add_detail(
        BranchID="HEADOFFICE",
        InventoryID="APPLES",
        OrderQty=1,
        WarehouseID="WHOLESALE",
        UOM="LB"
    )
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["InventoryID"]["value"] == "APPLES"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = PurchaseOrderBuilder().vendor_id("Test")
    body1 = builder.to_body()
    body1["VendorID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["VendorID"]["value"] == "Test"