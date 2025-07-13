# src/easy_acumatica/models/employee_payroll_class_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class EmployeePayrollClassBuilder:
    """
    Fluent builder for the JSON payload to create an EmployeePayrollClass.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._payroll_defaults: Dict[str, Any] = {}
        self._pto_defaults: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> EmployeePayrollClassBuilder:
        """Set a top-level field on the employee payroll class."""
        self._fields[field] = {"value": value}
        return self

    def employee_payroll_class_id(self, id: str) -> EmployeePayrollClassBuilder:
        """Shortcut for .set('EmployeePayrollClassID', id)."""
        return self.set("EmployeePayrollClassID", id)

    def description(self, description: str) -> EmployeePayrollClassBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)

    def payroll_defaults(self, **kwargs) -> EmployeePayrollClassBuilder:
        """Set fields within the PayrollDefaults object."""
        for key, value in kwargs.items():
            self._payroll_defaults[key] = {"value": value}
        return self

    def add_pto_default(self, **kwargs) -> EmployeePayrollClassBuilder:
        """Adds a PTO default to the PTODefaults list."""
        pto_default = {}
        for key, value in kwargs.items():
            pto_default[key] = {"value": value}
        self._pto_defaults.append(pto_default)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._payroll_defaults:
            body["PayrollDefaults"] = copy.deepcopy(self._payroll_defaults)
        if self._pto_defaults:
            body["PTODefaults"] = copy.deepcopy(self._pto_defaults)
        return body