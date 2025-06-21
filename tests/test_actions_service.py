# tests/test_actions_service.py
import pytest
import requests
import time

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.actions import ActionsService
from easy_acumatica.models.record_builder import RecordBuilder

API_VERSION = "24.200.001"
BASE = "https://fake"

class DummyResponse:
    """Fake Response for stubbing requests."""
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
    """Provides a mocked AcumaticaClient instance with the ActionsService attached."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    client_instance.actions = ActionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    """Provides an instance of the ActionsService."""
    return client.actions

# -------------------------------------------------------------------------
# execute_action Tests
# -------------------------------------------------------------------------

def test_execute_action_synchronous_success(monkeypatch, service):
    """Tests an action that completes immediately with a 204 status."""
    entity_payload = RecordBuilder().field("OrderNbr", "000001")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "post"
        assert url.endswith(f"/SalesOrder/ReopenOrder")
        
        body = kwargs.get("json", {})
        assert body["entity"] == entity_payload.build()
        assert "parameters" in body and not body["parameters"] # Ensure empty params are sent
        
        return DummyResponse(204) # Synchronous completion

    monkeypatch.setattr(service._client, "_request", fake_request)
    # This should execute without raising an error
    service.execute_action(API_VERSION, "SalesOrder", "ReopenOrder", entity_payload)

def test_execute_action_asynchronous_success(monkeypatch, service):
    """Tests an action that completes asynchronously after polling."""
    location_url = f"{BASE}/entity/Default/{API_VERSION}/SalesOrder/ReopenOrder/status/some-guid"
    
    # Mock the two-stage response
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)
    get_response_success = DummyResponse(204) # Final success status

    call_count = 0
    def fake_request(method, url, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1: # Initial POST
            return post_response
        if call_count == 2: # First GET poll
            assert url == location_url
            return get_response_pending
        if call_count == 3: # Second GET poll (success)
            return get_response_success
        pytest.fail("Made too many requests")

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    entity_payload = RecordBuilder().field("OrderNbr", "000001")
    service.execute_action(
        API_VERSION, "SalesOrder", "ReopenOrder", entity_payload, polling_interval_sec=0.01
    )
    assert call_count == 3

def test_execute_action_timeout_error(monkeypatch, service):
    """Tests that an action raises a RuntimeError if it times out."""
    location_url = f"{BASE}/entity/Default/{API_VERSION}/SalesOrder/ReopenOrder/status/some-guid"
    
    # Always return 202 to simulate a timeout
    post_response = DummyResponse(202, headers={"Location": location_url})
    get_response_pending = DummyResponse(202)

    def fake_request(method, url, **kwargs):
        return post_response if method.lower() == "post" else get_response_pending

    monkeypatch.setattr(service._client, "_request", fake_request)
    # Mock time.sleep to avoid waiting during the test
    monkeypatch.setattr(time, "sleep", lambda s: None)

    entity_payload = RecordBuilder().field("OrderNbr", "000001")
    with pytest.raises(RuntimeError, match="Action 'ReopenOrder' timed out"):
        service.execute_action(
            API_VERSION, "SalesOrder", "ReopenOrder", entity_payload, timeout_sec=0.1
        )

# -------------------------------------------------------------------------
# execute_custom_action Tests
# -------------------------------------------------------------------------

def test_execute_custom_action_success(monkeypatch, service):
    """Tests successful execution of a custom action with nested parameters."""
    entity_payload = RecordBuilder().field("id", "case-guid")
    custom_params = {
        "FilterPreview": {
            "Reason": {"type": "CustomStringField", "value": "Abandoned"}
        }
    }

    def fake_request(method, url, **kwargs):
        assert method.lower() == "post"
        assert url.endswith("/Case/Close")
        
        body = kwargs.get("json", {})
        assert body["entity"] == entity_payload.build()
        assert body["parameters"]["custom"] == custom_params
        
        return DummyResponse(204) # Assume synchronous for simplicity

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    service.execute_custom_action(
        API_VERSION,
        "Case",
        "Close",
        entity_payload,
        custom_parameters=custom_params
    )

