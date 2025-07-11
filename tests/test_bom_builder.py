import pytest
from easy_acumatica.models.bom_builder import BOMBuilder

def test_builder_sets_simple_fields():
    builder = (
        BOMBuilder()
        .bom_id("BOM-001")
        .inventory_id("ITEM-123")
        .revision("A1")
        .description("Test BOM")
    )
    payload = builder.to_body()

    assert payload["BOMID"]["value"] == "BOM-001"
    assert payload["InventoryID"]["value"] == "ITEM-123"
    assert payload["Revision"]["value"] == "A1"
    assert payload["Description"]["value"] == "Test BOM"


def test_builder_adds_single_operation():
    builder = BOMBuilder().add_operation(
        operation_nbr="10",
        work_center="WC001"
    )
    payload = builder.to_body()

    assert "Operations" in payload
    operation = payload["Operations"][0]
    assert operation["OperationNbr"]["value"] == "10"
    assert operation["WorkCenter"]["value"] == "WC001"


def test_builder_adds_operation_with_materials():
    materials = [
        {"InventoryID": "PART-A", "QtyRequired": "2", "UnitCost": "10.00", "UOM": "EA"},
        {"InventoryID": "PART-B", "QtyRequired": "5", "UnitCost": "4.00", "UOM": "EA"},
    ]
    builder = BOMBuilder().add_operation(
        operation_nbr="20",
        work_center="WC002",
        materials=materials
    )
    payload = builder.to_body()

    operation = payload["Operations"][0]
    assert "Material" in operation
    assert len(operation["Material"]) == 2
    assert operation["Material"][0]["InventoryID"]["value"] == "PART-A"
    assert operation["Material"][1]["QtyRequired"]["value"] == "5"


def test_builder_adds_operation_with_extra_kwargs():
    builder = BOMBuilder().add_operation(
        operation_nbr="30",
        work_center="WC003",
        LaborTime="15.5",
        MachineTime="10.0"
    )
    payload = builder.to_body()
    operation = payload["Operations"][0]

    assert operation["LaborTime"]["value"] == "15.5"
    assert operation["MachineTime"]["value"] == "10.0"


def test_to_body_returns_deep_copy():
    builder = BOMBuilder().bom_id("BOM-TEST")
    body1 = builder.to_body()
    body1["BOMID"]["value"] = "CHANGED"

    body2 = builder.to_body()
    assert body2["BOMID"]["value"] == "BOM-TEST"
