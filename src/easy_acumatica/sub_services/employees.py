# src/easy_acumatica/sub_services/employees.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..core import BaseService # Import the new base class
from ..builders.employee_builder import EmployeeBuilder
from ..odata import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["EmployeesService"]

class EmployeesService(BaseService):
    """Sub-service for creating and managing Employees."""

    def __init__(self, client: "AcumaticaClient") -> None:
        # Initialize the base service with the entity name
        super().__init__(client, "Employee")

    def create_employee(
        self,
        builder: EmployeeBuilder,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None
    ) -> Any:
        """
        Create a new Employee.
        Sends a PUT request to the /Employee endpoint.
        """
        # The _put method from BaseService handles the entire request lifecycle
        return self._put(builder, api_version, options)

    def get_employees(
        self,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of employees.
        Sends a GET request to the /Employee endpoint.
        """
        # The _get method from BaseService handles the request
        return self._get(api_version=api_version, options=options)