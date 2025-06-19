# easy_acumatica/sub_services/codes.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict

from ..helpers import _raise_with_detail
from ..models.code_builder import (
    DeductionBenefitCodeBuilder,
    EarningTypeCodeBuilder,
    PayrollWCCCodeBuilder,
)

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["CodesService"]


class CodesService:
    """
    Sub-service for payroll-related “code” entities in Acumatica ERP.

    This class exposes creation endpoints for:
      - Deduction/Benefit Codes
      - Earning Type Codes
      - Workers’ Compensation Class Codes

    All methods issue a PUT to the contract-based REST API under:
        /entity/Default/{api_version}/{EntityName}

    Preparation
    -----------
    - Ensure the Payroll and US Payroll features are enabled on CS100000.
    - Log in with a user who has rights to the corresponding forms.

    Usage Examples
    --------------
    >>> from easy_acumatica import AcumaticaClient
    >>> from easy_acumatica.models.code_builder import (
    ...     DeductionBenefitCodeBuilder,
    ...     EarningTypeCodeBuilder,
    ...     PayrollWCCCodeBuilder,
    ... )
    >>> client = AcumaticaClient(...)

    # 1) Create a Deduction/Benefit Code
    >>> ded_builder = (
    ...     DeductionBenefitCodeBuilder()
    ...     .code_id("TST")
    ...     .description("Test Deduction")
    ...     .contribution_type("DED")
    ...     .active(False)
    ...     .associated_with("Employee Settings")
    ...     .employee_deduction(calculation_method="GRS", percent=20, applicable_earnings="TOT")
    ...     .gl_accounts(deduction_liability_account="20000", deduction_liability_sub="000000")
    ... )
    >>> ded = client.codes.create_deduction_benefit_code("24.200.001", ded_builder)

    # 2) Create an Earning Type Code
    >>> earn_builder = (
    ...     EarningTypeCodeBuilder()
    ...     .code_id("ETC1")
    ...     .description("Overtime")
    ...     .category("Wage")
    ...     .accrue_time_off(True)
    ...     .active(True)
    ... )
    >>> etc = client.codes.create_earning_type_code("24.200.001", earn_builder)

    # 3) Create a Workers’ Compensation Class Code
    >>> wcc_builder = (
    ...     PayrollWCCCodeBuilder()
    ...     .country("US")
    ...     .add_wcc_code("2222", "Test Code", active=True)
    ... )
    >>> wcc = client.codes.create_payroll_wcc_code("24.200.001", wcc_builder)
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_deduction_benefit_code(
        self,
        api_version: str,
        builder: DeductionBenefitCodeBuilder
    ) -> Dict[str, Any]:
        """
        Create a new Deduction/Benefit Code.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/DeductionBenefitCode

        Args
        ----
        api_version : str
            The contract API version, e.g. "24.200.001".
        builder : DeductionBenefitCodeBuilder
            Fluent builder with required fields:
              - DeductionBenefitCodeID
              - Description
              - ContributionType
              - Active
              - AssociatedWith
              - EmployeeDeduction (nested)
              - GLAccounts (nested)

        Returns
        -------
        dict
            JSON of the newly created code.

        Raises
        ------
        RuntimeError
            On non-2xx HTTP responses, with server detail.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/DeductionBenefitCode"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = builder.build()

        resp = self._client._request(
            "put",
            url,
            headers=headers,
            json=payload,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def create_earning_type_code(
        self,
        api_version: str,
        builder: EarningTypeCodeBuilder
    ) -> Dict[str, Any]:
        """
        Create a new Earning Type Code.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/EarningTypeCode

        Args
        ----
        api_version : str
            The contract API version.
        builder : EarningTypeCodeBuilder
            Fluent builder with required fields:
              - EarningTypeCodeID
              - Description
              - Category
              - AccrueTimeOff
              - Active

        Returns
        -------
        dict
            JSON of the newly created earning type code.

        Raises
        ------
        RuntimeError
            On non-2xx HTTP responses.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/EarningTypeCode"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = builder.build()

        resp = self._client._request(
            "put",
            url,
            headers=headers,
            json=payload,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

    def create_payroll_wcc_code(
        self,
        api_version: str,
        builder: PayrollWCCCodeBuilder
    ) -> Dict[str, Any]:
        """
        Create a Workers’ Compensation Class Code.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/PayrollWCCCode

        Args
        ----
        api_version : str
            The contract API version.
        builder : PayrollWCCCodeBuilder
            Fluent builder for the payload:
              - Country
              - WCCCodes (list of codes with fields WCCCode, Description, Active)

        Returns
        -------
        dict
            JSON of the newly created WCC code.

        Raises
        ------
        RuntimeError
            On non-2xx HTTP responses.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/PayrollWCCCode"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        payload = builder.build()

        resp = self._client._request(
            "put",
            url,
            headers=headers,
            json=payload,
            verify=self._client.verify_ssl
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
