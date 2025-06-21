# tests/test_customers_service.py

import pytest
import requests

from easy_acumatica.sub_services.customers import CustomersService
from easy_acumatica.models.customer_builder import CustomerBuilder
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions


class DummyResponse:
    """Fake Response with raise_for_status() and json()."""
    def __init__(self, status_code: int, body=None):
        self.status_code = status_code
        self._body = body or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._body


@pytest.fixture
def client():
    class DummyClient:
        def __init__(self):
            self.base_url = "https://fake"
            self.verify_ssl = True
            self.persistent_login = True
            # session is a blank object we’ll monkeypatch
            self.session = type("S", (), {})()
        def login(self): pass
        def logout(self): pass
        def _request(self, *args, **kwargs):
            raise NotImplementedError("_request must be stubbed")
    return DummyClient()


@pytest.fixture
def service(client):
    return CustomersService(client)


# -------------------------------------------------------------------------
# get_customers
# -------------------------------------------------------------------------
def test_get_customers_success(monkeypatch, service, client):
    data = [{"foo": 1}, {"bar": 2}]
    dummy = DummyResponse(200, data)
    monkeypatch.setattr(client.session, "get", lambda *a, **k: dummy, raising=False)
    assert service.get_customers("v1") == data


def test_get_customers_with_options(monkeypatch, service, client):
    data = [{"x": "y"}]
    dummy = DummyResponse(200, data)
    captured = {}
    def fake_get(url, params=None, verify=None):
        captured["url"] = url
        captured["params"] = params
        return dummy
    monkeypatch.setattr(client.session, "get", fake_get, raising=False)

    opts = QueryOptions(
        filter=F.A == F.B,
        select=["X"], expand=["Y"], top=5, skip=2, custom=["Z"]
    )
    out = service.get_customers("24.200.001", opts)
    assert out == data
    assert captured["url"].endswith("/entity/Default/24.200.001/Customer")
    assert captured["params"] == opts.to_params()


def test_get_customers_error(monkeypatch, service, client):
    dummy = DummyResponse(500, {"error": "oops"})
    monkeypatch.setattr(client.session, "get", lambda *a, **k: dummy, raising=False)
    with pytest.raises(RuntimeError) as exc:
        service.get_customers("v1")
    assert "Acumatica API error 500" in str(exc.value)


# -------------------------------------------------------------------------
# create_customer
# -------------------------------------------------------------------------
def test_create_customer_success(monkeypatch, service, client):
    result = {"CustomerID": {"value": "C1"}}
    # return a 201 so _request→raise_for_status passes
    dummy = DummyResponse(201, result)
    monkeypatch.setattr(client, "_request", lambda *a, **k: dummy, raising=False)

    builder = CustomerBuilder().customer_id("C1").customer_name("Name1").customer_class("DEF")
    assert service.create_customer("v1", builder) == result


def test_create_customer_error(monkeypatch, service, client):
    # make _request raise
    def fake_request(*a, **k):
        raise RuntimeError("HTTP 400 Bad Request")
    monkeypatch.setattr(client, "_request", fake_request, raising=False)

    with pytest.raises(RuntimeError):
        service.create_customer("v1", CustomerBuilder())


# -------------------------------------------------------------------------
# update_customer
# -------------------------------------------------------------------------
def test_update_customer_success(monkeypatch, service, client):
    dummy = DummyResponse(200, {"ok": True})
    captured = {}
    def fake_request(method, url, **kw):
        captured.update(method=method, url=url, **kw)
        return dummy
    monkeypatch.setattr(client, "_request", fake_request, raising=False)

    builder = CustomerBuilder().set("F", "V")
    opts = QueryOptions(
        filter=F.K == "V",
        expand=["E"], select=["S"]
    )
    out = service.update_customer("v1", builder, opts)
    assert out == {"ok": True}
    assert captured["method"] == "put"
    assert captured["url"].endswith("/entity/Default/v1/Customer")
    assert captured["params"] == opts.to_params()
    assert captured["json"] == builder.to_body()


def test_update_customer_error(monkeypatch, service, client):
    # force error from _request
    def fake_request(*a, **k):
        raise RuntimeError("HTTP 403")
    monkeypatch.setattr(client, "_request", fake_request, raising=False)

    with pytest.raises(RuntimeError):
        service.update_customer("v1", CustomerBuilder(), QueryOptions(filter=F.A == F.B))


# -------------------------------------------------------------------------
# update_customer_currency_overriding
# -------------------------------------------------------------------------
def test_update_customer_currency_overriding_success(monkeypatch, service, client):
    dummy = DummyResponse(200, {"enabled": True})
    monkeypatch.setattr(client, "_request", lambda *a, **k: dummy, raising=False)
    out = service.update_customer_currency_overriding("v1", "CUST", True, currency_rate_type="SPOT")
    assert out == {"enabled": True}


def test_update_customer_currency_overriding_error(monkeypatch, service, client):
    def fake_request(*a, **k):
        raise RuntimeError("HTTP 500")
    monkeypatch.setattr(client, "_request", fake_request, raising=False)
    with pytest.raises(RuntimeError):
        service.update_customer_currency_overriding("v1", "CUST", True)


# -------------------------------------------------------------------------
# get_shipping_contact
# -------------------------------------------------------------------------
def test_get_shipping_contact_found(monkeypatch, service):
    sc = {"Email": {"value": "x"}}
    monkeypatch.setattr(service, "get_customers", lambda v, opts: [{"ShippingContact": sc}])
    assert service.get_shipping_contact("v1", "ID") == sc


def test_get_shipping_contact_missing(monkeypatch, service):
    monkeypatch.setattr(service, "get_customers", lambda v, opts: [])
    assert service.get_shipping_contact("v1", "ID") is None


# -------------------------------------------------------------------------
# assign_tax_zone
# -------------------------------------------------------------------------
def test_assign_tax_zone_success(monkeypatch, service, client):
    dummy = DummyResponse(200, {"TaxZone": {"value": "NYSTATE"}})
    captured = {}
    def fake_request(method, url, **kw):
        captured.update(method=method, url=url, **kw)
        return dummy
    monkeypatch.setattr(client, "_request", fake_request, raising=False)

    out = service.assign_tax_zone("v1", "FRUIT", "ZONE1")
    assert out == {"TaxZone": {"value": "NYSTATE"}}
    assert captured["method"] == "put"
    assert "$select" in captured["params"]
    assert captured["json"] == {"CustomerID": {"value": "FRUIT"}, "TaxZone": {"value": "ZONE1"}}


def test_assign_tax_zone_error(monkeypatch, service, client):
    def fake_request(*a, **k):
        raise RuntimeError("HTTP 404")
    monkeypatch.setattr(client, "_request", fake_request, raising=False)

    with pytest.raises(RuntimeError):
        service.assign_tax_zone("v1", "FRUIT", "ZONE1")
