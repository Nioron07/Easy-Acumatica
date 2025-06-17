import pytest
from requests import HTTPError
from easy_acumatica import AcumaticaClient

API_VERSION = "24.200.001"
BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"
CONTACTS_URL = f"{BASE}/entity/Default/{API_VERSION}/Contact"

@pytest.fixture
def client():
    return AcumaticaClient(
        base_url="https://fake",
        username="u",
        password="p",
        tenant="t",
        branch="b",
        verify_ssl=False,
    )

def test_get_contacts_success(requests_mock, client):
    # 1) stub login
    requests_mock.post(LOGIN_URL, status_code=204)

    # 2) realistic payload
    sample_response = [
        {
            "id": "f75fdac1-4e14-ef11-8427-127508bafbb3",
            "rowNumber": 1,
            "ContactID": {"value": 102210},
            "DisplayName": {"value": "Brian Wooten"},
            "Email": {"value": "BWOOTEN@HANDLINGSERVICES.CO"},
            "_links": {
                "self": f"/entity/Default/{API_VERSION}/Contact/f75fdac1-4e14-ef11-8427-127508bafbb3"
            }
        },
        {
            "id": "245b93db-4f2e-ef11-8428-127508bafbb3",
            "rowNumber": 2,
            "ContactID": {"value": 102262},
            "DisplayName": {"value": "Mavis Sarti"},
            "Email": {"value": "mavis.sarti@marshelectronics.com"},
            "_links": {
                "self": f"/entity/Default/{API_VERSION}/Contact/245b93db-4f2e-ef11-8428-127508bafbb3"
            }
        }
    ]
    # 3) stub GET
    requests_mock.get(CONTACTS_URL, json=sample_response, status_code=200)
    # 4) stub logout
    requests_mock.post(LOGOUT_URL, status_code=204)

    # exercise
    result = client.contacts.get_contacts(API_VERSION)
    assert result == sample_response

def test_get_contacts_login_fails(requests_mock, client):
    requests_mock.post("https://fake/entity/auth/login", status_code=403)
    with pytest.raises(HTTPError):
        client.contacts.get_contacts(API_VERSION)

def test_get_contacts_get_fails(requests_mock, client):
    requests_mock.post("https://fake/entity/auth/login", status_code=204)
    requests_mock.get(CONTACTS_URL, status_code=500)
    # stub logout so that error comes from GET, not from missing logout mock
    requests_mock.post("https://fake/entity/auth/logout", status_code=204)

    with pytest.raises(HTTPError):
        client.contacts.get_contacts(API_VERSION)

def test_get_contacts_logout_fails(requests_mock, client):
    requests_mock.post("https://fake/entity/auth/login", status_code=204)
    requests_mock.get(CONTACTS_URL, json=[], status_code=200)
    requests_mock.post("https://fake/entity/auth/logout", status_code=502)

    with pytest.raises(HTTPError):
        client.contacts.get_contacts(API_VERSION)