# tests/test_client.py

import pytest
import requests
from requests import HTTPError

from easy_acumatica import AcumaticaClient

BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"


# -------------------------------------------------------------------------
# login / logout
# -------------------------------------------------------------------------
def test_login_success(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)          # auto-login
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )
    assert client.login() == 204


def test_login_failure(requests_mock):
    # first login succeeds so client can be built
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=True
    )

    # make the client "unauthenticated" again
    client.logout()

    # next POST /login should fail
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
    client.session.cookies.set("foo", "bar")                # artificial cookie
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
# _request retry logic
# -------------------------------------------------------------------------
class DummyResponse:
    def __init__(self, status_code: int, body=None):
        self.status_code = status_code
        self._body = body if body is not None else {}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code}")

    def json(self):
        return self._body


def test_request_retries_on_401_then_succeeds(monkeypatch):
    client = AcumaticaClient(
        BASE, "u", "p", "t", "b",
        verify_ssl=False,
        persistent_login=False,
        retry_on_idle_logout=True
    )

    calls = []
    # stub out login()
    def fake_login():
        calls.append("login")
        client._logged_in = True
        return 200
    monkeypatch.setattr(client, "login", fake_login)

    # first GET returns 401, second returns 200
    def fake_get(url, **kwargs):
        calls.append(f"get{len(calls)}")
        if len(calls) == 1:
            return DummyResponse(401, {"foo": "bar"})
        return DummyResponse(200, {"baz": "qux"})
    monkeypatch.setattr(client.session, "get", fake_get)

    resp = client._request("get", f"{BASE}/test", headers={}, verify=True)
    assert resp.json() == {"baz": "qux"}
    # expected call order: GET (1), login, GET (2)
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
        client._request("post", f"{BASE}/test", headers={}, verify=True)
    # should only call once, no login retry
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

    # first PUT returns 401, then 500
    def fake_put(url, **kwargs):
        calls.append(f"put{len(calls)}")
        if len(calls) == 1:
            return DummyResponse(401)
        return DummyResponse(500)
    monkeypatch.setattr(client.session, "put", fake_put)

    with pytest.raises(RuntimeError):
        client._request("put", f"{BASE}/test", headers={}, verify=True)
    # call order: PUT(1), login, PUT(2)
    assert calls == ["put0", "login", "put2"]
