# src/easy_acumatica/sub_services/employees.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.employee_builder import EmployeeBuilder
from ..models.employee_payroll_class_builder import EmployeePayrollClassBuilder
from ..models.employee_payroll_settings_builder import EmployeePayrollSettingsBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["EmployeesService"]


class EmployeesService:
    """Sub-service for creating and managing Employees."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_employee(
        self,
        api_version: str,
        builder: EmployeeBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Employee.

        Sends a PUT request to the /Employee endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : EmployeeBuilder
            A fluent builder instance containing the employee details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Employee"
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            params=params,
            json=builder.to_body(),
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def get_employees(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of employees.

        Sends a GET request to the /Employee endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        options : QueryOptions, optional
            Allows for specifying $filter, $select, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body from Acumatica, typically a list of employees.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Employee"
        params = options.to_params() if options else None
        headers = {"Accept": "application/json"}

        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def create_employee_payroll_class(self, api_version: str, builder: EmployeePayrollClassBuilder) -> Any:
        """
        Create a new employee payroll class.

        Sends a PUT request to the /EmployeePayrollClass endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/EmployeePayrollClass"
        params = {"$expand": "PayrollDefaults/WorkLocations,PTODefaults"}
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        resp = self._client._request(
            "put", url, params=params, json=builder.to_body(), headers=headers, verify=self._client.verify_ssl
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def update_employee_payroll_settings(
        self, api_version: str, builder: EmployeePayrollSettingsBuilder, expand_work_locations: bool = False, expand_employment_records: bool = False
    ) -> Any:
        """
        Update employee payroll settings.

        Sends a PUT request to the /EmployeePayrollSettings endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/EmployeePayrollSettings"
        
        expand_options = []
        if expand_work_locations:
            expand_options.append("WorkLocations/WorkLocationDetails")
        if expand_employment_records:
            expand_options.append("EmploymentRecords")
        
        params = {"$expand": ",".join(expand_options)} if expand_options else None
        
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        resp = self._client._request(
            "put", url, params=params, json=builder.to_body(), headers=headers, verify=self._client.verify_ssl
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()