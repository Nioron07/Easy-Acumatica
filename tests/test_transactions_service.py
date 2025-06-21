# tests/test_transactions_service.py
import pytest
import requests
from datetime import datetime

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.transactions import TransactionsService
from easy_acumatica.models.query_builder import QueryOptions

API_VERSION = "24.200.001"
BASE = "https://fake"

class DummyResponse:
    """Fake Response for stubbing requests."""
    def __init__(self, status_code: int, json_body=None, text_body=None, headers=None):
        self.status_code = status_code
        self._json = json_body
        self._text = text_body or ""
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json

@pytest.fixture
def client(monkeypatch):
    """Provides a mocked AcumaticaClient instance."""
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)
    
    client_instance = AcumaticaClient(
        base_url=BASE, username="u", password="p", tenant="t", branch="b"
    )
    # Add the service to the client instance for testing
    client_instance.transactions = TransactionsService(client_instance)
    return client_instance

@pytest.fixture
def service(client):
    """Provides an instance of the TransactionsService."""
    return client.transactions

# -------------------------------------------------------------------------
# get_ledger_transactions Tests
# -------------------------------------------------------------------------

def test_get_ledger_transactions_success(monkeypatch, service):
    """
    Tests successful retrieval of ledger transactions, verifying the request
    method, URL, parameters, and payload are all correct.
    """
    start_date = datetime(2024, 4, 15)
    end_date = datetime(2024, 5, 20)
    opts = QueryOptions(expand=["Results"])
    expected_data = {"Results": [{"Account": "12345"}]}

    def fake_request(method, url, **kwargs):
        # 1. Verify the HTTP method and URL
        assert method.lower() == "put"
        assert url.endswith(f"/entity/Default/{API_VERSION}/AccountDetailsForPeriodInquiry")

        # 2. Verify the JSON payload for dates
        json_body = kwargs.get("json", {})
        assert json_body.get("FromPeriod") == {"value": "042024"}
        assert json_body.get("ToPeriod") == {"value": "052024"}

        # 3. Verify the URL parameters ($expand)
        params = kwargs.get("params", {})
        assert params.get("$expand") == "Results"

        return DummyResponse(200, expected_data)

    monkeypatch.setattr(service._client, "_request", fake_request)

    # Execute the method
    result = service.get_ledger_transactions(
        API_VERSION,
        start_date=start_date,
        end_date=end_date,
        options=opts
    )

    # Assert the response is correct
    assert result == expected_data

def test_get_ledger_transactions_error(monkeypatch, service):
    """
    Tests that the method correctly raises a RuntimeError when the API
    returns an error status.
    """
    start_date = datetime(2024, 1, 1)
    end_date = datetime(2024, 1, 31)

    def fake_request(method, url, **kwargs):
        # Simulate a server error
        raise RuntimeError("Acumatica API error 500: Internal Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    # The method should raise a RuntimeError
    with pytest.raises(RuntimeError, match="Acumatica API error 500"):
        service.get_ledger_transactions(
            API_VERSION,
            start_date=start_date,
            end_date=end_date
        )

