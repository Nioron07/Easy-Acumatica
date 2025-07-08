# tests/test_manufacturing_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.manufacturing import ManufacturingService
from easy_acumatica.models.configuration_entry_builder import ConfigurationEntryBuilder

API_VERSION = "25.100.001"
BASE = "https://fake"
ENTITY_NAME = "ConfigurationEntry"

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
    client_instance.manufacturing = ManufacturingService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    return client.manufacturing

def test_get_configuration_entry_success(monkeypatch, service):
    """Tests successful retrieval of a configuration entry."""
    configuration_id = "AMC000001"
    expected_response = {"ConfigurationID": {"value": configuration_id}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity/MANUFACTURING/{API_VERSION}/{ENTITY_NAME}/{configuration_id}"
        assert kwargs.get("params") == {"$expand": "Attributes,Features/Options"}
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)

    result = service.get_configuration_entry(API_VERSION, configuration_id)
    assert result == expected_response

def test_update_configuration_entry_success(monkeypatch, service):
    """Tests successful update of a configuration entry."""
    options = [
        {
            "FeatureLineNbr": {"value": 1},
            "OptionLineNbr": {"value": 1},
            "ConfigResultsID": {"value": "5"},
            "Included": {"value": True},
        }
    ]
    builder = (
        ConfigurationEntryBuilder()
        .prod_order_nbr("AM000022")
        .add_feature(1, "5", options)
    )
    expected_response = builder.to_body()

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/MANUFACTURING/{API_VERSION}/{ENTITY_NAME}"
        assert kwargs.get("params") == {"$expand": "Attributes,Features/Options"}
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(200, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)

    result = service.update_configuration_entry(API_VERSION, builder)
    assert result == expected_response