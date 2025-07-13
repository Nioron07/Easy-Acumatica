# src/easy_acumatica/models/purchase_receipt_builder.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
import copy

class PurchaseReceiptBuilder:
    """
    Fluent builder for the JSON payload to create or update a PurchaseReceipt.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> PurchaseReceiptBuilder:
        """Set a top-level field on the purchase receipt."""
        self._fields[field] = {"value": value}
        return self

    def vendor_id(self, id: str) -> PurchaseReceiptBuilder:
        """Shortcut for .set('VendorID', id)."""
        return self.set("VendorID", id)
        
    def location(self, location: str) -> PurchaseReceiptBuilder:
        """Shortcut for .set('Location', location)."""
        return self.set("Location", location)

    def hold(self, hold: bool) -> PurchaseReceiptBuilder:
        """Shortcut for .set('Hold', hold)."""
        return self.set("Hold", hold)
    
    def control_quantity(self, quantity: str) -> PurchaseReceiptBuilder:
        return self.set("ControlQty", quantity)

    def type(self, type: str) -> PurchaseReceiptBuilder:
        """Shortcut for .set('Type', type). Can be 'Receipt', 'Return', or 'Transfer Receipt'."""
        return self.set("Type", type)
        
    def create_bill(self, create_bill: bool) -> PurchaseReceiptBuilder:
        """Shortcut for .set('CreateBill', create_bill)."""
        return self.set("CreateBill", create_bill)

    def description(self, description: str) -> PurchaseReceiptBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)

    def process_return_with_original_cost(self, process: bool) -> PurchaseReceiptBuilder:
        """Shortcut for .set('ProcessReturnWithOriginalCost', process)."""
        return self.set("ProcessReturnWithOriginalCost", process)
        
    def currency(self, currency_id: str, rate: Optional[float] = None) -> PurchaseReceiptBuilder:
        """Sets the currency and optionally the rate."""
        self.set("CurrencyID", currency_id)
        if rate is not None:
            self.set("CurrencyRate", rate)
        return self

    def warehouse(self, warehouse_id: str) -> PurchaseReceiptBuilder:
        """Shortcut for .set('Warehouse', warehouse_id)."""
        return self.set("Warehouse", warehouse_id)

    def add_detail_from_po(self, po_order_nbr: str, po_order_type: str = "Normal", **kwargs) -> PurchaseReceiptBuilder:
        """Adds a detail line from a Purchase Order."""
        detail = {
            "POOrderNbr": {"value": po_order_nbr},
            "POOrderType": {"value": po_order_type}
        }
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_detail_with_allocations(self, inventory_id: str, receipt_qty: float, allocations: List[Dict[str, Any]], **kwargs) -> PurchaseReceiptBuilder:
        """Adds a detail line with item allocations."""
        detail = {
            "InventoryID": {"value": inventory_id},
            "ReceiptQty": {"value": receipt_qty},
            "Allocations": []
        }
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        
        # Format allocations
        for alloc in allocations:
            formatted_alloc = {}
            for key, value in alloc.items():
                formatted_alloc[key] = {"value": value}
            detail["Allocations"].append(formatted_alloc)
            
        self._details.append(detail)
        return self
        
    def add_return_detail(self, inventory_id: str, receipt_qty: float, **kwargs) -> PurchaseReceiptBuilder:
        """Adds a detail line for a purchase return of a specific item."""
        detail = {
            "InventoryID": {"value": inventory_id},
            "ReceiptQty": {"value": receipt_qty}
        }
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self
        
    def add_return_from_receipt(self, receipt_nbr: str, line_nbr: Optional[int] = None) -> PurchaseReceiptBuilder:
        """Adds a detail line for a purchase return from an existing receipt."""
        detail = {"POReceiptNbr": {"value": receipt_nbr}}
        if line_nbr:
            detail["POReceiptLineNbr"] = {"value": str(line_nbr)}
        self._details.append(detail)
        return self
        
    def add_transfer_detail(self, transfer_order_nbr: str, allocations: List[Dict[str, Any]], **kwargs) -> PurchaseReceiptBuilder:
        """Adds a detail line for a transfer receipt."""
        detail = {
            "TransferOrderNbr": {"value": transfer_order_nbr},
            "Allocations": []
        }
        for key, value in kwargs.items():
            detail[key] = {"value": value}
            
        # Format allocations
        for alloc in allocations:
            formatted_alloc = {}
            for key, value in alloc.items():
                formatted_alloc[key] = {"value": value}
            detail["Allocations"].append(formatted_alloc)

        self._details.append(detail)
        return self


    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        return body
