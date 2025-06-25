# src/easy_acumatica/models/invoice_builder.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
import copy


class InvoiceBuilder:
    """
    Fluent builder for the JSON payload to create or update an Invoice.
    Handles nested Details and TaxDetails, and custom fields.
    """

    def __init__(self):
        self._id: Optional[str] = None
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Dict[str, Any]]] = []
        self._tax_details: List[Dict[str, Dict[str, Any]]] = []
        self._custom_fields: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def id(self, note_id: str) -> InvoiceBuilder:
        """Sets the top-level 'id' field for updating an existing record."""
        self._id = note_id
        return self

    def set(self, field: str, value: Any) -> InvoiceBuilder:
        """Set a top-level field on the invoice."""
        self._fields[field] = {"value": value}
        return self

    def type(self, doc_type: str) -> InvoiceBuilder:
        """Shortcut for .set('Type', doc_type). e.g., 'Invoice', 'Credit Memo'."""
        return self.set("Type", doc_type)

    def customer(self, customer_id: str) -> InvoiceBuilder:
        """Shortcut for .set('Customer', customer_id)."""
        return self.set("Customer", customer_id)

    def date(self, date_str: str) -> InvoiceBuilder:
        """Shortcut for .set('Date', date_str) in 'YYYY-MM-DD' format."""
        return self.set("Date", date_str)

    def post_period(self, period: str) -> InvoiceBuilder:
        """Shortcut for .set('PostPeriod', period), e.g., '012025'."""
        return self.set("PostPeriod", period)
        
    def due_date(self, date_str: str) -> InvoiceBuilder:
        """Shortcut for .set('DueDate', date_str) in 'YYYY-MM-DD' format."""
        return self.set("DueDate", date_str)

    def description(self, text: str) -> InvoiceBuilder:
        """Shortcut for .set('Description', text)."""
        return self.set("Description", text)

    def hold(self, flag: bool) -> InvoiceBuilder:
        """Shortcut for .set('Hold', flag)."""
        return self.set("Hold", flag)
        
    def is_tax_valid(self, flag: bool) -> InvoiceBuilder:
        """Shortcut for .set('IsTaxValid', flag)."""
        return self.set("IsTaxValid", flag)

    def location_id(self, location: str) -> InvoiceBuilder:
        """Shortcut for .set('LocationID', location)."""
        return self.set("LocationID", location)
        
    def customer_order(self, order_nbr: str) -> InvoiceBuilder:
        """Shortcut for .set('CustomerOrder', order_nbr)."""
        return self.set("CustomerOrder", order_nbr)
        
    def terms(self, terms_id: str) -> InvoiceBuilder:
        """Shortcut for .set('Terms', terms_id)."""
        return self.set("Terms", terms_id)
        
    def link_ar_account(self, account: str) -> InvoiceBuilder:
        """Shortcut for .set('LinkARAccount', account)."""
        return self.set("LinkARAccount", account)

    def bill_to_contact_override(self, flag: bool) -> InvoiceBuilder:
        """Shortcut for .set('BillToContactOverride', flag)."""
        return self.set("BillToContactOverride", flag)
        
    def ship_to_contact_override(self, flag: bool) -> InvoiceBuilder:
        """Shortcut for .set('ShipToContactOverride', flag)."""
        return self.set("ShipToContactOverride", flag)

    def add_detail_line(
        self,
        inventory_id: str,
        quantity: float,
        unit_price: float,
        **kwargs
    ) -> InvoiceBuilder:
        """Adds a line item to the invoice's Details."""
        line = {
            "InventoryID": {"value": inventory_id},
            "Qty": {"value": quantity},
            "UnitPrice": {"value": unit_price},
        }
        # Add any other optional fields for the line
        for key, value in kwargs.items():
            line[key] = {"value": value}
            
        self._details.append(line)
        return self

    def add_tax_detail(
        self,
        tax_id: str,
        taxable_amount: float,
        tax_amount: float
    ) -> InvoiceBuilder:
        """Adds a tax line to the invoice's TaxDetails."""
        tax_line = {
            "TaxID": {"value": tax_id},
            "TaxableAmount": {"value": taxable_amount},
            "TaxAmount": {"value": tax_amount},
        }
        self._tax_details.append(tax_line)
        return self
        
    def set_custom_field(self, view: str, field: str, value: Any, field_type: str = "CustomStringField") -> InvoiceBuilder:
        """Sets a custom field value."""
        if view not in self._custom_fields:
            self._custom_fields[view] = {}
        self._custom_fields[view][field] = {"type": field_type, "value": value}
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._id:
            body['id'] = self._id
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        if self._tax_details:
            body["TaxDetails"] = copy.deepcopy(self._tax_details)
        if self._custom_fields:
            body["custom"] = copy.deepcopy(self._custom_fields)
        return body
