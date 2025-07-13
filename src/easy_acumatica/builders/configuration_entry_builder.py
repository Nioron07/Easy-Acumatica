# src/easy_acumatica/models/configuration_entry_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class ConfigurationEntryBuilder:
    """
    Fluent builder for the JSON payload to create or update a Configuration Entry.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._features: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> ConfigurationEntryBuilder:
        """Set a top-level field on the configuration entry."""
        self._fields[field] = {"value": value}
        return self

    def prod_order_nbr(self, nbr: str) -> ConfigurationEntryBuilder:
        """Shortcut for .set('ProdOrderNbr', nbr)."""
        return self.set("ProdOrderNbr", nbr)

    def prod_order_type(self, type: str) -> ConfigurationEntryBuilder:
        """Shortcut for .set('ProdOrderType', type)."""
        return self.set("ProdOrderType", type)

    def config_results_id(self, id: str) -> ConfigurationEntryBuilder:
        """Shortcut for .set('ConfigResultsID', id)."""
        return self.set("ConfigResultsID", id)

    def configuration_id(self, id: str) -> ConfigurationEntryBuilder:
        """Shortcut for .set('ConfigurationID', id)."""
        return self.set("ConfigurationID", id)

    def add_feature(self, feature_line_nbr: int, config_results_id: str, options: List[Dict[str, Any]]) -> ConfigurationEntryBuilder:
        """Adds a feature with its options to the configuration entry."""
        feature = {
            "FeatureLineNbr": {"value": feature_line_nbr},
            "ConfigResultsID": {"value": config_results_id},
            "Options": options,
        }
        self._features.append(feature)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._features:
            body["Features"] = copy.deepcopy(self._features)
        return body