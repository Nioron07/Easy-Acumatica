import pytest
from unittest.mock import MagicMock
from easy_acumatica.sub_services.bills import BillsService
from easy_acumatica.models.bill_builder import BillBuilder
from easy_acumatica.models.query_builder import QueryOptions


@pytest.fixture
def client():
    mock_client = MagicMock()
    mock_client.base_url = "https://fake"
    mock_client.persistent_login = False
    mock_client.verify_ssl = True
    return mock_client


@pytest.fixture
def service(client):
    return BillsService(client)


def test_create_bill_calls_put_correctly(service, client):
    builder = BillBuilder().vendor("VENDOR123").type()
    client._request.return_value.json.return_value = {"status": "success"}

    result = service.create_bill("24.200.001", builder)

    assert result == {"status": "success"}
    client._request.assert_called_once()


def test_create_bill_with_query_options(service, client):
    builder = BillBuilder().vendor("VENDOR123")
    options = QueryOptions(expand=["Details"])
    client._request.return_value.json.return_value = {"ok": True}

    result = service.create_bill("24.200.001", builder, options)

    assert result == {"ok": True}
    assert client._request.call_args[1]["params"] == options.to_params()


def test_approve_bill_sends_post(service, client):
    service.approve_bill("24.200.001", "000123")

    args, kwargs = client._request.call_args
    assert args[0] == "post"
    assert args[1].endswith("/Bill/Approve")
    assert kwargs["json"]["entity"]["ReferenceNbr"]["value"] == "000123"


def test_release_retainage_with_parameters(service, client):
    service.release_retainage("24.200.001", "000999", {
        "AmtToRelease": 123.45,
        "PostPeriod": "032025"
    })

    body = client._request.call_args[1]["json"]
    assert body["parameters"]["AmtToRelease"]["value"] == 123.45
    assert body["parameters"]["PostPeriod"]["value"] == "032025"


def test_release_retainage_without_parameters(service, client):
    service.release_retainage("24.200.001", "000888")

    body = client._request.call_args[1]["json"]
    assert "parameters" not in body
    assert body["entity"]["ReferenceNbr"]["value"] == "000888"
