import pytest
from requests import HTTPError
from easy_acumatica import AcumaticaClient

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

def test_login_success(requests_mock, client):
    # stub the exact URL used in client.login()
    requests_mock.post("https://fake/entity/auth/login", status_code=204)
    assert client.login() == 204

def test_login_failure(requests_mock, client):
    requests_mock.post("https://fake/entity/auth/login", status_code=401)
    with pytest.raises(HTTPError):
        client.login()

def test_logout_success(requests_mock, client):
    # pre-populate a cookie so we can verify it gets cleared
    client.session.cookies.set("foo", "bar")
    requests_mock.post("https://fake/entity/auth/logout", status_code=204)
    assert client.logout() == 204
    assert not client.session.cookies  # cookies cleared

def test_logout_failure(requests_mock, client):
    requests_mock.post("https://fake/entity/auth/logout", status_code=500)
    with pytest.raises(HTTPError):
        client.logout()