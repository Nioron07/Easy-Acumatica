# src/easy_acumatica/models/bill_builder.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
import copy

class BillBuilder:
    """
    Fluent builder for the JSON payload to create or update a Bill.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []
        self._tax_details: List[Dict[str, Any]] = []
        self._custom_fields: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def set(self, field: str, value: Any) -> BillBuilder:
        """Set a top-level field on the bill."""
        self._fields[field] = {"value": value}
        return self

    def vendor(self, vendor_id: str) -> BillBuilder:
        """Shortcut for .set('Vendor', vendor_id)."""
        return self.set("Vendor", vendor_id)

    def vendor_ref(self, ref: str) -> BillBuilder:
        """Shortcut for .set('VendorRef', ref)."""
        return self.set("VendorRef", ref)

    def description(self, description: str) -> BillBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)
        
    def type(self, type: str = "Bill") -> BillBuilder:
        """Shortcut for .set('Type', type)."""
        return self.set("Type", type)

    def is_tax_valid(self, is_valid: bool) -> BillBuilder:
        """Shortcut for .set('IsTaxValid', is_valid)."""
        return self.set("IsTaxValid", is_valid)

    def add_detail_from_po(self, po_order_nbr: str, po_line: Optional[int] = None, po_type: str = None, **kwargs) -> BillBuilder:
        """Adds a detail line from a Purchase Order."""
        detail = {"POOrderNbr": {"value": po_order_nbr}}
        if po_line:
            detail["POLine"] = {"value": po_line}
        if po_type: 
            detail["POOrderType"] = {"value": po_type}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self
        
    def add_detail_from_pr(self, po_receipt_nbr: str, po_receipt_line: Optional[int] = None, **kwargs) -> BillBuilder:
        """Adds a detail line from a Purchase Receipt."""
        detail = {"POReceiptNbr": {"value": po_receipt_nbr}}
        if po_receipt_line:
            detail["POReceiptLine"] = {"value": po_receipt_line}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_detail(self, **kwargs) -> BillBuilder:
        """Adds a generic detail line. Put in your part or item number, quantity, and price here. 
        
        Common Parameters: 
        ----------
        InventoryID : str,
        Qty : str,
        UnitCost : str,
        """
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_tax_detail(self, **kwargs) -> BillBuilder:
        """Adds a tax detail line."""
        tax_detail = {}
        for key, value in kwargs.items():
            tax_detail[key] = {"value": value}
        self._tax_details.append(tax_detail)
        return self

    def set_custom_field(self, view: str, field: str, value: Any, field_type: str = "CustomStringField") -> BillBuilder:
        """Sets a custom field value."""
        if view not in self._custom_fields:
            self._custom_fields[view] = {}
        self._custom_fields[view][field] = {"type": field_type, "value": value}
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = self._details
        if self._tax_details:
            body["TaxDetails"] = self._tax_details
        if self._custom_fields:
            body["custom"] = self._custom_fields
        return body