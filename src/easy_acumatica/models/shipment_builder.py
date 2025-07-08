# src/easy_acumatica/models/shipment_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class ShipmentBuilder:
    """
    Fluent builder for the JSON payload to create or update a Shipment.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []
        self._packages: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> ShipmentBuilder:
        """Set a top-level field on the shipment."""
        self._fields[field] = {"value": value}
        return self

    def type(self, type: str) -> ShipmentBuilder:
        """Shortcut for .set('Type', type)."""
        return self.set("Type", type)

    def customer_id(self, id: str) -> ShipmentBuilder:
        """Shortcut for .set('CustomerID', id)."""
        return self.set("CustomerID", id)

    def warehouse_id(self, id: str) -> ShipmentBuilder:
        """Shortcut for .set('WarehouseID', id)."""
        return self.set("WarehouseID", id)

    def shipment_date(self, date: str) -> ShipmentBuilder:
        """Shortcut for .set('ShipmentDate', date)."""
        return self.set("ShipmentDate", date)

    def add_detail(self, **kwargs) -> ShipmentBuilder:
        """Adds a detail line to the shipment."""
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_package(self, **kwargs) -> ShipmentBuilder:
        """Adds a package to the shipment."""
        package = {}
        for key, value in kwargs.items():
            package[key] = {"value": value}
        self._packages.append(package)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        if self._packages:
            body["Packages"] = copy.deepcopy(self._packages)
        return body