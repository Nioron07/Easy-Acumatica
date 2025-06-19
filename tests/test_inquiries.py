import pytest
from requests import Response, Session
from easy_acumatica.sub_services.inquiries import InquiriesService
from easy_acumatica.models.inquiry_builder import InquiryOptions
from easy_acumatica.models.filters import QueryOptions

class DummyResponse(Response):
    def __init__(self, status_code: int, json_data: dict):
        super().__init__()
        self._json_data = json_data
        self.status_code = status_code

    def json(self):
        return self._json_data


def dummy_raise_for_status(resp):
    if resp.status_code >= 400:
        raise Exception(f"HTTP {resp.status_code}")

@pytest.fixture
def client(monkeypatch):
    class DummyClient:
        base_url = "https://example.com"
        tenant = "TENANT"
        username = "user"
        password = "pass"
        verify_ssl = True
        session = Session()
    client = DummyClient()
    # patch shared _raise_with_detail to use dummy behavior
    monkeypatch.setattr(
        "easy_acumatica.sub_services.inquiries._raise_with_detail",
        lambda resp: dummy_raise_for_status(resp),
    )
    return client

@ pytest.mark.parametrize("results_json,expected", [
    ([{"foo": 1}, {"bar": 2}], [{"foo": 1}, {"bar": 2}]),
    ([], []),
])
def test_get_data_from_inquiry_form(monkeypatch, client, results_json, expected):
    # prepare dummy response
    dummy_resp = DummyResponse(200, results_json)
    monkeypatch.setattr(
        client.session,
        "put",
        lambda url, params, json, headers, verify: dummy_resp
    )
    svc = InquiriesService(client)
    opts = InquiryOptions().param("A", "B").expand("Results")
    out = svc.get_data_from_inquiry_form("v1", "InquiryX", opts)
    assert out == expected

@ pytest.mark.parametrize("odata_params,return_json", [
    (None, {"value": [{"id": 1}]}),
    ({"$top": "5"}, {"value": [{"id": 1}, {"id": 2}]}),
])
def test_execute_generic_inquiry(monkeypatch, client, odata_params, return_json):
    # prepare dummy response
    dummy_resp = DummyResponse(200, return_json)
    monkeypatch.setattr(
        client.session,
        "get",
        lambda url, params, headers, verify, auth=None: dummy_resp
    )
    svc = InquiriesService(client)
    if odata_params:
        qopts = QueryOptions(filter=None, expand=None, select=None, top=None, skip=None)
        # manually set params for test
        qopts_dict = odata_params
        monkeypatch.setattr(qopts, "to_params", lambda: qopts_dict)
        res = svc.execute_generic_inquiry("InquiryY", qopts)
    else:
        res = svc.execute_generic_inquiry("InquiryY")
    assert res == return_json


def test_execute_generic_inquiry_unauthorized(monkeypatch, client):
    dummy_resp = DummyResponse(401, {})
    monkeypatch.setattr(
        client.session,
        "get",
        lambda url, params, headers, verify, auth=None: dummy_resp
    )
    svc = InquiriesService(client)
    with pytest.raises(Exception) as exc:
        svc.execute_generic_inquiry("InquiryY")
    assert "HTTP 401" in str(exc.value)
