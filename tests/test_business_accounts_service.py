

# tests/test_business_accounts_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.business_accounts import BusinessAccountsService
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "BusinessAccount"

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
    client_instance.business_accounts = BusinessAccountsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.business_accounts

def test_get_business_accounts_success(monkeypatch, service):
    """Tests successful retrieval of business accounts."""
    expected_response = [{"BusinessAccountID": {"value": "C00001"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_business_accounts(API_VERSION)
    assert result == expected_response

def test_get_business_accounts_with_options(monkeypatch, service):
    """Tests retrieving business accounts with QueryOptions."""
    expected_response = [{"BusinessAccountID": {"value": "C00002"}}]
    opts = QueryOptions(filter=F.BusinessAccountID == "C00002", expand=["MainContact"])

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_business_accounts(API_VERSION, options=opts)
    assert result == expected_response

def test_get_business_accounts_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        # Simulate an API error by raising a RuntimeError, which is what _raise_with_detail does
        raise RuntimeError("Acumatica API error 500: Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_business_accounts(API_VERSION)
