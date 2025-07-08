# tests/test_shipments_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.shipments import ShipmentsService
from easy_acumatica.models.shipment_builder import ShipmentBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "Shipment"

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
    client_instance.shipments = ShipmentsService(client_instance)
    from easy_acumatica.sub_services.actions import ActionsService
    client_instance.actions = ActionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.shipments

def test_get_shipments_success(monkeypatch, service):
    """Tests successful retrieval of shipments."""
    expected_response = [{"ShipmentNbr": {"value": "000001"}}]
    opts = QueryOptions(filter=F.ShipmentNbr == "000001")

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_shipments(API_VERSION, opts)
    assert result == expected_response

def test_create_shipment_success(monkeypatch, service):
    """Tests successful creation of a shipment."""
    builder = ShipmentBuilder().type("Shipment")
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_shipment(API_VERSION, builder)
    assert result == expected_response

def test_confirm_shipment_success(monkeypatch, service):
    """Tests confirming a shipment."""
    shipment_nbr = "000082"

    def fake_execute_action(api_version, entity_name, action_name, entity):
        assert entity_name == "SalesOrder"
        assert action_name == "ConfirmShipment"
        assert entity["ShipmentNbr"]["value"] == shipment_nbr

    monkeypatch.setattr(service._client.actions, "execute_action", fake_execute_action)
    service.confirm_shipment(API_VERSION, shipment_nbr)

def test_prepare_invoice_success(monkeypatch, service):
    """Tests preparing an invoice for a shipment."""
    shipment_nbr = "000082"

    def fake_execute_action(api_version, entity_name, action_name, entity):
        assert entity_name == "Shipment"
        assert action_name == "PrepareInvoice"
        assert entity["ShipmentNbr"]["value"] == shipment_nbr

    monkeypatch.setattr(service._client.actions, "execute_action", fake_execute_action)
    service.prepare_invoice(API_VERSION, shipment_nbr)