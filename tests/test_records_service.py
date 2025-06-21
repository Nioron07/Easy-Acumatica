# tests/test_records_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.models.record_builder import RecordBuilder
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY = "Customer"
BASE_PATH = f"/entity/Default/{API_VERSION}/{ENTITY}"


class DummyResponse:
    """Fake Response for stubbing requests."""
    # Corrected __init__ to accept headers
    def __init__(self, status_code: int, json_body=None, text_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body
        self._text = text_body or ""
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def client(monkeypatch):
    # Stub out real login/logout
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)

    return AcumaticaClient(
        base_url=BASE,
        username="u",
        password="p",
        tenant="t",
        branch="b",
        verify_ssl=False,
        persistent_login=True,
    )


@pytest.fixture
def service(client):
    return client.records


# -------------------------------------------------------------------------
# CREATE RECORD
# -------------------------------------------------------------------------
def test_create_record_success(monkeypatch, service):
    payload = RecordBuilder().field("CustomerID", "JOHNGOOD")
    created = {"CustomerID": {"value": "JOHNGOOD"}}

    def fake_request(method, url, **kwargs):
        assert method == "put"
        assert url.endswith(BASE_PATH)
        headers = kwargs["headers"]
        assert headers["If-None-Match"] == "*"
        assert headers["Accept"] == "application/json"
        assert kwargs["json"] == payload.build()
        return DummyResponse(200, created)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.create_record(API_VERSION, ENTITY, payload) == created


def test_create_record_duplicate_412(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        # simulate server-side 412 via RuntimeError
        raise RuntimeError("HTTP 412 Precondition Failed")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.create_record(API_VERSION, ENTITY, RecordBuilder().field("CustomerID", "JOHNGOOD"))


def test_create_record_server_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 500 Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.create_record(API_VERSION, ENTITY, RecordBuilder().field("CustomerID", "X"))


# -------------------------------------------------------------------------
# UPDATE RECORD
# -------------------------------------------------------------------------
def test_update_record_success(monkeypatch, service):
    flt = F.CustomerID == "JOHNGOOD"
    opts = QueryOptions(filter=flt)
    patch = RecordBuilder().field("CustomerClass", "DEFAULT")
    updated = [
        {"CustomerID": {"value": "JOHNGOOD"}, "CustomerClass": {"value": "DEFAULT"}}
    ]

    def fake_request(method, url, **kwargs):
        assert method == "put"
        assert url.endswith(BASE_PATH)
        assert kwargs["params"] == {"$filter": flt.build()}
        headers = kwargs["headers"]
        assert headers["If-Match"] == "*"
        assert headers["Accept"] == "application/json"
        assert kwargs["json"] == patch.build()
        return DummyResponse(200, updated)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.update_record(API_VERSION, ENTITY, patch, options=opts) == updated


def test_update_record_missing_412(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 412 Precondition Failed")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.update_record(API_VERSION, ENTITY, RecordBuilder().field("F", "V"))


def test_update_record_server_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 500 Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.update_record(API_VERSION, ENTITY, RecordBuilder().field("F", "V"))


# -------------------------------------------------------------------------
# GET BY KEY FIELD
# -------------------------------------------------------------------------
def test_get_record_by_key_field_success(monkeypatch, service):
    dummy = {"Foo": {"value": "Bar"}}

    def fake_request(method, url, **kwargs):
        assert method == "get"
        assert url.endswith(f"{BASE_PATH}/KeyField/KeyValue")
        headers = kwargs["headers"]
        assert headers["Accept"] == "application/json"
        return DummyResponse(200, dummy)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.get_record_by_key_field(API_VERSION, ENTITY, "KeyField", "KeyValue") == dummy


def test_get_record_by_key_field_with_filter_error(service):
    opts = QueryOptions(filter=F.X == F.Y)
    with pytest.raises(ValueError):
        service.get_record_by_key_field(API_VERSION, ENTITY, "KeyField", "KeyValue", options=opts)


def test_get_record_by_key_field_http_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 404 Not Found")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.get_record_by_key_field(API_VERSION, ENTITY, "KeyField", "KeyValue")


# -------------------------------------------------------------------------
# GET BY FILTER
# -------------------------------------------------------------------------
def test_get_records_by_filter_success(monkeypatch, service):
    flt = F.CustomerID == "A1"
    opts = QueryOptions(filter=flt, select=["CustomerID"], top=2)
    expected = [{"CustomerID": {"value": "A1"}}, {"CustomerID": {"value": "A2"}}]

    def fake_request(method, url, **kwargs):
        assert method == "get"
        assert kwargs["params"] == opts.to_params()
        return DummyResponse(200, expected)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.get_records_by_filter(API_VERSION, ENTITY, opts) == expected


def test_get_records_by_filter_no_filter_error(service):
    opts = QueryOptions(filter=None)
    with pytest.raises(ValueError):
        service.get_records_by_filter(API_VERSION, ENTITY, opts)


def test_get_records_by_filter_http_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 500 Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.get_records_by_filter(API_VERSION, ENTITY, QueryOptions(filter=F.C == F.D))


def test_get_records_by_filter_show_archived_header(monkeypatch, service):
    flt = F.CustomerID == "A1"
    opts = QueryOptions(filter=flt)
    expected = [{"CustomerID": {"value": "A1"}}]

    def fake_request(method, url, **kwargs):
        headers = kwargs["headers"]
        assert headers.get("PX-ApiArchive") == "SHOW"
        return DummyResponse(200, expected)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.get_records_by_filter(API_VERSION, ENTITY, opts, show_archived=True) == expected


# -------------------------------------------------------------------------
# GET BY ID
# -------------------------------------------------------------------------
def test_get_record_by_id_success(monkeypatch, service):
    dummy = {"ID": "000123", "Status": {"value": "Open"}}

    def fake_request(method, url, **kwargs):
        assert method == "get"
        assert url.endswith(f"{BASE_PATH}/000123")
        return DummyResponse(200, dummy)

    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.get_record_by_id(API_VERSION, ENTITY, "000123") == dummy


def test_get_record_by_id_with_filter_error(service):
    opts = QueryOptions(filter= F.X == F.Y)
    with pytest.raises(ValueError):
        service.get_record_by_id(API_VERSION, ENTITY, "000123", options=opts)


def test_get_record_by_id_http_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 403 Forbidden")

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.get_record_by_id(API_VERSION, ENTITY, "000123")

# -------------------------------------------------------------------------
# SCHEMA AND REPORTING
# -------------------------------------------------------------------------
def test_get_custom_field_schema_success(monkeypatch, service):
    schema = {"Field": {"type": "CustomString"}}
    def fake_request(method, url, **kwargs):
        assert url.endswith("/$adHocSchema")
        return DummyResponse(200, schema)
    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.get_custom_field_schema(API_VERSION, ENTITY) == schema

def test_request_report_success(monkeypatch, service):
    location_url = f"{BASE}/entity/Report/0001/report/PDF/some-guid"
    
    # Mock the two-stage response for reports
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)
    get_response_success = DummyResponse(200, text_body="report content")

    call_count = 0
    def fake_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1: # Initial POST
            assert method == "post"
            return post_response
        if call_count == 2: # First GET (pending)
            assert method == "get"
            assert url == location_url
            return get_response_pending
        if call_count == 3: # Second GET (success)
            assert method == "get"
            return get_response_success
        pytest.fail("Too many requests made")

    monkeypatch.setattr(service._client, "_request", fake_request)
    response = service.request_report(
        "MyReport", "Report", "0001", polling_interval_sec=0.1
    )
    assert response.status_code == 200
    assert response._text == "report content"

def test_request_report_timeout(monkeypatch, service):
    location_url = f"{BASE}/entity/Report/0001/report/PDF/some-guid"
    
    # Always return 202 to simulate a report that never finishes
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)

    def fake_request(method, url, **kwargs):
        if method == "post":
            return post_response
        return get_response_pending

    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError, match="Report generation timed out"):
        service.request_report(
            "MyReport", "Report", "0001", timeout_sec=0.5, polling_interval_sec=0.1
        )

# -------------------------------------------------------------------------
# DELETE RECORDS
# -------------------------------------------------------------------------
def test_delete_record_by_id_success(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        assert method == "delete"
        assert url.endswith(f"{BASE_PATH}/some-guid")
        return DummyResponse(204)
    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.delete_record_by_id(API_VERSION, ENTITY, "some-guid") is None

def test_delete_record_by_id_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 404 Not Found")
    monkeypatch.setattr(service._client, "_request", fake_request)
    with pytest.raises(RuntimeError):
        service.delete_record_by_id(API_VERSION, ENTITY, "bad-guid")

def test_delete_record_by_key_field_success(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        assert method == "delete"
        assert url.endswith(f"{BASE_PATH}/Type/Number")
        return DummyResponse(204)
    monkeypatch.setattr(service._client, "_request", fake_request)
    assert service.delete_record_by_key_field(API_VERSION, ENTITY, "Type", "Number") is None
