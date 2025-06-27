# tests/sub_services/test_leads_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.leads import LeadsService
from easy_acumatica.models.lead_builder import LeadBuilder

API_VERSION = "24.200.001"
BASE = "https://fake"


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
    client_instance.leads = LeadsService(client_instance)
    return client_instance


@pytest.fixture
def service(client):
    return client.leads


def test_create_lead_success(monkeypatch, service):
    """Tests successful creation of a lead."""
    builder = (
        LeadBuilder()
        .first_name("Brent")
        .last_name("Edds")
        .email("brent.edds@example.com")
    )
    expected_response = {"NoteID": {"value": "some-guid-123"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url == f"{BASE}/entity/Default/{API_VERSION}/Lead"
        assert kwargs.get("json") == builder.to_body()
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    
    result = service.create_lead(API_VERSION, builder)
    assert result == expected_response

def test_create_lead_error(monkeypatch, service):
    """Tests that an API error during creation is propagated."""
    builder = LeadBuilder().first_name("Invalid")

    def fake_request(method, url, **kwargs):
        raise RuntimeError("Acumatica API error 400: Bad Request")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError, match="Acumatica API error 400"):
        service.create_lead(API_VERSION, builder)
