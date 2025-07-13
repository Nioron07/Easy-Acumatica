# src/easy_acumatica/models/purchase_order_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class PurchaseOrderBuilder:
    """
    Fluent builder for the JSON payload to create or update a PurchaseOrder.

    Unknown which fields are expressly useful as a quick function, just took the ones from the documentation. 
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> PurchaseOrderBuilder:
        """Set a top-level field on the purchase order."""
        self._fields[field] = {"value": value}
        return self

    def vendor_id(self, id: str) -> PurchaseOrderBuilder:
        """Shortcut for .set('VendorID', id)."""
        return self.set("VendorID", id)

    def location(self, location: str) -> PurchaseOrderBuilder:
        """Shortcut for .set('Location', location)."""
        return self.set("Location", location)

    def hold(self, hold: bool) -> PurchaseOrderBuilder:
        """Shortcut for .set('Hold', hold)."""
        return self.set("Hold", hold)

    def add_detail(self, **kwargs) -> PurchaseOrderBuilder:
        """Adds a detail line to the purchase order."""
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        return body