# tests/test_sales_order_builder.py

import pytest
from easy_acumatica.models.sales_order_builder import SalesOrderBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        SalesOrderBuilder()
        .customer_id("GOODFOOD")
        .order_type("SO")
        .hold(False)
    )
    payload = builder.to_body()
    assert payload["CustomerID"]["value"] == "GOODFOOD"
    assert payload["OrderType"]["value"] == "SO"
    assert payload["Hold"]["value"] is False

def test_builder_details():
    """Tests adding detail lines."""
    builder = SalesOrderBuilder().add_detail(
        InventoryID="APJAM08",
        OrderQty=2
    )
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["InventoryID"]["value"] == "APJAM08"

def test_builder_payments():
    """Tests adding payments."""
    builder = SalesOrderBuilder().add_payment(
        PaymentAmount=980.00,
        PaymentMethod="ACUPAYCC"
    )
    payload = builder.to_body()
    assert "Payments" in payload
    assert len(payload["Payments"]) == 1
    assert payload["Payments"][0]["PaymentAmount"]["value"] == 980.00

def test_builder_tax_details():
    """Tests adding tax details."""
    builder = SalesOrderBuilder().add_tax_detail(
        TaxID="NYSTATETAX",
        TaxAmount=0.5
    )
    payload = builder.to_body()
    assert "TaxDetails" in payload
    assert len(payload["TaxDetails"]) == 1
    assert payload["TaxDetails"][0]["TaxID"]["value"] == "NYSTATETAX"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = SalesOrderBuilder().customer_id("Test")
    body1 = builder.to_body()
    body1["CustomerID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["CustomerID"]["value"] == "Test"