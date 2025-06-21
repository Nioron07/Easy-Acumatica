# tests/test_client.py

import pytest
import requests
from requests import HTTPError

from easy_acumatica import AcumaticaClient

BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"


# -------------------------------------------------------------------------
# DummyResponse for mocking
# -------------------------------------------------------------------------
class DummyResponse:
    def __init__(self, status_code: int, body=None, headers=None):
        self.status_code = status_code
        self._body = body if body is not None else {}
        self.headers = headers or {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._body

# -------------------------------------------------------------------------
# login / logout tests
# -------------------------------------------------------------------------
def test_login_success(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )
    assert client.login() == 204


def test_login_failure(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )
    client.logout()
    requests_mock.post(LOGIN_URL, status_code=401)

    with pytest.raises(HTTPError):
        client.login()


def test_logout_success(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )
    client.session.cookies.set("foo", "bar")
    assert client.logout() == 204
    assert not client.session.cookies


def test_logout_failure(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=500)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )
    with pytest.raises(HTTPError):
        client.logout()


# -------------------------------------------------------------------------
# _request retry logic tests
# -------------------------------------------------------------------------
def test_request_retries_on_401_then_succeeds(monkeypatch):
    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=False,
        retry_on_idle_logout=True
    )

    calls = []
    def fake_login():
        calls.append("login")
        client._logged_in = True
        return 200
    monkeypatch.setattr(client, "login", fake_login)

    def fake_get(url, **kwargs):
        calls.append(f"get{len(calls)}")
        if len(calls) == 1:
            return DummyResponse(401, {"foo": "bar"})
        return DummyResponse(200, {"baz": "qux"})
    monkeypatch.setattr(client.session, "get", fake_get)

    resp = client._request("get", f"{BASE}/test", verify=True)
    assert resp.json() == {"baz": "qux"}
    assert calls == ["get0", "login", "get2"]


def test_request_no_retry_when_disabled(monkeypatch):
    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=False,
        retry_on_idle_logout=False
    )

    calls = []
    def fake_post(url, **kwargs):
        calls.append("post")
        return DummyResponse(401)
    monkeypatch.setattr(client.session, "post", fake_post)

    with pytest.raises(RuntimeError):
        client._request("post", f"{BASE}/test", verify=True)
    assert calls == ["post"]


def test_request_retry_then_final_failure(monkeypatch):
    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=False,
        retry_on_idle_logout=True
    )

    calls = []
    def fake_login():
        calls.append("login")
        client._logged_in = True
        return 200
    monkeypatch.setattr(client, "login", fake_login)

    def fake_put(url, **kwargs):
        calls.append(f"put{len(calls)}")
        if len(calls) == 1:
            return DummyResponse(401)
        return DummyResponse(500)
    monkeypatch.setattr(client.session, "put", fake_put)

    with pytest.raises(RuntimeError):
        client._request("put", f"{BASE}/test", verify=True)
    assert calls == ["put0", "login", "put2"]

# -------------------------------------------------------------------------
# get_endpoint_info test
# -------------------------------------------------------------------------
def test_get_endpoint_info_success(monkeypatch):
    """
    Tests that get_endpoint_info calls the correct URL and returns the JSON body.
    """
    # Initialize with persistent_login=False to avoid login on creation.
    # We will mock the login call inside the method itself.
    client = AcumaticaClient(BASE, "u", "p", "t", "b", persistent_login=False)
    
    # Mock the login method to prevent the real network call
    monkeypatch.setattr(client, "login", lambda: None)
    
    expected_data = {
        "version": "24.200.001",
        "endpoints": [{"name": "Default", "version": "24.200.001"}]
    }

    def fake_request(method, url, **kwargs):
        assert method.lower() == "get"
        assert url == f"{BASE}/entity"
        return DummyResponse(200, body=expected_data)

    monkeypatch.setattr(client, "_request", fake_request)
    
    result = client.get_endpoint_info()
    assert result == expected_data
