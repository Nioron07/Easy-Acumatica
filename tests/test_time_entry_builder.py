# tests/test_time_entry_builder.py

import pytest
from easy_acumatica.models.time_entry_builder import TimeEntryBuilder

def test_builder_all_shortcut_methods():
    """Tests that all shortcut methods correctly set their respective fields."""
    builder = (
        TimeEntryBuilder()
        .summary("Time entry summary")
        .date("2022-08-17T05:50:43.233")
        .employee("EP00000026")
        .project_id("TOMYUM1")
        .project_task_id("PHASE1")
        .cost_code("00-000")
        .earning_type("RG")
        .time_spent("01:30")
        .billable_time("00:30")
        .time_entry_id("some-guid-string")
    )
    
    payload = builder.to_body()
    
    assert payload["Summary"]["value"] == "Time entry summary"
    assert payload["Date"]["value"] == "2022-08-17T05:50:43.233"
    assert payload["Employee"]["value"] == "EP00000026"
    assert payload["ProjectID"]["value"] == "TOMYUM1"
    assert payload["ProjectTaskID"]["value"] == "PHASE1"
    assert payload["CostCode"]["value"] == "00-000"
    assert payload["EarningType"]["value"] == "RG"
    assert payload["TimeSpent"]["value"] == "01:30"
    assert payload["BillableTime"]["value"] == "00:30"
    assert payload["TimeEntryID"]["value"] == "some-guid-string"

def test_builder_set_method():
    """Tests using the generic .set() method for any other field."""
    builder = TimeEntryBuilder().set("CustomField", "CustomValue")
    payload = builder.to_body()
    assert payload["CustomField"]["value"] == "CustomValue"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder's state."""
    builder = TimeEntryBuilder().summary("Original Summary")
    
    body1 = builder.to_body()
    body1["Summary"]["value"] = "Modified Summary"

    body2 = builder.to_body()
    
    # The second body should have the original value, not the modified one
    assert body2["Summary"]["value"] == "Original Summary"