import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.service_orders import ServiceOrdersService
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.filter_builder import F

API_VERSION = "24.200.001"
BASE = "https://fake.com"


class DummyResponse:
    """A dummy response class to mock requests.Response."""
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
    """Mocks the AcumaticaClient and its login/logout methods."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    # Attach the service to the client instance for testing
    client_instance.service_orders = ServiceOrdersService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    """Provides an instance of the ServiceOrdersService."""
    return client.service_orders


def test_get_service_orders_success(monkeypatch, service):
    """Tests successful retrieval of a list of service orders."""
    expected_response = [{"OrderNbr": {"value": "SV0001"}}, {"OrderNbr": {"value": "SV0002"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/ServiceOrder"
        assert "params" not in kwargs or not kwargs.get("params")
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_service_orders(API_VERSION)
    assert result == expected_response


def test_get_service_orders_with_options(monkeypatch, service):
    """Tests retrieving service orders with QueryOptions."""
    opts = QueryOptions(
        filter=F.Status == "Open",
        select=["OrderNbr", "Description"],
        expand=["Customer"]
    )
    expected_response = [{"OrderNbr": {"value": "SV0001"}, "Description": {"value": "Repair service"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/ServiceOrder"
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_service_orders(API_VERSION, options=opts)
    assert result == expected_response


def test_get_service_orders_error(monkeypatch, service):
    """Tests that an API error is propagated correctly."""
    def fake_request(method, url, **kwargs):
        # Simulate a server error from the API
        raise RuntimeError("Acumatica API error 500: Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_service_orders(API_VERSION)
