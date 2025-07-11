import pytest
from unittest.mock import MagicMock
from easy_acumatica.sub_services.boms import BomsService
from easy_acumatica.models.bom_builder import BOMBuilder
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
    return BomsService(client)


def test_create_bom_calls_put_correctly(service, client):
    builder = BOMBuilder().inventory_id("TEST123").revision("A")
    client._request.return_value.json.return_value = {"status": "success"}

    result = service.create_bom("24.200.001", builder)

    assert result == {"status": "success"}
    client._request.assert_called_once()
    assert client._request.call_args[0][0] == "put"
    assert "/BillOfMaterial" in client._request.call_args[0][1]


def test_create_bom_with_query_options(service, client):
    builder = BOMBuilder().inventory_id("TEST123").revision("A")
    options = QueryOptions(expand=["Materials"])
    client._request.return_value.json.return_value = {"ok": True}

    result = service.create_bom("24.200.001", builder, options)

    assert result == {"ok": True}
    assert client._request.call_args[1]["params"] == options.to_params()


def test_get_all_boms(service, client):
    client._request.return_value.json.return_value = [{"bom": "list"}]

    result = service.get_boms("24.200.001")

    assert result == [{"bom": "list"}]
    args, kwargs = client._request.call_args
    assert args[0] == "get"
    assert args[1].endswith("/BillOfMaterial")


def test_get_single_bom(service, client):
    client._request.return_value.json.return_value = {"bom": "TEST123"}

    result = service.get_boms("24.200.001", "TEST123", "A")

    assert result == {"bom": "TEST123"}
    args, kwargs = client._request.call_args
    assert args[0] == "get"
    assert "/BillOfMaterial/TEST123/A" in args[1]


def test_get_boms_with_query_options(service, client):
    options = QueryOptions(filter={"InventoryID": {"eq": "TEST123"}})
    client._request.return_value.json.return_value = [{"bom": "filtered"}]

    result = service.get_boms("24.200.001", options=options)

    assert result == [{"bom": "filtered"}]
    assert client._request.call_args[1]["params"] == options.to_params()