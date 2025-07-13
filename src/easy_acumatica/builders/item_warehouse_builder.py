# src/easy_acumatica/models/item_warehouse_builder.py

from __future__ import annotations
from typing import Any, Dict
import copy

class ItemWarehouseBuilder:
    """
    Fluent builder for the JSON payload to update ItemWarehouse details.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> ItemWarehouseBuilder:
        """Set a top-level field on the item-warehouse details."""
        self._fields[field] = {"value": value}
        return self

    def inventory_id(self, id: str) -> ItemWarehouseBuilder:
        """Shortcut for .set('InventoryID', id)."""
        return self.set("InventoryID", id)

    def warehouse_id(self, id: str) -> ItemWarehouseBuilder:
        """Shortcut for .set('WarehouseID', id)."""
        return self.set("WarehouseID", id)

    def override(self, field: str, value: bool) -> ItemWarehouseBuilder:
        """Sets an override flag for a specific field."""
        return self.set(f"Override{field}", value)

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        return copy.deepcopy(self._fields)