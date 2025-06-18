# tests/test_client.py
import pytest
from requests import HTTPError

from easy_acumatica import AcumaticaClient

BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"


# -------------------------------------------------------------------------
# login
# -------------------------------------------------------------------------
def test_login_success(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)          # auto-login
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False)
    assert client.login() == 204


# tests/test_client.py
def test_login_failure(requests_mock):
    # first login succeeds so client can be built
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False)

    # make the client "unauthenticated" again
    client.logout()

    # next POST /login should fail
    requests_mock.post(LOGIN_URL, status_code=401)

    with pytest.raises(HTTPError):
        client.login()


# -------------------------------------------------------------------------
# logout
# -------------------------------------------------------------------------
def test_logout_success(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)

    client = AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False)
    client.session.cookies.set("foo", "bar")                # artificial cookie
    assert client.logout() == 204
    assert not client.session.cookies


def test_logout_failure(requests_mock):
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=500)

    client = AcumaticaClient(BASE, "u", "p", "t", "b", verify_ssl=False)
    with pytest.raises(HTTPError):
        client.logout()
