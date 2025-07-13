# src/easy_acumatica/models/sales_order_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class SalesOrderBuilder:
    """
    Fluent builder for the JSON payload to create or update a SalesOrder.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []
        self._payments: List[Dict[str, Any]] = []
        self._tax_details: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> SalesOrderBuilder:
        """Set a top-level field on the sales order."""
        self._fields[field] = {"value": value}
        return self

    def customer_id(self, id: str) -> SalesOrderBuilder:
        """Shortcut for .set('CustomerID', id)."""
        return self.set("CustomerID", id)

    def order_type(self, type: str) -> SalesOrderBuilder:
        """Shortcut for .set('OrderType', type)."""
        return self.set("OrderType", type)

    def order_nbr(self, nbr: str) -> SalesOrderBuilder:
        """Shortcut for .set('OrderNbr', nbr)."""
        return self.set("OrderNbr", nbr)

    def hold(self, hold: bool) -> SalesOrderBuilder:
        """Shortcut for .set('Hold', hold)."""
        return self.set("Hold", hold)

    def add_detail(self, **kwargs) -> SalesOrderBuilder:
        """Adds a detail line to the sales order."""
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_payment(self, **kwargs) -> SalesOrderBuilder:
        """Adds a payment to the sales order."""
        payment = {}
        for key, value in kwargs.items():
            payment[key] = {"value": value}
        self._payments.append(payment)
        return self

    def add_tax_detail(self, **kwargs) -> SalesOrderBuilder:
        """Adds a tax detail to the sales order."""
        tax_detail = {}
        for key, value in kwargs.items():
            tax_detail[key] = {"value": value}
        self._tax_details.append(tax_detail)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        if self._payments:
            body["Payments"] = copy.deepcopy(self._payments)
        if self._tax_details:
            body["TaxDetails"] = copy.deepcopy(self._tax_details)
        return body