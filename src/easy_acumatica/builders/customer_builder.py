# easy_acumatica/models/customer_builder.py

from __future__ import annotations
from typing import Any, Dict


class CustomerBuilder:
    """
    Fluent builder for the JSON payload to create or update a Customer.
    Each field is wrapped as {"value": ...} to match Acumatica's contract-based API.
    """

    def __init__(self) -> None:
        self._fields: Dict[str, Dict[str, Any]] = {}

    def set(self, field: str, value: Any) -> CustomerBuilder:
        """
        Set any arbitrary field on the Customer payload.
        Overwrites previous value if called twice.
        """
        self._fields[field] = {"value": value}
        return self

    def customer_id(self, cust_id: str) -> CustomerBuilder:
        """Shortcut for .set('CustomerID', cust_id)."""
        return self.set("CustomerID", cust_id)

    def customer_name(self, name: str) -> CustomerBuilder:
        """Shortcut for .set('CustomerName', name)."""
        return self.set("CustomerName", name)

    def customer_class(self, cls: str) -> CustomerBuilder:
        """Shortcut for .set('CustomerClass', cls)."""
        return self.set("CustomerClass", cls)

    def to_body(self) -> Dict[str, Dict[str, Any]]:
        """
        Return a fresh dict suitable for the PUT body. Each inner dict
        is .copy()'d so callers can't mutate this builder's internal state.
        """
        return {field: data.copy() for field, data in self._fields.items()}
