# src/easy_acumatica/sub_services/employee_payroll.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..core import BaseService
from ..builders import (
    EmployeePayrollClassBuilder, 
    EmployeePayrollSettingsBuilder
)
from ..odata import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["EmployeePayrollService"]

class EmployeePayrollService(BaseService):
    """
    Sub-service for managing employee payroll classes and settings.
    This service handles both EmployeePayrollClass and EmployeePayrollSettings entities.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        # Initialize the base service without a default entity name,
        # as this service handles multiple entities.
        super().__init__(client, "") 

    def create_employee_payroll_class(
        self, 
        builder: EmployeePayrollClassBuilder, 
        api_version: Optional[str] = None
    ) -> Any:
        """
        Creates a new employee payroll class.

        Sends a PUT request to the /EmployeePayrollClass endpoint, expanding
        the default payroll and PTO details in the response.
        """
        self.entity_name = "EmployeePayrollClass"
        try:
            options = QueryOptions(expand=["PayrollDefaults/WorkLocations", "PTODefaults"])
            return self._put(builder, api_version, options)
        finally:
            # Reset entity_name in case the service instance is reused
            self.entity_name = ""

    def update_employee_payroll_settings(
        self, 
        builder: EmployeePayrollSettingsBuilder, 
        api_version: Optional[str] = None, 
        expand_work_locations: bool = False, 
        expand_employment_records: bool = False
    ) -> Any:
        """
        Updates employee payroll settings, including work locations and
        employment records.

        Sends a PUT request to the /EmployeePayrollSettings endpoint. The response
        can be expanded to include related details based on the boolean flags.
        """
        self.entity_name = "EmployeePayrollSettings"
        try:
            expand_options = []
            if expand_work_locations:
                expand_options.append("WorkLocations/WorkLocationDetails")
            if expand_employment_records:
                expand_options.append("EmploymentRecords")
            
            # Create QueryOptions only if there's something to expand
            options = QueryOptions(expand=expand_options) if expand_options else None
            
            # The _put method handles the entire request lifecycle
            return self._put(builder, api_version, options)
        finally:
            # Reset entity_name
            self.entity_name = ""