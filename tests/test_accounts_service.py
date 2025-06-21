# tests/test_account_service.py
import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.accounts import AccountService
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions

API_VERSION = "24.200.001"
BASE = "https://fake"

class DummyResponse:
    """Fake Response for stubbing requests."""
    def __init__(self, status_code: int, json_body=None):
        self.status_code = status_code
        self._json = json_body or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json

@pytest.fixture
def client(monkeypatch):
    """Provides a mocked AcumaticaClient instance with the AccountService attached."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    
    client_instance = AcumaticaClient(base_url=BASE, username="u", password="p", tenant="t", branch="b")
    client_instance.accounts = AccountService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    """Provides an instance of the AccountService."""
    return client.accounts

# -------------------------------------------------------------------------
# get_accounts Tests
# -------------------------------------------------------------------------

def test_get_accounts_success(monkeypatch, service):
    """Tests successful retrieval of accounts with query options."""
    opts = QueryOptions(filter=(F.Type == 'Asset'), select=["AccountCD", "Description"])
    expected_data = [{"AccountCD": {"value": "10100"}, "Description": {"value": "Cash"}}]

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url.endswith(f"/entity/Default/{API_VERSION}/Account")
        assert kwargs.get("params") == opts.to_params()
        return DummyResponse(200, expected_data)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.get_accounts(API_VERSION, options=opts)
    assert result == expected_data

# -------------------------------------------------------------------------
# create_account_group Tests
# -------------------------------------------------------------------------

def test_create_account_group_success(monkeypatch, service):
    """Tests successful creation of an account group."""
    expected_response = {"AccountGroupID": {"value": "ASSET-L"}, "Description": {"value": "Long-Term Assets"}}

    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url.endswith(f"/entity/Default/{API_VERSION}/AccountGroup")
        
        payload = kwargs.get("json", {})
        assert payload.get("AccountGroupID") == {"value": "ASSET-L"}
        assert payload.get("Description") == {"value": "Long-Term Assets"}
        
        return DummyResponse(201, expected_response)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.create_account_group(API_VERSION, "ASSET-L", "Long-Term Assets")
    assert result == expected_response

# -------------------------------------------------------------------------
# add_account_to_group Tests
# -------------------------------------------------------------------------

def test_add_account_to_group_success(monkeypatch, service):
    """Tests successfully adding an account to a group."""
    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url.endswith(f"/entity/Default/{API_VERSION}/Account")
        
        payload = kwargs.get("json", {})
        assert payload.get("AccountCD") == {"value": "170100"}
        assert payload.get("AccountGroup") == {"value": "ASSET-L"}
        
        return DummyResponse(200, payload)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.add_account_to_group(API_VERSION, "170100", "ASSET-L")
    assert result["AccountGroup"]["value"] == "ASSET-L"

# -------------------------------------------------------------------------
# remove_account_from_group Tests
# -------------------------------------------------------------------------

def test_remove_account_from_group_success(monkeypatch, service):
    """Tests successfully removing an account from a group."""
    def fake_request(method, url, **kwargs):
        payload = kwargs.get("json", {})
        assert payload.get("AccountCD") == {"value": "170100"}
        assert payload.get("AccountGroup") == {"value": None}
        return DummyResponse(200, payload)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.remove_account_from_group(API_VERSION, "170100")
    assert result["AccountGroup"]["value"] is None

# -------------------------------------------------------------------------
# set_default_account_for_group Tests
# -------------------------------------------------------------------------

def test_set_default_account_for_group_success(monkeypatch, service):
    """Tests successfully setting the default account for a group."""
    def fake_request(method, url, **kwargs):
        assert method.lower() == "put"
        assert url.endswith(f"/entity/Default/{API_VERSION}/AccountGroup")
        
        payload = kwargs.get("json", {})
        assert payload.get("AccountGroupID") == {"value": "ASSET-L"}
        assert payload.get("DefaultAccountID") == {"value": "170100"}
        
        return DummyResponse(200, payload)

    monkeypatch.setattr(service._client, "_request", fake_request)
    result = service.set_default_account_for_group(API_VERSION, "ASSET-L", "170100")
    assert result["DefaultAccountID"]["value"] == "170100"

