import pytest
import requests

from easy_acumatica.client import AcumaticaClient
from easy_acumatica.sub_services.work_locations import WorkLocationsService
from easy_acumatica.models.work_location_builder import WorkLocationBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "WorkLocation"

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
    # Manually attach the service since it's new
    client_instance.work_locations = WorkLocationsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.work_locations

# --- Tests for create_work_location ---

def test_create_work_location_success(monkeypatch, service):
    """Tests successful creation of a work location."""
    builder = (
        WorkLocationBuilder()
        .work_location_id("BELLEVUE")
        .active(True)
        .address_info(city="Bellevue")
    )
    expected_response = builder.to_body()
    opts = QueryOptions(expand=["AddressInfo"])

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_work_location(API_VERSION, builder, options=opts)
    assert result == expected_response

# --- Tests for get_work_locations ---

def test_get_work_locations_with_options(monkeypatch, service):
    """Tests retrieving work locations with QueryOptions."""
    expected_response = [{"WorkLocationID": {"value": "SPECIFIC"}}]
    opts = QueryOptions(filter=F.WorkLocationID == "SPECIFIC")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_work_locations(API_VERSION, options=opts)
    assert result == expected_response