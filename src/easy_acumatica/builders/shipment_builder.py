# src/easy_acumatica/models/shipment_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy
from ..core import BaseDataClassModel # Import the new base class

class ShipmentBuilder(BaseDataClassModel): # Inherit from BaseModel
    """
    Fluent builder for the JSON payload to create or update a Shipment.
    """

    def __init__(self):
        super().__init__() # Call the parent constructor
        self._details: List[Dict[str, Any]] = []
        self._packages: List[Dict[str, Any]] = []

    # The .set() method is inherited, so you can remove it if it's identical.
    # We'll keep these specific setters for type hinting and convenience.
    def type(self, type: str) -> ShipmentBuilder:
        return self.set("Type", type)

    def customer_id(self, id: str) -> ShipmentBuilder:
        return self.set("CustomerID", id)

    def warehouse_id(self, id: str) -> ShipmentBuilder:
        return self.set("WarehouseID", id)

    def shipment_date(self, date: str) -> ShipmentBuilder:
        return self.set("ShipmentDate", date)

    def add_detail(self, **kwargs) -> ShipmentBuilder:
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def add_package(self, **kwargs) -> ShipmentBuilder:
        package = {}
        for key, value in kwargs.items():
            package[key] = {"value": value}
        self._packages.append(package)
        return self

    def to_body(self) -> Dict[str, Any]:
        """
        Constructs the final JSON payload for the API request.
        This overrides the base method to add details and packages.
        """
        body = super().to_body() # Start with the base fields
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        if self._packages:
            body["Packages"] = copy.deepcopy(self._packages)
        return body