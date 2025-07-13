# src/easy_acumatica/models/bom_builder.py
from __future__ import annotations
from typing import Any, Dict, List
import copy

class BOMBuilder:
    """Fluent builder for constructing BOM JSON payloads.
    Required Fields (from prelimenary testing)
    ---------------
    bom_id
    inventeory_id
    
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._operations: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> BOMBuilder:
        self._fields[field] = {"value": value}
        return self

    def bom_id(self, value: str) -> BOMBuilder:
        return self.set("BOMID", value)

    def description(self, value: str) -> BOMBuilder:
        return self.set("Description", value)

    def inventory_id(self, value: str) -> BOMBuilder:
        return self.set("InventoryID", value)

    def revision(self, value: str) -> BOMBuilder:
        return self.set("Revision", value)

    def add_operation(self, operation_nbr: str, work_center: str,  materials: List[Dict[str, str]] = None, **kwargs) -> BOMBuilder:
        """

        Common, useful parameters when adding materials:
        ---------------------------
        InventoryID

        UOM

        UnitCost

        QtyRequired
        """
        operation = {"OperationNbr": {"value": operation_nbr}}
        if (work_center): 
            operation["WorkCenter"] = {"value": work_center}
        if (materials):
            operation["Material"] = [ {k: {"value": v} for k, v in material.items()} for material in materials]
        for key, value in kwargs.items():
            operation[key] = {"value": value}
        self._operations.append(operation)
        return self

    def to_body(self) -> Dict[str, Any]:
        body = copy.deepcopy(self._fields)
        if self._operations:
            body["Operations"] = self._operations
        return body
