# tests/sub_services/test_payments_service.py

import pytest
import requests
import time

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.payments import PaymentsService
from easy_acumatica.models.payment_builder import PaymentBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"


class DummyResponse:
    """Minimal fake Response for mocking."""
    def __init__(self, status_code: int, json_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body if json_body is not None else {}
        self.headers = headers or {}


    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def client(monkeypatch):
    """Provides a mocked AcumaticaClient instance."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    client_instance.payments = PaymentsService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    """Provides an instance of the PaymentsService."""
    return client.payments


def test_create_payment_success(monkeypatch, service):
    """Tests successful creation of a payment."""
    builder = (
        PaymentBuilder()
        .cash_account("10250ST")
        .customer_id("FRUITICO")
        .hold(False)
        .payment_amount(235.27)
        .type("Payment")
    )
    expected_response = {"ReferenceNbr": {"value": "000123"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Payment"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_payment(API_VERSION, builder)
    assert result == expected_response


def test_create_payment_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    builder = PaymentBuilder().customer_id("ERROR")

    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 400: Bad Request")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 400"):
        service.create_payment(API_VERSION, builder)

# -------------------------------------------------------------------------
# get_payment Tests
# -------------------------------------------------------------------------

def test_get_payment_success(monkeypatch, service):
    """Tests successful retrieval of a single payment."""
    payment_type = "Payment"
    ref_nbr = "000123"
    expected_response = {"ReferenceNbr": {"value": ref_nbr}, "Type": {"value": payment_type}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Payment/{payment_type}/{ref_nbr}"
        assert "params" not in kwargs or not kwargs.get("params")
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_payment(API_VERSION, payment_type, ref_nbr)
    assert result == expected_response

def test_get_payment_with_options(monkeypatch, service):
    """Tests retrieval with QueryOptions for $select and $expand."""
    payment_type = "Prepayment"
    ref_nbr = "000456"
    opts = QueryOptions(
        select=["ReferenceNbr", "Status"],
        expand=["ApplicationHistory"]
    )
    expected_response = {"ReferenceNbr": {"value": ref_nbr}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Payment/{payment_type}/{ref_nbr}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_payment(API_VERSION, payment_type, ref_nbr, options=opts)
    assert result == expected_response

def test_get_payment_not_found(monkeypatch, service):
    """Tests that a 404 error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 404: Not Found")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 404"):
        service.get_payment(API_VERSION, "Payment", "nonexistent")

def test_get_payment_with_filter_in_options_raises_error(service):
    """Tests that using a filter in QueryOptions raises a ValueError."""
    opts = QueryOptions(filter=F.Status == "Open")
    with pytest.raises(ValueError):
        service.get_payment(API_VERSION, "Payment", "123", options=opts)
        
# -------------------------------------------------------------------------
# release_payment Tests
# -------------------------------------------------------------------------

def test_release_payment_synchronous_success(monkeypatch, service):
    """Tests a release action that completes immediately with a 204 status."""
    def fake_request(method, url, **kwargs):
        assert method.lower() == "post"
        assert url.endswith("/Payment/Release")
        # Body should contain the entity with keys
        body = kwargs.get("json")
        assert body["entity"]["Type"]["value"] == "Payment"
        assert body["entity"]["ReferenceNbr"]["value"] == "000077"
        return DummyResponse(204) # Synchronous completion

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    # This should execute without raising an error
    service.release_payment(API_VERSION, "Payment", "000077")


def test_release_payment_asynchronous_success(monkeypatch, service):
    """Tests a release action that completes asynchronously after polling."""
    location_url = f"{BASE}/entity/Default/{API_VERSION}/Payment/Release/status/some-guid"
    
    # Mock the two-stage response
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)
    get_response_success = DummyResponse(204) # Final success status

    call_count = 0
    def fake_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1: # Initial POST
            assert method.lower() == "post"
            assert url.endswith("/Payment/Release")
            return post_response
        elif call_count == 2: # First GET poll
            assert method.lower() == "get"
            assert url == location_url
            return get_response_pending
        elif call_count == 3: # Second GET poll (success)
            assert method.lower() == "get"
            return get_response_success
        pytest.fail("Made too many requests")

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    # This should complete without raising an error
    service.release_payment(API_VERSION, "Payment", "000077", polling_interval_sec=0.01)
    assert call_count == 3

def test_release_payment_timeout_error(monkeypatch, service):
    """Tests that the release action raises a RuntimeError if it times out."""
    location_url = f"{BASE}/entity/Default/{API_VERSION}/Payment/Release/status/some-guid"
    
    # Always return 202 to simulate a timeout
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)

    def fake_request(method, url, **kwargs):
        return post_response if method.lower() == "post" else get_response_pending

    monkeypatch.setattr(service._client, "_request", fake_request)
    monkeypatch.setattr(time, "sleep", lambda s: None) # Avoid waiting in test

    with pytest.raises(RuntimeError, match="Action 'Release Payment' timed out"):
        service.release_payment(API_VERSION, "Payment", "000077", timeout_sec=0.1)
