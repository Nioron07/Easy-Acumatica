# tests/test_time_entries_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.time_entries import TimeEntriesService
from easy_acumatica.models.time_entry_builder import TimeEntryBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "TimeEntry"

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
    client_instance.time_entries = TimeEntriesService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.time_entries

# --- Tests for get_time_entries ---

def test_get_time_entries_success(monkeypatch, service):
    """Tests successful retrieval of time entries."""
    expected_response = [{"TimeEntryCD": {"value": "TE000001"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_time_entries(API_VERSION)
    assert result == expected_response

def test_get_time_entries_with_options(monkeypatch, service):
    """Tests retrieving time entries with QueryOptions."""
    expected_response = [{"TimeEntryCD": {"value": "TE000002"}}]
    opts = QueryOptions(filter=F.Employee == "EP00000003")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_time_entries(API_VERSION, options=opts)
    assert result == expected_response

def test_get_time_entries_error(monkeypatch, service):
    """Tests that an API error is propagated correctly during a GET request."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_time_entries(API_VERSION)

# --- Tests for create_time_entry ---

def test_create_time_entry_success(monkeypatch, service):
    """Tests successful creation of a time entry."""
    builder = (
        TimeEntryBuilder()
        .summary("Test Entry")
        .employee("EP00000026")
        .time_spent("01:00")
    )
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_time_entry(API_VERSION, builder)
    assert result == expected_response

def test_create_time_entry_error(monkeypatch, service):
    """Tests that an API error is propagated correctly during a create request."""
    builder = TimeEntryBuilder().summary("Invalid Entry")

    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 422: Unprocessable Entity")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 422"):
        service.create_time_entry(API_VERSION, builder)