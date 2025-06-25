# tests/models/test_employee_builder.py

import pytest
from easy_acumatica.models.employee_builder import EmployeeBuilder

def test_builder_simple_fields():
    """Tests setting simple, top-level fields."""
    builder = EmployeeBuilder().status("Active")
    payload = builder.to_body()
    assert payload["Status"]["value"] == "Active"

def test_builder_contact_info_with_kwargs():
    """Tests setting contact info using both dedicated params and kwargs."""
    builder = EmployeeBuilder().contact_info(
        first_name="Jane", 
        last_name="Doe", 
        email="jane.doe@example.com",
        Title="Developer" # Example of a kwarg
    )
    payload = builder.to_body()
    contact_info = payload.get("ContactInfo", {})
    assert contact_info.get("FirstName", {}).get("value") == "Jane"
    assert contact_info.get("LastName", {}).get("value") == "Doe"
    assert contact_info.get("Email", {}).get("value") == "jane.doe@example.com"
    assert contact_info.get("Title", {}).get("value") == "Developer"

def test_builder_financial_settings_with_kwargs():
    """Tests setting financial settings using both dedicated params and kwargs."""
    builder = EmployeeBuilder().financial_settings(
        ap_account="20000", 
        payment_method="CHECK",
        PrepaymentAccount="12345" # Example of a kwarg
    )
    payload = builder.to_body()
    financial_settings = payload.get("FinancialSettings", {})
    assert financial_settings.get("APAccount", {}).get("value") == "20000"
    assert financial_settings.get("PaymentMethod", {}).get("value") == "CHECK"
    assert financial_settings.get("PrepaymentAccount", {}).get("value") == "12345"

def test_builder_employee_settings_with_kwargs():
    """Tests setting employee settings using both dedicated params and kwargs."""
    builder = EmployeeBuilder().employee_settings(
        department_id="AFTERSALES", 
        employee_class="EMPHOURLY",
        Calendar="MAIN" # Example of a kwarg
    )
    payload = builder.to_body()
    employee_settings = payload.get("EmployeeSettings", {})
    assert employee_settings.get("DepartmentID", {}).get("value") == "AFTERSALES"
    assert employee_settings.get("EmployeeClass", {}).get("value") == "EMPHOURLY"
    assert employee_settings.get("Calendar", {}).get("value") == "MAIN"


def test_builder_full_payload():
    """Tests building a complex payload with all components."""
    builder = (
        EmployeeBuilder()
        .status("Active")
        .contact_info(first_name="John", last_name="Smith")
        .financial_settings(terms="7D")
        .employee_settings(branch_id="HEADOFFICE")
    )
    payload = builder.to_body()
    assert payload["Status"]["value"] == "Active"
    assert "ContactInfo" in payload
    assert "FinancialSettings" in payload
    assert "EmployeeSettings" in payload
    assert payload["ContactInfo"]["FirstName"]["value"] == "John"
    assert payload["FinancialSettings"]["Terms"]["value"] == "7D"
    assert payload["EmployeeSettings"]["BranchID"]["value"] == "HEADOFFICE"

def test_to_body_returns_deep_copy():
    """Ensures that mutating the returned body does not affect the builder."""
    builder = EmployeeBuilder().contact_info(first_name="Test", last_name="User")
    body1 = builder.to_body()
    body1["ContactInfo"]["FirstName"]["value"] = "Modified"

    body2 = builder.to_body()
    assert body2["ContactInfo"]["FirstName"]["value"] == "Test"
