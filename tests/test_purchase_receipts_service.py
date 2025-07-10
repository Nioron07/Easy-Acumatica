# tests/test_purchase_receipts_service.py

import pytest
import requests
import time

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.purchase_receipts import PurchaseReceiptsService
from easy_acumatica.models.purchase_receipt_builder import PurchaseReceiptBuilder
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.sub_services.actions import ActionsService

API_VERSION = "24.200.001"
BASE = "https://fake"
ENTITY_NAME = "PurchaseReceipt"

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
    client_instance.purchase_receipts = PurchaseReceiptsService(client_instance)
    client_instance.actions = ActionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.purchase_receipts

def test_create_success(monkeypatch, service):
    """Tests successful creation of a purchase receipt."""
    builder = (
        PurchaseReceiptBuilder()
        .vendor_id("GOODFRUITS")
        .type("Receipt")
        .add_detail_from_po("PO000001")
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
    result = service.create(API_VERSION, builder, opts)
    assert result == expected_response

def test_release_purchase_receipt_success(monkeypatch, service):
    """Tests successful release of a purchase receipt."""
    receipt_id = "some-guid-123"

    def fake_request(method, url, **kwargs):
        assert method.lower() == "post"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/{ENTITY_NAME}/ReleasePurchaseReceipt"
        assert kwargs.get("json") == {"entity": {"id": receipt_id}}
        return DummyResponse(202) # Simulate async start

    monkeypatch.setattr(service._client, "_request", fake_request)
    service.release_purchase_receipt(API_VERSION, receipt_id)
