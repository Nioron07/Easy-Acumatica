# tests/sub_services/test_ledgers_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.ledgers import LedgersService
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
    client_instance.ledgers = LedgersService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    return client.ledgers


def test_get_ledgers_success(monkeypatch, service):
    """Tests successful retrieval of a list of ledgers."""
    expected_response = [{"LedgerID": {"value": "ACTUAL"}}, {"LedgerID": {"value": "BUDGET"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Ledger"
        assert "params" not in kwargs or not kwargs.get("params")
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_ledgers(API_VERSION)
    assert result == expected_response

def test_get_ledgers_with_options(monkeypatch, service):
    """Tests retrieving ledgers with QueryOptions."""
    opts = QueryOptions(
        filter=F.LedgerID == "ACTUAL",
        select=["LedgerID", "Description"],
        expand=["Branches"]
    )
    expected_response = [{"LedgerID": {"value": "ACTUAL"}, "Description": {"value": "Actual Ledger"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_ledgers(API_VERSION, options=opts)
    assert result == expected_response

def test_get_ledgers_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_ledgers(API_VERSION)
