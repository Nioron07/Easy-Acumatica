# tests/test_activities_service.py
import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.activities import ActivitiesService

API_VERSION = "24.200.001"
BASE = "https://fake"

class DummyResponse:
    """Fake Response for stubbing requests."""
    def __init__(self, status_code: int, json_body=None):
        self.status_code = status_code
        self._json = json_body or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json

@pytest.fixture
def client(monkeypatch):
    """Provides a mocked AcumaticaClient instance with the ActivitiesService attached."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    # Add the service to the client instance for testing
    client_instance.activities = ActivitiesService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    """Provides an instance of the ActivitiesService."""
    return client.activities

# -------------------------------------------------------------------------
# Test Cases for each entity type
# -------------------------------------------------------------------------

@pytest.mark.parametrize(
    "method_name, entity_note_id, expected_entity_type",
    [
        ("create_activity_linked_to_case", "case-guid-123", "PX.Objects.CR.CRCase"),
        ("create_activity_linked_to_customer", "customer-guid-456", "PX.Objects.AR.Customer"),
        ("create_activity_linked_to_lead", "lead-guid-789", "PX.Objects.CR.CRLead"),
    ]
)
def test_create_linked_activity_success(monkeypatch, service, method_name, entity_note_id, expected_entity_type):
    """
    Tests that each public method correctly calls the internal helper
    with the right entity type and parameters.
    """
    summary = "Test Summary"
    details = "Test Details"
    activity_type = "T"  # Task
    expected_response = {"ActivityID": {"value": 999}}

    # Mock the internal helper method to intercept its arguments
    def fake_create_linked_activity(
        api_version, related_entity_note_id, related_entity_type, 
        summary, details, activity_type
    ):
        assert api_version == API_VERSION
        assert related_entity_note_id == entity_note_id
        assert related_entity_type == expected_entity_type
        assert summary == summary
        assert details == details
        assert activity_type == activity_type
        return expected_response

    monkeypatch.setattr(service, "_create_linked_activity", fake_create_linked_activity)

    # Get the actual public method from the service object
    method_to_test = getattr(service, method_name)
    
    # Call the public method
    result = method_to_test(
        api_version=API_VERSION,
        # The first argument name changes based on the method, so we use a generic name
        **{f"{method_name.split('_')[-1]}_note_id": entity_note_id},
        summary=summary,
        details=details,
        activity_type=activity_type
    )

    assert result == expected_response

def test_create_linked_activity_http_request(monkeypatch, service):
    """
    Tests that the internal _create_linked_activity method constructs
    the correct HTTP PUT request.
    """
    expected_payload = {
        "Summary": {"value": "A summary"},
        "Type": {"value": "M"},
        "ActivityDetails": {"value": "Some details"},
        "RelatedEntityNoteID": {"value": "any-guid"},
        "RelatedEntityType": {"value": "Any.EntityType"},
    }

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Activity"
        assert kwargs.get("json") == expected_payload
        return DummyResponse(200, {"id": 1})

    monkeypatch.setattr(service._client, "_request", fake_request)

    # Call the internal method directly to test the request logic
    service._create_linked_activity(
        api_version=API_VERSION,
        related_entity_note_id="any-guid",
        related_entity_type="Any.EntityType",
        summary="A summary",
        details="Some details",
        activity_type="M"
    )

def test_create_activity_error_handling(monkeypatch, service):
    """
    Tests that the service correctly propagates exceptions from the HTTP client.
    """
    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 500: Server exploded")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Server exploded"):
        service.create_activity_linked_to_case(
            api_version=API_VERSION,
            case_note_id="any-id",
            summary="test",
            details="test"
        )
