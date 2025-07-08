# tests/sub_services/test_employees_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.employees import EmployeesService
from easy_acumatica.models.employee_builder import EmployeeBuilder
from easy_acumatica.models.employee_payroll_class_builder import EmployeePayrollClassBuilder
from easy_acumatica.models.employee_payroll_settings_builder import EmployeePayrollSettingsBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"


class DummyResponse:
    def __init__(self, status_code: int, json_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body or {}
        self.headers = headers or {}


    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def client(monkeypatch):
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    client_instance.employees = EmployeesService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    return client.employees


def test_create_employee_success(monkeypatch, service):
    """Tests successful creation of an employee."""
    builder = (
        EmployeeBuilder()
        .status("Active")
        .contact_info(first_name="Jane", last_name="Doe")
        .financial_settings(APAccount="20000", PaymentMethod="CHECK")
        .employee_settings(DepartmentID="AFTERSALES", EmployeeClass="EMPHOURLY")
    )
    expected_response = {"EmployeeID": {"value": "EMP001"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Employee"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    result = service.create_employee(API_VERSION, builder)
    assert result == expected_response

def test_create_employee_error(monkeypatch, service):
    """Tests that an API error during creation is propagated."""
    builder = EmployeeBuilder().status("Invalid")

    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 422: Unprocessable Entity")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 422"):
        service.create_employee(API_VERSION, builder)

# -------------------------------------------------------------------------
# get_employees Tests
# -------------------------------------------------------------------------

def test_get_employees_success(monkeypatch, service):
    """Tests successful retrieval of a list of employees."""
    expected_response = [{"EmployeeID": {"value": "EMP001"}}, {"EmployeeID": {"value": "EMP002"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Employee"
        assert "params" not in kwargs or not kwargs.get("params")
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_employees(API_VERSION)
    assert result == expected_response

def test_get_employees_with_options(monkeypatch, service):
    """Tests retrieving employees with QueryOptions."""
    opts = QueryOptions(
        filter=F.EmployeeID == "EP00000001",
        expand=["ContactInfo", "EmployeeSettings"]
    )
    expected_response = [{"EmployeeID": {"value": "EP00000001"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_employees(API_VERSION, options=opts)
    assert result == expected_response

def test_get_employees_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_employees(API_VERSION)

def test_create_employee_payroll_class_success(monkeypatch, service):
    """Tests successful creation of an employee payroll class."""
    builder = EmployeePayrollClassBuilder().employee_payroll_class_id("TESTCLASS")
    expected_response = {"EmployeePayrollClassID": {"value": "TESTCLASS"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/EmployeePayrollClass"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_employee_payroll_class(API_VERSION, builder)
    assert result == expected_response

def test_update_employee_payroll_settings_success(monkeypatch, service):
    """Tests successful update of employee payroll settings."""
    builder = EmployeePayrollSettingsBuilder().employee_id("EP00000004")
    expected_response = {"EmployeeID": {"value": "EP00000004"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/EmployeePayrollSettings"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.update_employee_payroll_settings(API_VERSION, builder)
    assert result == expected_response