# tests/test_cases_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.cases import CasesService
from easy_acumatica.models.case_builder import CaseBuilder
from easy_acumatica.models.query_builder import QueryOptions

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
    client_instance.cases = CasesService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.cases

def test_create_case_success(monkeypatch, service):
    """Tests successful creation of a case."""
    builder = (
        CaseBuilder()
        .class_id("JREPAIR")
        .business_account("ABAKERY")
        .contact_id("100211")
        .subject("Some Subject")
    )
    expected_response = {"CaseID": {"value": "000005"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Case"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)

    result = service.create_case(API_VERSION, builder)
    assert result == expected_response

def test_link_case_to_another_case_success(monkeypatch, service):
    """Tests successfully linking a case to another case."""
    builder = (
        CaseBuilder()
        .class_id("SERVCONS")
        .business_account("GOODFOOD")
        .subject("Billing plan")
        .add_related_case("000004")
    )
    expected_response = {"CaseID": {"value": "000006"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Case"
        assert kwargs.get("params") == {"$expand": "RelatedCases"}
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)

    result = service.link_case_to_another_case(API_VERSION, builder)
    assert result == expected_response