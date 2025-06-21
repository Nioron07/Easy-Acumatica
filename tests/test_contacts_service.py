# tests/test_contacts_service.py

import pytest
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions
from easy_acumatica.models.contact_builder import ContactBuilder

API_VERSION = "24.200.001"
BASE = "https://fake"
CONTACTS_PATH = f"/entity/Default/{API_VERSION}/Contact"


class DummyResponse:
    """Minimal fake Response for _request to return."""
    def __init__(self, status_code: int, json_body=None):
        self.status_code = status_code
        self._json = json_body if json_body is not None else []

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._json


@pytest.fixture
def client(monkeypatch):
    # Prevent real HTTP during login/logout
    monkeypatch.setattr(AcumaticaClient, "login", lambda self: 204)
    monkeypatch.setattr(AcumaticaClient, "logout", lambda self: 204)

    return AcumaticaClient(
        base_url=BASE,
        username="u",
        password="p",
        tenant="t",
        branch="b",
        verify_ssl=False,
        persistent_login=True,
    )


@pytest.fixture
def service(client):
    return client.contacts


# -------------------------------------------------------------------------
# get_contacts
# -------------------------------------------------------------------------
def test_get_contacts_success(monkeypatch, service):
    sample = [{"ContactID": {"value": 1}}]

    def fake_request(method, url, **kwargs):
        assert method == "get"
        assert url.startswith(BASE + CONTACTS_PATH)
        return DummyResponse(200, sample)

    monkeypatch.setattr(service._client, "_request", fake_request)

    assert service.get_contacts(API_VERSION) == sample


def test_get_contacts_server_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        return DummyResponse(500, {"error": "oops"})

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.get_contacts(API_VERSION)


def test_get_contacts_with_options(monkeypatch, service):
    sample = [{"foo": "bar"}]
    captured = {}

    def fake_request(method, url, **kwargs):
        captured["method"] = method
        captured["url"] = url
        captured["params"] = kwargs.get("params")
        return DummyResponse(200, sample)

    monkeypatch.setattr(service._client, "_request", fake_request)

    opts = QueryOptions(
        filter=F.X == F.Y,
        expand=["E"],
        select=["S"],
        top=3,
        skip=1,
        custom=["Z"],
    )
    out = service.get_contacts(API_VERSION, options=opts)
    assert out == sample
    assert captured["method"] == "get"
    assert captured["params"] == opts.to_params()


# -------------------------------------------------------------------------
# create_contact
# -------------------------------------------------------------------------
def test_create_contact_success(monkeypatch, service):
    draft = ContactBuilder().first_name("A").last_name("B").email("a@b.com")
    created = {"ContactID": {"value": 123}}

    def fake_request(method, url, **kwargs):
        assert method == "put"
        assert url.startswith(BASE + CONTACTS_PATH)
        assert kwargs["json"] == draft.build()
        return DummyResponse(200, created)

    monkeypatch.setattr(service._client, "_request", fake_request)

    assert service.create_contact(API_VERSION, draft) == created


def test_create_contact_validation_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        # simulate internal _request error on 422
        raise RuntimeError("HTTP 422 Validation Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.create_contact(API_VERSION, ContactBuilder())


# -------------------------------------------------------------------------
# deactivate_contact
# -------------------------------------------------------------------------
def test_deactivate_contact_success(monkeypatch, service):
    flt = F.ContactID == 1
    updated = [{"Active": {"value": False}}]

    def fake_request(method, url, **kwargs):
        assert method == "put"
        assert kwargs["params"] == {"$filter": flt.build()}
        assert kwargs["json"] == {"Active": {"value": False}}
        return DummyResponse(200, updated)

    monkeypatch.setattr(service._client, "_request", fake_request)

    res = service.deactivate_contact(API_VERSION, flt, active=False)
    assert res == updated


def test_deactivate_contact_server_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 500 Server Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.deactivate_contact(API_VERSION, F.ContactID == 1)


# -------------------------------------------------------------------------
# update_contact
# -------------------------------------------------------------------------
def test_update_contact_success(monkeypatch, service):
    flt = F.ContactID == 1
    builder = ContactBuilder().email("new@example.com")
    updated = [{"Email": {"value": "new@example.com"}}]

    def fake_request(method, url, **kwargs):
        assert method == "put"
        assert kwargs["params"] == {"$filter": flt.build()}
        assert kwargs["json"] == builder.build()
        return DummyResponse(200, updated)

    monkeypatch.setattr(service._client, "_request", fake_request)

    res = service.update_contact(API_VERSION, flt, builder)
    assert res == updated


def test_update_contact_validation_error(monkeypatch, service):
    flt = F.ContactID == 1

    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 422 Validation Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.update_contact(API_VERSION, flt, {"MaritalStatus": {"value": "Invalid"}})


# -------------------------------------------------------------------------
# delete_contact
# -------------------------------------------------------------------------
def test_delete_contact_success(monkeypatch, service):
    note_id = "guid-1"

    def fake_request(method, url, **kwargs):
        assert method == "delete"
        assert url.endswith(f"/Contact/{note_id}")
        return DummyResponse(204)

    monkeypatch.setattr(service._client, "_request", fake_request)

    assert service.delete_contact(API_VERSION, note_id) is None


def test_delete_contact_not_found(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 404 Not Found")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.delete_contact(API_VERSION, "missing")


# -------------------------------------------------------------------------
# link_contact_to_customer
# -------------------------------------------------------------------------
def test_link_contact_success_dict(monkeypatch, service):
    contact_id = 1
    acct_cd = "ABAKERY"
    payload = {"LastName": {"value": "Doe"}}
    updated = [{
        "ContactID": {"value": contact_id},
        "BusinessAccount": {"value": acct_cd},
        "LastName": {"value": "Doe"},
    }]

    def fake_request(method, url, **kwargs):
        body = kwargs["json"]
        assert body["ContactID"]["value"] == contact_id
        assert body["BusinessAccount"]["value"] == acct_cd
        assert body["LastName"]["value"] == "Doe"
        return DummyResponse(200, updated)

    monkeypatch.setattr(service._client, "_request", fake_request)

    res = service.link_contact_to_customer(
        API_VERSION,
        contact_id,
        acct_cd,
        payload=payload,
    )
    assert res == updated


def test_link_contact_success_builder(monkeypatch, service):
    contact_id = 2
    acct_cd = "JWHOIST"
    builder = ContactBuilder().last_name("Hoister")
    updated = [{
        "ContactID": {"value": contact_id},
        "BusinessAccount": {"value": acct_cd},
        "LastName": {"value": "Hoister"},
    }]

    def fake_request(method, url, **kwargs):
        body = kwargs["json"]
        assert body["ContactID"]["value"] == contact_id
        assert body["BusinessAccount"]["value"] == acct_cd
        assert body["LastName"]["value"] == "Hoister"
        return DummyResponse(200, updated)

    monkeypatch.setattr(service._client, "_request", fake_request)

    res = service.link_contact_to_customer(
        API_VERSION,
        contact_id,
        acct_cd,
        payload=builder,
    )
    assert res == updated


def test_link_contact_validation_error(monkeypatch, service):
    def fake_request(method, url, **kwargs):
        raise RuntimeError("HTTP 422 Validation Error")

    monkeypatch.setattr(service._client, "_request", fake_request)

    with pytest.raises(RuntimeError):
        service.link_contact_to_customer(
            API_VERSION,
            99,
            "BADACCT",
            payload={"LastName": {"value": "Error"}},
        )
