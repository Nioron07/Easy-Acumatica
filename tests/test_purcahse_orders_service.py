# tests/test_purchase_orders_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.purchase_orders import PurchaseOrdersService
from easy_acumatica.models.purchase_order_builder import PurchaseOrderBuilder
from easy_acumatica.models.query_builder import QueryOptions

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "PurchaseOrder"

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
    client_instance.purchase_orders = PurchaseOrdersService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.purchase_orders

def test_create_purchase_order_success(monkeypatch, service):
    """Tests successful creation of a purchase order."""
    builder = (
        PurchaseOrderBuilder()
        .vendor_id("GOODFRUITS")
        .location("MAIN")
        .add_detail(
            BranchID="HEADOFFICE",
            InventoryID="APPLES",
            OrderQty=1,
            WarehouseID="WHOLESALE",
            UOM="LB"
        )
        .hold(False)
    )
    expected_response = builder.to_body()
    opts = QueryOptions(expand=["Details"])

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_purchase_order(API_VERSION, builder, opts)
    assert result == expected_response