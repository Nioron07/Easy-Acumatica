from easy_acumatica.models.work_calendar_builder import WorkCalendarBuilder

def test_builder_shortcut_methods():
    """Tests that the shortcut methods correctly set their respective fields."""
    builder = (
        WorkCalendarBuilder()
        .work_calendar_id("TESTCAL")
        .description("Test Calendar Description")
        .time_zone("GMTM0800A")
    )
    
    payload = builder.to_body()
    
    assert payload["WorkCalendarID"]["value"] == "TESTCAL"
    assert payload["Description"]["value"] == "Test Calendar Description"
    assert payload["TimeZone"]["value"] == "GMTM0800A"
    # Ensure empty lists are not added to the body
    assert "CalendarExceptions" not in payload
    assert "Calendar" not in payload

def test_builder_set_method():
    """Tests using the generic .set() method for any other field."""
    builder = WorkCalendarBuilder().set("Is24Hours", True)
    payload = builder.to_body()
    assert payload["Is24Hours"]["value"] is True

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder's state."""
    builder = WorkCalendarBuilder().work_calendar_id("OriginalID")
    
    body1 = builder.to_body()
    body1["WorkCalendarID"]["value"] = "ModifiedID"

    body2 = builder.to_body()
    
    # The second body should have the original value, not the modified one
    assert body2["WorkCalendarID"]["value"] == "OriginalID"