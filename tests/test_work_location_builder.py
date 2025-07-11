from easy_acumatica.models.work_location_builder import WorkLocationBuilder

def test_builder_all_fields():
    """Tests that all shortcut methods correctly set their respective fields."""
    builder = (
        WorkLocationBuilder()
        .work_location_id("BELLEVUE")
        .work_location_name("Bellevue Office")
        .active(True)
        .address_info(
            address_line_1="123 Main Street",
            city="Bellevue",
            country="US",
            postal_code="98004",
            state="WA"
        )
    )
    
    payload = builder.to_body()
    
    assert payload["WorkLocationID"]["value"] == "BELLEVUE"
    assert payload["WorkLocationName"]["value"] == "Bellevue Office"
    assert payload["Active"]["value"] is True
    
    address = payload.get("AddressInfo", {})
    assert address.get("AddressLine1", {}).get("value") == "123 Main Street"
    assert address.get("City", {}).get("value") == "Bellevue"
    assert address.get("Country", {}).get("value") == "US"
    assert address.get("PostalCode", {}).get("value") == "98004"
    assert address.get("State", {}).get("value") == "WA"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder's state."""
    builder = WorkLocationBuilder().work_location_id("OriginalID")
    
    body1 = builder.to_body()
    body1["WorkLocationID"]["value"] = "ModifiedID"

    body2 = builder.to_body()
    assert body2["WorkLocationID"]["value"] == "OriginalID"