# tests/test_companies_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.companies import CompaniesService

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
    client_instance.companies = CompaniesService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.companies

def test_get_structure_success(monkeypatch, service):
    """Tests successful retrieval of the company structure."""
    expected_results = [{"Company": "Company A", "Branch": "Branch 1"}]
    response_payload = {"Results": expected_results}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/CompaniesStructure"
        assert kwargs.get("params") == {"$expand": "Results"}
        assert kwargs.get("json") == {}
        return DummyResponse(200, response_payload)

    monkeypatch.setattr(service._client, "_request", fake_request)

    result = service.get_structure(API_VERSION)
    assert result == expected_results

def test_get_structure_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_structure(API_VERSION)