import pytest
from easy_acumatica import AcumaticaClient

@pytest.fixture
def client(monkeypatch):
    # monkeypatch a requests.Session or use requests-mock
    return AcumaticaClient("https://fake", "u", "p", "t", "b")

def test_login_success(client, requests_mock):
    requests_mock.post("https://fake/auth/login", status_code=204)
    assert client.login() == 204
