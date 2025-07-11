import pytest
from easy_acumatica.models.bill_builder import BillBuilder

def test_builder_simple_fields():
    builder = (
        BillBuilder()
        .vendor("VENDOR123")
        .vendor_ref("REF001")
        .description("Test bill")
        .type("Prepayment")
        .is_tax_valid(True)
    )
    payload = builder.to_body()
    assert payload["Vendor"]["value"] == "VENDOR123"
    assert payload["VendorRef"]["value"] == "REF001"
    assert payload["Description"]["value"] == "Test bill"
    assert payload["Type"]["value"] == "Prepayment"
    assert payload["IsTaxValid"]["value"] is True

def test_builder_add_detail():
    builder = BillBuilder().add_detail(InventoryID="PART-001", Qty="2", UnitCost="100")
    payload = builder.to_body()
    assert "Details" in payload
    detail = payload["Details"][0]
    assert detail["InventoryID"]["value"] == "PART-001"
    assert detail["Qty"]["value"] == "2"
    assert detail["UnitCost"]["value"] == "100"

def test_builder_add_detail_from_po():
    builder = BillBuilder().add_detail_from_po("PO123", po_line=2, po_type="Regular")
    payload = builder.to_body()
    detail = payload["Details"][0]
    assert detail["POOrderNbr"]["value"] == "PO123"
    assert detail["POLine"]["value"] == 2
    assert detail["POOrderType"]["value"] == "Regular"

def test_builder_add_tax_detail():
    builder = BillBuilder().add_tax_detail(TaxID="TAX001", TaxAmt="20.00")
    payload = builder.to_body()
    tax_detail = payload["TaxDetails"][0]
    assert tax_detail["TaxID"]["value"] == "TAX001"
    assert tax_detail["TaxAmt"]["value"] == "20.00"

def test_builder_custom_fields():
    builder = BillBuilder().set_custom_field("Document", "UsrNote", "Urgent")
    payload = builder.to_body()
    assert "custom" in payload
    assert payload["custom"]["Document"]["UsrNote"]["value"] == "Urgent"
    assert payload["custom"]["Document"]["UsrNote"]["type"] == "CustomStringField"

def test_to_body_returns_deep_copy():
    builder = BillBuilder().description("Initial")
    body1 = builder.to_body()
    body1["Description"]["value"] = "Changed"

    body2 = builder.to_body()
    assert body2["Description"]["value"] == "Initial"