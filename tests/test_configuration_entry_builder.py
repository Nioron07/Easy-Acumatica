# tests/test_configuration_entry_builder.py

import pytest
from easy_acumatica.models.configuration_entry_builder import ConfigurationEntryBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = (
        ConfigurationEntryBuilder()
        .prod_order_nbr("AM000022")
        .prod_order_type("RO")
        .config_results_id("5")
        .configuration_id("AMC000003")
    )
    payload = builder.to_body()
    assert payload["ProdOrderNbr"]["value"] == "AM000022"
    assert payload["ProdOrderType"]["value"] == "RO"
    assert payload["ConfigResultsID"]["value"] == "5"
    assert payload["ConfigurationID"]["value"] == "AMC000003"

def test_builder_features_and_options():
    """Tests adding features and options."""
    options = [
        {
            "FeatureLineNbr": {"value": 1},
            "OptionLineNbr": {"value": 1},
            "ConfigResultsID": {"value": "5"},
            "Included": {"value": True},
        },
        {
            "FeatureLineNbr": {"value": 1},
            "OptionLineNbr": {"value": 2},
            "ConfigResultsID": {"value": "5"},
            "Included": {"value": True},
        },
    ]
    builder = ConfigurationEntryBuilder().add_feature(1, "5", options)
    payload = builder.to_body()
    assert "Features" in payload
    assert len(payload["Features"]) == 1
    assert payload["Features"][0]["FeatureLineNbr"]["value"] == 1
    assert len(payload["Features"][0]["Options"]) == 2

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = ConfigurationEntryBuilder().configuration_id("Test")
    body1 = builder.to_body()
    body1["ConfigurationID"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["ConfigurationID"]["value"] == "Test"