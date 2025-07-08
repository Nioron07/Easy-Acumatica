# src/easy_acumatica/models/employee_payroll_settings_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class EmployeePayrollSettingsBuilder:
    """
    Fluent builder for the JSON payload to update EmployeePayrollSettings.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._work_locations: Dict[str, Any] = {}
        self._employment_records: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> EmployeePayrollSettingsBuilder:
        """Set a top-level field on the employee payroll settings."""
        self._fields[field] = {"value": value}
        return self

    def employee_id(self, id: str) -> EmployeePayrollSettingsBuilder:
        """Shortcut for .set('EmployeeID', id)."""
        return self.set("EmployeeID", id)

    def class_id(self, id: str) -> EmployeePayrollSettingsBuilder:
        """Shortcut for .set('ClassID', id)."""
        return self.set("ClassID", id)

    def payment_method(self, method: str) -> EmployeePayrollSettingsBuilder:
        """Shortcut for .set('PaymentMethod', method)."""
        return self.set("PaymentMethod", method)

    def cash_account(self, account: str) -> EmployeePayrollSettingsBuilder:
        """Shortcut for .set('CashAccount', account)."""
        return self.set("CashAccount", account)

    def work_locations(self, use_class_defaults: bool, details: List[Dict[str, Any]]) -> EmployeePayrollSettingsBuilder:
        """Set fields within the WorkLocations object."""
        self._work_locations["WorkLocationClassDefaults"] = {"value": use_class_defaults}
        self._work_locations["WorkLocationDetails"] = details
        return self

    def add_employment_record(self, **kwargs) -> EmployeePayrollSettingsBuilder:
        """Adds an employment record to the EmploymentRecords list."""
        record = {}
        for key, value in kwargs.items():
            record[key] = {"value": value}
        self._employment_records.append(record)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._work_locations:
            body["WorkLocations"] = copy.deepcopy(self._work_locations)
        if self._employment_records:
            body["EmploymentRecords"] = copy.deepcopy(self._employment_records)
        return body