# tests/test_employee_payroll_builders.py

import pytest
from easy_acumatica.models.employee_payroll_class_builder import EmployeePayrollClassBuilder
from easy_acumatica.models.employee_payroll_settings_builder import EmployeePayrollSettingsBuilder

def test_employee_payroll_class_builder():
    """Tests the EmployeePayrollClassBuilder."""
    builder = (
        EmployeePayrollClassBuilder()
        .employee_payroll_class_id("TESTCLASS")
        .description("Test CLASS")
        .payroll_defaults(EmployeeType="Hourly", PayGroup="WEEKLY")
        .add_pto_default(PTOBank="PTO", EffectiveDate="01/01/2016")
    )
    payload = builder.to_body()
    assert payload["EmployeePayrollClassID"]["value"] == "TESTCLASS"
    assert payload["PayrollDefaults"]["EmployeeType"]["value"] == "Hourly"
    assert len(payload["PTODefaults"]) == 1

def test_employee_payroll_settings_builder():
    """Tests the EmployeePayrollSettingsBuilder."""
    work_location_details = [{"LocationID": {"value": "BELLEVUE"}, "DefaultWorkLocation": {"value": False}}]
    builder = (
        EmployeePayrollSettingsBuilder()
        .employee_id("EP00000004")
        .class_id("HOURLY")
        .work_locations(False, work_location_details)
        .add_employment_record(StartDate="2021-05-13", Position="ACCOUNTANT")
    )
    payload = builder.to_body()
    assert payload["EmployeeID"]["value"] == "EP00000004"
    assert not payload["WorkLocations"]["WorkLocationClassDefaults"]["value"]
    assert len(payload["EmploymentRecords"]) == 1