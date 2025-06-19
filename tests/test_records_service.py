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

# ---------------------------------------------------------------------
# GET RECORD BY KEY FIELD
# ---------------------------------------------------------------------
def test_get_record_by_key_field_success(requests_mock, client):
    # no filter → simply GET /Customer/KeyField/KeyValue
    dummy = {"Foo": {"value": "Bar"}}
    requests_mock.get(f"{CUSTOMER_URL}/KeyField/KeyValue", status_code=200, json=dummy)

    res = client.records.get_record_by_key_field(
        API_VERSION, "Customer", "KeyField", "KeyValue"
    )
    assert res == dummy
    # verify that Accept header is present
    last = requests_mock.request_history[-1]
    assert last.headers["Accept"] == "application/json"


def test_get_record_by_key_field_with_filter_error(client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    opts = QueryOptions(filter=Filter().eq("X", "Y"))
    with pytest.raises(ValueError) as exc:
        client.records.get_record_by_key_field(
            API_VERSION, "Customer", "KeyField", "KeyValue", opts
        )
    assert "QueryOptions.filter must be None" in str(exc.value)


# ---------------------------------------------------------------------
# GET RECORDS BY FILTER
# ---------------------------------------------------------------------
def test_get_records_by_filter_success(requests_mock, client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    # must supply a filter
    flt = Filter().eq("CustomerID", "A1")
    opts = QueryOptions(filter=flt, select=["CustomerID"], top=2)
    encoded = "?$filter=CustomerID%20eq%20'A1'&$select=CustomerID&$top=2"
    expected = [{"CustomerID": {"value": "A1"}}, {"CustomerID": {"value": "A2"}}]

    requests_mock.get(f"{CUSTOMER_URL}{encoded}", status_code=200, json=expected)

    res = client.records.get_records_by_filter(API_VERSION, "Customer", opts)
    assert res == expected

    last = requests_mock.request_history[-1]
    assert last.headers["Accept"] == "application/json"


def test_get_records_by_filter_no_filter_error(client):
    from easy_acumatica.models.filter_builder import QueryOptions

    opts = QueryOptions(filter=None)
    with pytest.raises(ValueError) as exc:
        client.records.get_records_by_filter(API_VERSION, "Customer", opts)
    assert "QueryOptions.filter must be set" in str(exc.value)


# ---------------------------------------------------------------------
# GET RECORD BY ID
# ---------------------------------------------------------------------
def test_get_record_by_id_success(requests_mock, client):
    dummy = {"ID": "000123", "Status": {"value": "Open"}}
    requests_mock.get(f"{CUSTOMER_URL}/000123", status_code=200, json=dummy)

    res = client.records.get_record_by_id(
        API_VERSION, "Customer", "000123"
    )
    assert res == dummy
    last = requests_mock.request_history[-1]
    assert last.headers["Accept"] == "application/json"


def test_get_record_by_id_with_filter_error(client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    opts = QueryOptions(filter=Filter().eq("X", "Y"))
    with pytest.raises(ValueError) as exc:
        client.records.get_record_by_id(API_VERSION, "Customer", "000123", opts)
    assert "QueryOptions.filter must be None" in str(exc.value)


# ---------------------------------------------------------------------
# GET RECORD BY KEY FIELD — error path
# ---------------------------------------------------------------------
def test_get_record_by_key_field_http_error(requests_mock, client):
    # simulate a 404 Not Found with JSON body
    requests_mock.get(f"{CUSTOMER_URL}/KeyField/KeyValue", status_code=404, json={"message": "Not found"})
    with pytest.raises(RuntimeError) as exc:
        client.records.get_record_by_key_field(
            API_VERSION, "Customer", "KeyField", "KeyValue"
        )
    # should contain the status code and detail
    assert "404" in str(exc.value)
    assert "Not found" in str(exc.value)


# ---------------------------------------------------------------------
# GET RECORDS BY FILTER — error path
# ---------------------------------------------------------------------
def test_get_records_by_filter_http_error(requests_mock, client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    flt = Filter().eq("CustomerID", "A1")
    opts = QueryOptions(filter=flt)
    encoded = "?$filter=CustomerID%20eq%20'A1'"

    # simulate a 500 Internal Server Error with plain-text body
    requests_mock.get(f"{CUSTOMER_URL}{encoded}", status_code=500, text="Server exploded")
    with pytest.raises(RuntimeError) as exc:
        client.records.get_records_by_filter(API_VERSION, "Customer", opts)
    assert "500" in str(exc.value)
    assert "Server exploded" in str(exc.value)


# ---------------------------------------------------------------------
# GET RECORD BY ID — error path
# ---------------------------------------------------------------------
def test_get_record_by_id_http_error(requests_mock, client):
    # simulate a 403 Forbidden with no JSON body
    requests_mock.get(f"{CUSTOMER_URL}/000123", status_code=403, text="")
    with pytest.raises(RuntimeError) as exc:
        client.records.get_record_by_id(
            API_VERSION, "Customer", "000123"
        )
    # should at least report the status code
    assert "403" in str(exc.value)

# ---------------------------------------------------------------------
# GET RECORDS BY FILTER — archived header
# ---------------------------------------------------------------------
def test_get_records_by_filter_show_archived_header_success(requests_mock, client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    flt = Filter().eq("CustomerID", "A1")
    opts = QueryOptions(filter=flt)
    encoded = "?$filter=CustomerID%20eq%20'A1'"
    expected = [{"CustomerID": {"value": "A1"}}]

    # stub the response
    requests_mock.get(f"{CUSTOMER_URL}{encoded}", status_code=200, json=expected)

    # call with show_archived=True
    res = client.records.get_records_by_filter(
        API_VERSION, "Customer", opts, show_archived=True
    )
    assert res == expected

    # verify the PX-ApiArchive header was sent
    last = requests_mock.request_history[-1]
    assert last.headers.get("PX-ApiArchive") == "SHOW"


def test_get_records_by_filter_show_archived_header_error(requests_mock, client):
    from easy_acumatica.models.filter_builder import QueryOptions, Filter

    flt = Filter().eq("CustomerID", "A1")
    opts = QueryOptions(filter=flt)
    encoded = "?$filter=CustomerID%20eq%20'A1'"

    # simulate server error
    requests_mock.get(f"{CUSTOMER_URL}{encoded}", status_code=500, text="Server boom")

    with pytest.raises(RuntimeError) as exc:
        client.records.get_records_by_filter(
            API_VERSION, "Customer", opts, show_archived=True
        )
    # header should still have been sent
    last = requests_mock.request_history[-1]
    assert last.headers.get("PX-ApiArchive") == "SHOW"
    # error message contains status and body
    assert "500" in str(exc.value)
    assert "Server boom" in str(exc.value)