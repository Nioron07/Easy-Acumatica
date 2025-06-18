# tests/test_records.py
import pytest
from requests import HTTPError
from urllib.parse import unquote_plus
from easy_acumatica import AcumaticaClient
from easy_acumatica.models.record_builder import RecordBuilder
from easy_acumatica.models.filter_builder import QueryOptions, Filter

API_VERSION = "24.200.001"
BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"
CUSTOMER_URL = f"{BASE}/entity/Default/{API_VERSION}/Customer"


# ---------------------------------------------------------------------
# shared client fixture
# ---------------------------------------------------------------------
@pytest.fixture
def client(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)
    return AcumaticaClient(
        base_url=BASE,
        username="u",
        password="p",
        tenant="t",
        branch="b",
        verify_ssl=False,
    )


# ---------------------------------------------------------------------
# CREATE RECORD
# ---------------------------------------------------------------------
def test_create_record_success(requests_mock, client):
    payload = RecordBuilder().field("CustomerID", "JOHNGOOD")
    created = {"CustomerID": {"value": "JOHNGOOD"}}

    requests_mock.put(CUSTOMER_URL, status_code=200, json=created)

    res = client.records.create_record(API_VERSION, "Customer", payload)
    assert res == created

    req = requests_mock.request_history[-1]
    assert req.headers["If-None-Match"] == "*"
    assert req.json()["CustomerID"]["value"] == "JOHNGOOD"


def test_create_record_duplicate_412(requests_mock, client):
    payload = RecordBuilder().field("CustomerID", "JOHNGOOD")
    requests_mock.put(CUSTOMER_URL, status_code=412, json="already exists")

    with pytest.raises(RuntimeError):
        client.records.create_record(API_VERSION, "Customer", payload)


def test_create_record_server_error(requests_mock, client):
    payload = RecordBuilder().field("CustomerID", "JOHNGOOD")
    requests_mock.put(CUSTOMER_URL, status_code=500, text="boom")

    with pytest.raises(RuntimeError):
        client.records.create_record(API_VERSION, "Customer", payload)


# ---------------------------------------------------------------------
# UPDATE RECORD
# ---------------------------------------------------------------------
def test_update_record_success(requests_mock, client):
    flt = Filter().eq("CustomerID", "JOHNGOOD")
    opts = QueryOptions(filter=flt)

    patch = RecordBuilder().field("CustomerClass", "DEFAULT")
    updated = [{"CustomerID": {"value": "JOHNGOOD"},
                "CustomerClass": {"value": "DEFAULT"}}]

    requests_mock.put(CUSTOMER_URL, status_code=200, json=updated)

    res = client.records.update_record(
        API_VERSION, "Customer", patch, options=opts
    )
    assert res == updated

    req = requests_mock.request_history[-1]
    assert req.headers["If-Match"] == "*"
    decoded = unquote_plus(req.query).lower()
    assert "customerid eq 'johngood'" in decoded


def test_update_record_missing_412(requests_mock, client):
    patch = RecordBuilder().field("CustomerClass", "DEFAULT")
    requests_mock.put(CUSTOMER_URL, status_code=412, json="not found")

    with pytest.raises(RuntimeError):
        client.records.update_record(API_VERSION, "Customer", patch)


def test_update_record_server_error(requests_mock, client):
    patch = RecordBuilder().field("CustomerClass", "DEFAULT")
    requests_mock.put(CUSTOMER_URL, status_code=500, text="oops")

    with pytest.raises(RuntimeError):
        client.records.update_record(API_VERSION, "Customer", patch)


# ---------------------------------------------------------------------
# LOGIN FAILURE (generic for the service)
# ---------------------------------------------------------------------
def test_records_login_failure(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=403)
    with pytest.raises(HTTPError):
        AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False) \
            .records.create_record(API_VERSION, "Customer", {})
