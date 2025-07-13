# src/easy_acumatica/models/employee_builder.py

from __future__ import annotations
from typing import Any, Dict, Optional
import copy


class EmployeeBuilder:
    """
    Fluent builder for the JSON payload to create or update an Employee.
    Handles nested objects like ContactInfo, FinancialSettings, and EmployeeSettings.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._contact_info: Dict[str, Any] = {}
        self._financial_settings: Dict[str, Any] = {}
        self._employee_settings: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> EmployeeBuilder:
        """Set a top-level field on the employee, like Status."""
        self._fields[field] = {"value": value}
        return self

    def status(self, status: str) -> EmployeeBuilder:
        """Shortcut for .set('Status', status). e.g., 'Active'."""
        return self.set("Status", status)

    def contact_info(
        self,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        email: Optional[str] = None,
        phone_1: Optional[str] = None,
        phone_2: Optional[str] = None,
        phone_3: Optional[str] = None,
        **kwargs
    ) -> EmployeeBuilder:
        """
        Set fields within the ContactInfo object.
        Additional contact fields can be passed as keyword arguments.
        """
        fields_to_set = {
            "FirstName": first_name,
            "LastName": last_name,
            "Email": email,
            "Phone1": phone_1,
            "Phone2": phone_2,
            "Phone3": phone_3,
            **kwargs
        }
        for key, value in fields_to_set.items():
            if value is not None:
                self._contact_info[key] = {"value": value}
        return self

    def financial_settings(
        self,
        ap_account: Optional[str] = None,
        ap_subaccount: Optional[str] = None,
        cash_account: Optional[str] = None,
        expense_account: Optional[str] = None,
        expense_subaccount: Optional[str] = None,
        payment_method: Optional[str] = None,
        sales_account: Optional[str] = None,
        sales_subaccount: Optional[str] = None,
        terms: Optional[str] = None,
        tax_zone: Optional[str] = None,
        **kwargs
    ) -> EmployeeBuilder:
        """Set fields within the FinancialSettings object using keyword arguments."""
        fields_to_set = {
            "APAccount": ap_account,
            "APSubaccount": ap_subaccount,
            "CashAccount": cash_account,
            "ExpenseAccount": expense_account,
            "ExpenseSubaccount": expense_subaccount,
            "PaymentMethod": payment_method,
            "SalesAccount": sales_account,
            "SalesSubaccount": sales_subaccount,
            "Terms": terms,
            "TaxZone": tax_zone,
            **kwargs
        }
        for key, value in fields_to_set.items():
            if value is not None:
                self._financial_settings[key] = {"value": value}
        return self

    def employee_settings(
        self,
        branch_id: Optional[str] = None,
        department_id: Optional[str] = None,
        employee_class: Optional[str] = None,
        reports_to: Optional[str] = None,
        time_card_is_required: Optional[bool] = None,
        **kwargs
    ) -> EmployeeBuilder:
        """Set fields within the EmployeeSettings object using keyword arguments."""
        fields_to_set = {
            "BranchID": branch_id,
            "DepartmentID": department_id,
            "EmployeeClass": employee_class,
            "ReportsTo": reports_to,
            "TimeCardIsRequired": time_card_is_required,
            **kwargs
        }
        for key, value in fields_to_set.items():
            if value is not None:
                self._employee_settings[key] = {"value": value}
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._contact_info:
            body["ContactInfo"] = copy.deepcopy(self._contact_info)
        if self._financial_settings:
            body["FinancialSettings"] = copy.deepcopy(self._financial_settings)
        if self._employee_settings:
            body["EmployeeSettings"] = copy.deepcopy(self._employee_settings)
        return body
