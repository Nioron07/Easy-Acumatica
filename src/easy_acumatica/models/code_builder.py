# easy_acumatica/models/deduction_builder.py

from __future__ import annotations
from typing import Any, Dict, List


class DeductionBenefitCodeBuilder:
    """
    Fluent builder for a DeductionBenefitCode payload.

    Allows setting all required properties for a deduction/benefit code,
    including associated GL accounts and employee-deduction settings.

    Example
    -------
    >>> builder = (
    ...     DeductionBenefitCodeBuilder()
    ...     .code_id("TST")
    ...     .description("Test deduction")
    ...     .contribution_type("DED")
    ...     .active(False)
    ...     .associated_with("Employee Settings")
    ...     .employee_deduction(calculation_method="GRS", percent=20, applicable_earnings="TOT")
    ...     .gl_accounts(deduction_liability_account="20000", deduction_liability_sub="000000")
    ... )
    >>> builder.build()
    {
        "DeductionBenefitCodeID": {"value":"TST"},
        "Description": {"value":"Test deduction"},
        ...
    }
    """

    def __init__(self) -> None:
        self._fields: Dict[str, Dict[str, Any]] = {}

    def code_id(self, code: str) -> DeductionBenefitCodeBuilder:
        """Set the DeductionBenefitCodeID field."""
        self._fields["DeductionBenefitCodeID"] = {"value": code}
        return self

    def description(self, text: str) -> DeductionBenefitCodeBuilder:
        """Set the Description field."""
        self._fields["Description"] = {"value": text}
        return self

    def contribution_type(self, ct: str) -> DeductionBenefitCodeBuilder:
        """Set the ContributionType field (e.g., 'DED' or 'BEN')."""
        self._fields["ContributionType"] = {"value": ct}
        return self

    def active(self, is_active: bool) -> DeductionBenefitCodeBuilder:
        """Set the Active flag."""
        self._fields["Active"] = {"value": is_active}
        return self

    def associated_with(self, assoc: str) -> DeductionBenefitCodeBuilder:
        """Set the AssociatedWith field (e.g., 'Employee Settings')."""
        self._fields["AssociatedWith"] = {"value": assoc}
        return self

    def employee_deduction(
        self,
        calculation_method: str | None = None,
        percent: float | None = None,
        applicable_earnings: str | None = None,
    ) -> DeductionBenefitCodeBuilder:
        """Configure the EmployeeDeduction nested object."""
        sub: Dict[str, Any] = {}
        if calculation_method is not None:
            sub["CalculationMethod"] = {"value": calculation_method}
        if percent is not None:
            sub["Percent"] = {"value": percent}
        if applicable_earnings is not None:
            sub["ApplicableEarnings"] = {"value": applicable_earnings}
        self._fields["EmployeeDeduction"] = sub
        return self

    def gl_accounts(
        self,
        deduction_liability_account: str | None = None,
        deduction_liability_sub: str | None = None
    ) -> DeductionBenefitCodeBuilder:
        """Configure the GLAccounts nested object."""
        sub: Dict[str, Any] = {}
        if deduction_liability_account is not None:
            sub["DeductionLiabilityAccount"] = {"value": deduction_liability_account}
        if deduction_liability_sub is not None:
            sub["DeductionLiabilitySub"] = {"value": deduction_liability_sub}
        self._fields["GLAccounts"] = sub
        return self

    def build(self) -> Dict[str, Dict[str, Any]]:
        """
        Produce a fresh JSON payload dict for the API call.
        Consumers can safely mutate the result without altering this builder.
        """
        # shallow-copy each inner dict to prevent external mutation
        return {k: v.copy() for k, v in self._fields.items()}


class EarningTypeCodeBuilder:
    """
    Fluent builder for an EarningTypeCode payload.

    Required fields:
      - EarningTypeCodeID
      - Description
      - Category
      - AccrueTimeOff
      - Active

    Example:
        builder = (
            EarningTypeCodeBuilder()
            .code_id("TST")
            .description("Test Code")
            .category("Wage")
            .accrue_time_off(True)
            .active(False)
        )
        payload = builder.build()
    """

    def __init__(self) -> None:
        self._fields: Dict[str, Dict[str, Any]] = {}

    def code_id(self, code: str) -> EarningTypeCodeBuilder:
        """Set the EarningTypeCodeID field."""
        self._fields["EarningTypeCodeID"] = {"value": code}
        return self

    def description(self, text: str) -> EarningTypeCodeBuilder:
        """Set the Description field."""
        self._fields["Description"] = {"value": text}
        return self

    def category(self, cat: str) -> EarningTypeCodeBuilder:
        """Set the Category field (e.g., 'Wage')."""
        self._fields["Category"] = {"value": cat}
        return self

    def accrue_time_off(self, flag: bool) -> EarningTypeCodeBuilder:
        """Set the AccrueTimeOff flag."""
        self._fields["AccrueTimeOff"] = {"value": flag}
        return self

    def active(self, flag: bool) -> EarningTypeCodeBuilder:
        """Set the Active flag."""
        self._fields["Active"] = {"value": flag}
        return self

    def build(self) -> Dict[str, Dict[str, Any]]:
        """
        Return a fresh JSON payload dict; shallow-copy inner dicts
        so callers cannot mutate builder state.
        """
        return {k: v.copy() for k, v in self._fields.items()}

class PayrollWCCCodeBuilder:
    """
    Fluent builder for a Workers' Compensation Class Code (PayrollWCCCode) payload.

    Required structure:
      {
        "Country": { "value": <country> },
        "WCCCodes": [
          {
            "WCCCode":       { "value": code },
            "Description":   { "value": desc },
            "Active":        { "value": bool },
          },
          ... more entries ...
        ]
      }

    Example:
        builder = (
            PayrollWCCCodeBuilder()
            .country("US")
            .add_wcc_code("2222", "Test Code", active=True)
        )
        payload = builder.build()
    """

    def __init__(self) -> None:
        self._country: dict[str, Any] = {}
        self._wcc_list: list[dict[str, Any]] = []

    def country(self, country_code: str) -> PayrollWCCCodeBuilder:
        """Set the Country field (e.g., "US")."""
        self._country = {"value": country_code}
        return self

    def add_wcc_code(
        self,
        wcc_code: str,
        description: str,
        active: bool = True
    ) -> PayrollWCCCodeBuilder:
        """
        Append one WCCCodes entry.

        Args:
            wcc_code: the class code value (e.g., "2222")
            description: description text
            active: whether the code is active
        """
        entry: dict[str, Any] = {
            "WCCCode":      {"value": wcc_code},
            "Description":  {"value": description},
            "Active":       {"value": bool(active)},
        }
        self._wcc_list.append(entry)
        return self

    def build(self) -> dict[str, Any]:
        """
        Return a fresh JSON payload dict. Inner dicts/lists are copied
        so callers can’t mutate builder state.
        """
        # shallow-copy the country dict
        country_field = self._country.copy()
        # deep-copy each WCCCodes entry (copy each inner dict too)
        wcc_codes = [
            { field: val.copy() for field, val in entry.items() }
            for entry in self._wcc_list
        ]
        return {
            "Country": country_field,
            "WCCCodes": wcc_codes
        }

