"""
Unit tests for easy_acumatica.models.query_builder, using the
QueryOptions and CustomField classes.
"""
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions, CustomField

# ---------------------------------------------------------------------------
# CustomField and QueryOptions Tests
# ---------------------------------------------------------------------------

def test_customfield_formatting():
    """Tests the CustomField helper formats strings correctly."""
    # Test top-level field
    cf1 = CustomField.field("ItemSettings", "UsrRepairItemType")
    assert str(cf1) == "ItemSettings.UsrRepairItemType"

    # Test detail entity field
    cf2 = CustomField.field("Transactions", "UsrSpecialCode", entity_name="Details")
    assert str(cf2) == "Details/Transactions.UsrSpecialCode"

    # Test user-defined attribute
    cf3 = CustomField.attribute("Document", "OPERATSYST")
    assert str(cf3) == "Document.AttributeOPERATSYST"

def test_queryoptions_serialization():
    """Tests that QueryOptions correctly serializes all parameters to a dictionary."""
    filter_expr = F.Status == "Active"
    opts = QueryOptions(
        filter=filter_expr,
        select=["OrderID", "OrderDate"],
        expand=["Customer"],
        top=50,
        skip=100,
        custom=[
            CustomField.field("OrderProperties", "UsrPriority"),
            "Results/AttributeCOLOR" # Also test raw string
        ]
    )

    params = opts.to_params()

    assert params["$filter"] == "(Status eq 'Active')"
    assert params["$select"] == "OrderID,OrderDate"
    assert params["$expand"] == "Customer" # Should not be modified here
    assert params["$top"] == "50"
    assert params["$skip"] == "100"
    assert params["$custom"] == "OrderProperties.UsrPriority,Results/AttributeCOLOR"

def test_queryoptions_auto_expand_for_custom_fields():
    """
    Tests that QueryOptions intelligently adds required entities to the
    $expand list when custom fields from detail entities are used.
    """
    opts = QueryOptions(
        expand=["MainContact"],  # Initial expand list
        custom=[
            CustomField.field("Transactions", "UsrCost", entity_name="Details"),
            CustomField.field("ShipmentInfo", "UsrLabel", entity_name="Shipping"),
            "SomeOtherRawCustomField", # Should not affect expand
            CustomField.attribute("Document", "MYATTRIB"), # Should not affect expand
        ]
    )

    params = opts.to_params()

    # The resulting expand string should be a sorted, comma-separated list
    # containing the original values plus the auto-detected ones.
    expected_expand = "Details,MainContact,Shipping"
    assert "$expand" in params
    assert sorted(params["$expand"].split(',')) == sorted(expected_expand.split(','))

def test_queryoptions_handles_empty_and_none_values():
    """Tests that QueryOptions produces an empty dict when no options are given."""
    assert QueryOptions().to_params() == {}
    assert QueryOptions(filter=None, expand=[], custom=None).to_params() == {}
