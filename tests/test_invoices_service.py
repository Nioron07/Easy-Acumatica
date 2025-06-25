# tests/sub_services/test_invoices_service.py

import pytest
import requests
import time

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.invoices import InvoicesService
from easy_acumatica.models.invoice_builder import InvoiceBuilder
from easy_acumatica.models.query_builder import QueryOptions, CustomField
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
    client_instance.invoices = InvoicesService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    return client.invoices


def test_create_invoice_success(monkeypatch, service):
    """Tests successful creation of an invoice."""
    builder = (
        InvoiceBuilder()
        .set("Customer", "AACUSTOMER")
        .set("Description", "Invoice with overridden tax")
        .set("IsTaxValid", True)
        .add_detail_line("CONSULTING", 10, 100.0)
        .add_tax_detail("CAGST", 1000.0, 150.0)
    )
    expected_response = {"ReferenceNbr": {"value": "INV001"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Invoice"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    opts = QueryOptions(expand=["Details", "TaxDetails"])
    result = service.create_invoice(API_VERSION, builder, options=opts)
    assert result == expected_response

def test_create_invoice_error(monkeypatch, service):
    """Tests that an API error during creation is propagated."""
    builder = InvoiceBuilder().set("Customer", "INVALID")

    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 422: Unprocessable Entity")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 422"):
        service.create_invoice(API_VERSION, builder)

# -------------------------------------------------------------------------
# get_invoices Tests
# -------------------------------------------------------------------------

def test_get_invoices_success(monkeypatch, service):
    """Tests successful retrieval of a list of invoices."""
    expected_response = [{"ReferenceNbr": {"value": "INV001"}}, {"ReferenceNbr": {"value": "INV002"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Invoice"
        assert "params" not in kwargs or not kwargs.get("params")
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_invoices(API_VERSION)
    assert result == expected_response

def test_get_invoices_with_options(monkeypatch, service):
    """Tests retrieving invoices with QueryOptions."""
    opts = QueryOptions(
        filter=F.Status == "Open",
        select=["ReferenceNbr", "Amount"],
        top=10
    )
    expected_response = [{"ReferenceNbr": {"value": "INV003"}, "Amount": {"value": 100.0}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_invoices(API_VERSION, options=opts)
    assert result == expected_response

def test_get_invoices_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_invoices(API_VERSION)

# -------------------------------------------------------------------------
# update_invoice Tests
# -------------------------------------------------------------------------

def test_update_invoice_success(monkeypatch, service):
    """Tests successful update of an invoice."""
    note_id = "some-guid-123"
    builder = (
        InvoiceBuilder()
        .id(note_id)
        .set_custom_field("CurrentDocument", "TaxZoneID", "AVALARA")
    )
    
    opts = QueryOptions(custom=[CustomField.field("CurrentDocument", "TaxZoneID")])

    expected_response = {"id": note_id, "custom": {"CurrentDocument": {"TaxZoneID": {"value": "AVALARA"}}}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Invoice"
        
        assert kwargs.get("params") == opts.to_params()
        
        body = kwargs.get("json")
        assert body.get("id") == note_id
        assert body["custom"]["CurrentDocument"]["TaxZoneID"]["value"] == "AVALARA"

        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.update_invoice(API_VERSION, builder, options=opts)
    assert result == expected_response

def test_update_invoice_missing_id_raises_error(service):
    """Tests that update_invoice raises an error if the builder has no id."""
    builder = InvoiceBuilder().description("No ID here")
    with pytest.raises(ValueError, match="must have the 'id' set"):
        service.update_invoice(API_VERSION, builder)

# -------------------------------------------------------------------------
# release_invoice Tests
# -------------------------------------------------------------------------

def test_release_invoice_asynchronous_success(monkeypatch, service):
    """Tests a release action that completes asynchronously after polling."""
    note_id = "async-guid"
    location_url = f"{BASE}/entity/Default/{API_VERSION}/Invoice/ReleaseInvoice/status/some-guid"
    
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)
    get_response_success = DummyResponse(204)

    call_count = 0
    def fake_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return post_response
        elif call_count <= 3:
            return get_response_pending if call_count < 3 else get_response_success
        pytest.fail("Made too many requests")

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    service.release_invoice(API_VERSION, note_id, polling_interval_sec=0.01)
    assert call_count == 3

def test_release_invoice_timeout_error(monkeypatch, service):
    """Tests that the release action raises a RuntimeError if it times out."""
    note_id = "timeout-guid"
    location_url = f"{BASE}/entity/Default/{API_VERSION}/Invoice/ReleaseInvoice/status/some-guid"
    
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)

    def fake_request(method, url, **kwargs):
        return post_response if method.lower() == "post" else get_response_pending

    monkeypatch.setattr(service._client, "_request", fake_request)
    monkeypatch.setattr(time, "sleep", lambda s: None)

    with pytest.raises(RuntimeError, match="Action 'Release Invoice' timed out"):
        service.release_invoice(API_VERSION, note_id, timeout_sec=0.1)
