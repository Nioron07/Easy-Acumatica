# tests/test_stock_items_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.stock_items import StockItemsService
from easy_acumatica.models.stock_item_builder import StockItemBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "StockItem"

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
    client_instance.stock_items = StockItemsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.stock_items

def test_get_stock_items_success(monkeypatch, service):
    """Tests successful retrieval of stock items."""
    expected_response = [{"InventoryID": {"value": "AALEGO500"}}]
    opts = QueryOptions(filter=F.ItemStatus == "Active")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_stock_items(API_VERSION, opts)
    assert result == expected_response

def test_get_stock_item_by_id_success(monkeypatch, service):
    """Tests successful retrieval of a single stock item."""
    inventory_id = "APL-16OZ-GBT"
    expected_response = {"InventoryID": {"value": inventory_id}}
    opts = QueryOptions(expand=["Attributes"])

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}/{inventory_id}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_stock_item_by_id(API_VERSION, inventory_id, opts)
    assert result == expected_response

def test_create_stock_item_success(monkeypatch, service):
    """Tests successful creation of a stock item."""
    builder = StockItemBuilder().inventory_id("BASESERV1")
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_stock_item(API_VERSION, builder)
    assert result == expected_response

def test_get_stock_item_attachments_success(monkeypatch, service):
    """Tests successful retrieval of stock item attachments."""
    inventory_id = "AAMACHINE1"
    expected_files = [{"id": "file123"}]
    
    def fake_get_stock_item_by_id(api_version, id, options):
        assert id == inventory_id
        return {"files": expected_files}

    monkeypatch.setattr(service, "get_stock_item_by_id", fake_get_stock_item_by_id)
    
    result = service.get_stock_item_attachments(API_VERSION, inventory_id)
    assert result == expected_files