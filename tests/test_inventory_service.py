# tests/test_inventory_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.inventory import InventoryService
from easy_acumatica.models.inventory_issue_builder import InventoryIssueBuilder
from easy_acumatica.sub_services.inquiries import InquiriesService
from easy_acumatica.models.item_warehouse_builder import ItemWarehouseBuilder

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "InventoryIssue"

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
    client_instance.inventory = InventoryService(client_instance)
    client_instance.inquiries = InquiriesService(client_instance)
    # The new method uses the ActionsService, so we need to add it to the mock client
    from easy_acumatica.sub_services.actions import ActionsService
    client_instance.actions = ActionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.inventory

def test_create_inventory_issue_success(monkeypatch, service):
    """Tests successful creation of an inventory issue."""
    builder = InventoryIssueBuilder().description("Test")
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_inventory_issue(API_VERSION, builder)
    assert result == expected_response

def test_get_release_status_success(monkeypatch, service):
    """Tests successful retrieval of the release status."""
    location_url = f"{BASE}/entity/Default/24.200.001/InventoryIssue/ReleaseInventoryIssue/status/some-guid"

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == location_url
        return DummyResponse(202)

    monkeypatch.setattr(service._client, "_request", fake_request)
    response = service.get_release_status(location_url)
    assert response.status_code == 202

def test_release_inventory_issue_success(monkeypatch, service):
    """Tests successful release of an inventory issue."""
    reference_nbr = "000055"

    def fake_request(method, url, **kwargs):
        if method.lower() == "post":
            return DummyResponse(202, headers={"Location": "/entity/Default/24.200.001/InventoryIssue/ReleaseInventoryIssue/status/some-guid"})
        return DummyResponse(204)

    monkeypatch.setattr(service._client, "_request", fake_request)
    service.release_inventory_issue(API_VERSION, reference_nbr)

def test_get_inventory_quantity_available_success(monkeypatch, service):
    """Tests successful retrieval of inventory quantity."""
    expected_results = [{"Available": {"value": 10}}]
    
    def fake_get_data_from_inquiry_form(api_version, inquiry, opts):
        assert inquiry == "InventoryQuantityAvailable"
        return {"Results": expected_results}

    monkeypatch.setattr(service._client.inquiries, "get_data_from_inquiry_form", fake_get_data_from_inquiry_form)
    
    result = service.get_inventory_quantity_available(API_VERSION, "APJAM08", "6/7/2024")
    assert result == expected_results

def test_get_inventory_summary_success(monkeypatch, service):
    """Tests successful retrieval of inventory summary."""
    expected_results = [{"OnHand": {"value": 20}}]

    def fake_get_data_from_inquiry_form(api_version, inquiry, opts):
        assert inquiry == "InventorySummaryInquiry"
        return {"Results": expected_results}

    monkeypatch.setattr(service._client.inquiries, "get_data_from_inquiry_form", fake_get_data_from_inquiry_form)

    result = service.get_inventory_summary(API_VERSION, "SIMCARD")
    assert result == expected_results
    
def test_update_item_warehouse_details_success(monkeypatch, service):
    """Tests successful update of item-warehouse details."""
    builder = (
        ItemWarehouseBuilder()
        .inventory_id("APPLES")
        .warehouse_id("RETAIL")
        .override("MaxQty", True)
        .set("MaxQty", 2222)
    )
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/ItemWarehouse"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.update_item_warehouse_details(API_VERSION, builder)
    assert result == expected_response