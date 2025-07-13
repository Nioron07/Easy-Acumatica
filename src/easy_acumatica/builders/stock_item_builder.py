# src/easy_acumatica/models/stock_item_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class StockItemBuilder:
    """
    Fluent builder for the JSON payload to create or update a StockItem.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._attributes: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> StockItemBuilder:
        """Set a top-level field on the stock item."""
        self._fields[field] = {"value": value}
        return self

    def inventory_id(self, id: str) -> StockItemBuilder:
        """Shortcut for .set('InventoryID', id)."""
        return self.set("InventoryID", id)

    def description(self, description: str) -> StockItemBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)

    def item_class(self, item_class: str) -> StockItemBuilder:
        """Shortcut for .set('ItemClass', item_class)."""
        return self.set("ItemClass", item_class)
        
    def note(self, note: str) -> StockItemBuilder:
        """Shortcut for .set('note', note)."""
        self._fields["note"] = {"value": note}
        return self

    def add_attribute(self, attribute_id: str, value: str) -> StockItemBuilder:
        """Adds an attribute to the stock item."""
        attribute = {
            "AttributeID": {"value": attribute_id},
            "Value": {"value": value},
        }
        self._attributes.append(attribute)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._attributes:
            body["Attributes"] = copy.deepcopy(self._attributes)
        return body