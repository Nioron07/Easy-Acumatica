# tests/test_sales_orders_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.sales_orders import SalesOrdersService
from easy_acumatica.models.sales_order_builder import SalesOrderBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "SalesOrder"

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
    client_instance.sales_orders = SalesOrdersService(client_instance)
    from easy_acumatica.sub_services.actions import ActionsService
    client_instance.actions = ActionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.sales_orders

def test_get_sales_orders_success(monkeypatch, service):
    """Tests successful retrieval of sales orders."""
    expected_response = [{"OrderNbr": {"value": "SO0001"}}]
    opts = QueryOptions(filter=F.CustomerID == "C000000003")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_sales_orders(API_VERSION, opts)
    assert result == expected_response

def test_create_sales_order_success(monkeypatch, service):
    """Tests successful creation of a sales order."""
    builder = SalesOrderBuilder().customer_id("GOODFOOD")
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_sales_order(API_VERSION, builder)
    assert result == expected_response

def test_apply_discounts_success(monkeypatch, service):
    """Tests applying discounts to a sales order."""
    order_type = "SO"
    order_nbr = "000065"

    def fake_execute_action(api_version, entity_name, action_name, entity, parameters=None):
        assert entity_name == "SalesOrder"
        assert action_name == "AutoRecalculateDiscounts"
        assert entity["OrderType"]["value"] == order_type
        assert entity["OrderNbr"]["value"] == order_nbr

    monkeypatch.setattr(service._client.actions, "execute_action", fake_execute_action)
    service.apply_discounts(API_VERSION, order_type, order_nbr)

def test_create_shipment_success(monkeypatch, service):
    """Tests creating a shipment from a sales order."""
    order_id = "42bb9a17-a402-e911-b818-00155d408001"
    shipment_date = "2025-08-20T00:00:00+03:00"
    warehouse_id = "RETAIL"

    def fake_execute_action(api_version, entity_name, action_name, entity, parameters):
        assert entity_name == "SalesOrder"
        assert action_name == "SalesOrderCreateShipment"
        assert entity["id"]["value"] == order_id
        assert parameters["ShipmentDate"] == shipment_date
        assert parameters["WarehouseID"] == warehouse_id

    monkeypatch.setattr(service._client.actions, "execute_action", fake_execute_action)
    service.create_shipment(API_VERSION, order_id, shipment_date, warehouse_id)