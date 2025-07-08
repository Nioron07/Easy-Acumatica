# tests/test_shipment_builder.py

import pytest
from easy_acumatica.models.shipment_builder import ShipmentBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        ShipmentBuilder()
        .type("Shipment")
        .customer_id("C000000003")
        .warehouse_id("MAIN")
    )
    payload = builder.to_body()
    assert payload["Type"]["value"] == "Shipment"
    assert payload["CustomerID"]["value"] == "C000000003"
    assert payload["WarehouseID"]["value"] == "MAIN"

def test_builder_details():
    """Tests adding detail lines."""
    builder = ShipmentBuilder().add_detail(
        OrderType="SO",
        OrderNbr="000004"
    )
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["OrderNbr"]["value"] == "000004"

def test_builder_packages():
    """Tests adding packages."""
    builder = ShipmentBuilder().add_package(
        BoxID="LARGE",
        Weight=15
    )
    payload = builder.to_body()
    assert "Packages" in payload
    assert len(payload["Packages"]) == 1
    assert payload["Packages"][0]["BoxID"]["value"] == "LARGE"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = ShipmentBuilder().type("Test")
    body1 = builder.to_body()
    body1["Type"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["Type"]["value"] == "Test"