"""tests/test_contacts.py
Comprehensive tests for ContactsService using requests_mock.
"""
import json
import pytest
from requests import HTTPError

from easy_acumatica import AcumaticaClient
from easy_acumatica.filters import Filter
from easy_acumatica.models.contact_builder import ContactBuilder

API_VERSION = "24.200.001"
BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"
CONTACTS_URL = f"{BASE}/entity/Default/{API_VERSION}/Contact"


# automatic login/logout stubs --------------------------------------------
@pytest.fixture
def client(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)
    return AcumaticaClient(
        base_url=BASE,
        username="u",
        password="p",
        tenant="t",
        branch="b",
        verify_ssl=False,
    )


# -------------------------------------------------------------------------
# get_contacts
# -------------------------------------------------------------------------
def test_get_contacts_success(requests_mock, client):
    sample = [{"ContactID": {"value": 1}}]
    requests_mock.get(CONTACTS_URL, status_code=200, json=sample)
    assert client.contacts.get_contacts(API_VERSION) == sample


def test_get_contacts_server_failure(requests_mock, client):
    requests_mock.get(CONTACTS_URL, status_code=500)
    with pytest.raises(RuntimeError):
        client.contacts.get_contacts(API_VERSION)


def test_get_contacts_login_failure(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=403)
    with pytest.raises(HTTPError):
        AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False).contacts.get_contacts(
            API_VERSION
        )


# -------------------------------------------------------------------------
# create_contact
# -------------------------------------------------------------------------
def test_create_contact_success(requests_mock, client):
    draft = ContactBuilder().first_name("A").last_name("B").email("a@b.com")
    created = {"ContactID": {"value": 123}}
    requests_mock.put(CONTACTS_URL, status_code=200, json=created)
    assert client.contacts.create_contact(API_VERSION, draft) == created


def test_create_contact_validation_error(requests_mock, client):
    draft = ContactBuilder().first_name("Bad").email("x")
    requests_mock.put(CONTACTS_URL, status_code=422, json={"message": "bad"})
    with pytest.raises(RuntimeError):
        client.contacts.create_contact(API_VERSION, draft)


# -------------------------------------------------------------------------
# deactivate_contact
# -------------------------------------------------------------------------
def test_deactivate_contact_success(requests_mock, client):
    flt = Filter().eq("ContactID", 1)
    requests_mock.put(CONTACTS_URL, status_code=200,
                      json=[{"ContactID": {"value": 1}, "Active": {"value": False}}])
    res = client.contacts.deactivate_contact(API_VERSION, flt, active=False)
    assert res[0]["Active"]["value"] is False


def test_deactivate_contact_server_error(requests_mock, client):
    flt = Filter().eq("ContactID", 1)
    requests_mock.put(CONTACTS_URL, status_code=500)
    with pytest.raises(RuntimeError):
        client.contacts.deactivate_contact(API_VERSION, flt)


# -------------------------------------------------------------------------
# update_contact
# -------------------------------------------------------------------------
def test_update_contact_success(requests_mock, client):
    flt = Filter().eq("ContactID", 1)
    builder = ContactBuilder().email("new@example.com")
    updated = [{"ContactID": {"value": 1}, "Email": {"value": "new@example.com"}}]
    requests_mock.put(CONTACTS_URL, status_code=200, json=updated)
    res = client.contacts.update_contact(API_VERSION, flt, builder)
    assert res[0]["Email"]["value"] == "new@example.com"


def test_update_contact_validation_error(requests_mock, client):
    flt = Filter().eq("ContactID", 1)
    bad_payload = {"MaritalStatus": {"value": "Invalid"}}
    requests_mock.put(CONTACTS_URL, status_code=422, json={"message": "bad"})
    with pytest.raises(RuntimeError):
        client.contacts.update_contact(API_VERSION, flt, bad_payload)


# -------------------------------------------------------------------------
# delete_contact
# -------------------------------------------------------------------------
def test_delete_contact_success(requests_mock, client):
    note_id = "guid-1"
    requests_mock.delete(f"{CONTACTS_URL}/{note_id}", status_code=204)
    assert client.contacts.delete_contact(API_VERSION, note_id) is None


def test_delete_contact_not_found(requests_mock, client):
    note_id = "missing"
    requests_mock.delete(f"{CONTACTS_URL}/{note_id}", status_code=404)
    with pytest.raises(RuntimeError):
        client.contacts.delete_contact(API_VERSION, note_id)