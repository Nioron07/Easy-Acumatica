import pytest
from easy_acumatica.models.purchase_receipt_builder import PurchaseReceiptBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        PurchaseReceiptBuilder()
        .vendor_id("GOODFRUITS")
        .type("Receipt")
        .hold(False)
    )
    payload = builder.to_body()
    assert payload["VendorID"]["value"] == "GOODFRUITS"
    assert payload["Type"]["value"] == "Receipt"
    assert payload["Hold"]["value"] is False

def test_builder_detail_from_po():
    """Tests adding a detail line from a Purchase Order."""
    builder = PurchaseReceiptBuilder().add_detail_from_po("PO000001")
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["POOrderNbr"]["value"] == "PO000001"

def test_builder_detail_with_allocations():
    """Tests adding a detail line with allocations."""
    allocations = [
        {"Location": "R1S1", "Qty": 5},
        {"Location": "R1S2", "Qty": 5},
    ]
    builder = PurchaseReceiptBuilder().add_detail_with_allocations("APPLES", 10, allocations)
    payload = builder.to_body()
    assert "Details" in payload
    assert "Allocations" in payload["Details"][0]
    assert len(payload["Details"][0]["Allocations"]) == 2
    assert payload["Details"][0]["Allocations"][0]["Location"]["value"] == "R1S1"

def test_builder_return_detail():
    """Tests adding a detail line for a purchase return."""
    builder = PurchaseReceiptBuilder().add_return_detail("APPLES", 1)
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["InventoryID"]["value"] == "APPLES"

def test_builder_return_from_receipt():
    """Tests adding a detail line for a return from an existing receipt."""
    builder = PurchaseReceiptBuilder().add_return_from_receipt("000016", 1)
    payload = builder.to_body()
    assert "Details" in payload
    assert len(payload["Details"]) == 1
    assert payload["Details"][0]["POReceiptNbr"]["value"] == "000016"
    assert payload["Details"][0]["POReceiptLineNbr"]["value"] == "1"

def test_builder_transfer_detail():
    """Tests adding a detail line for a transfer."""
    allocations = [{"Location": "JS1", "Qty": 0.5}]
    builder = PurchaseReceiptBuilder().add_transfer_detail("000064", allocations)
    payload = builder.to_body()
    assert "Details" in payload
    assert "Allocations" in payload["Details"][0]
    assert len(payload["Details"][0]["Allocations"]) == 1
    assert payload["Details"][0]["TransferOrderNbr"]["value"] == "000064"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = PurchaseReceiptBuilder().vendor_id("Test")
    body1 = builder.to_body()
    body1["VendorID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["VendorID"]["value"] == "Test"
