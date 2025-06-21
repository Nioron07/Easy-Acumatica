# tests/test_inquiries.py
"""
Unit tests for easy_acumatica.sub_services.inquiries.InquiriesService
using client._request.
"""

import pytest
from requests import Response

from easy_acumatica.sub_services.inquiries import InquiriesService
from easy_acumatica.models.inquiry_builder import InquiryBuilder
from easy_acumatica.models.query_builder import QueryOptions


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
def client():
    """A minimal dummy client with _request method to be monkeypatched."""
    class DummyClient:
        base_url = "https://example.com"
        tenant = "TENANT"
        username = "user"
        password = "pass"
        verify_ssl = True
        persistent_login = True

        def _request(self, method: str, url: str, **kwargs):
            raise NotImplementedError("_request must be stubbed in tests")

    return DummyClient()


@ pytest.mark.parametrize("results_json,expected", [
    ([{"foo": 1}, {"bar": 2}], [{"foo": 1}, {"bar": 2}]),
    ([], []),
])
def test_get_data_from_inquiry_form(monkeypatch, client, results_json, expected):
    dummy_resp = DummyResponse(200, results_json)

    # Stub out client._request for the PUT-based inquiry form call
    def fake_request(method, url, params, json, headers, verify):
        # ensure it's the PUT path
        assert method.lower() == "put"
        return dummy_resp

    monkeypatch.setattr(client, "_request", fake_request)

    svc = InquiriesService(client)
    opts = InquiryBuilder().param("A", "B").expand("Results")
    out = svc.get_data_from_inquiry_form("v1", "InquiryX", opts)
    assert out == expected


@ pytest.mark.parametrize("odata_params,return_json", [
    (None, {"value": [{"id": 1}]}),
    ({"$top": "5"}, {"value": [{"id": 1}, {"id": 2}]}),
])
def test_execute_generic_inquiry(monkeypatch, client, odata_params, return_json):
    dummy_resp = DummyResponse(200, return_json)

    # Stub out client._request for the GET-based OData inquiry call
    def fake_request(method, url, params=None, headers=None, verify=None, auth=None):
        assert method.lower() == "get"
        # if params were provided, ensure they match what QueryOptions.to_params() would return
        if odata_params is not None:
            assert params == odata_params
        else:
            assert params is None
        return dummy_resp

    monkeypatch.setattr(client, "_request", fake_request)

    svc = InquiriesService(client)

    if odata_params:
        qopts = QueryOptions(filter=None, expand=None, select=None, top=None, skip=None)
        monkeypatch.setattr(qopts, "to_params", lambda: odata_params)
        res = svc.execute_generic_inquiry("InquiryY", qopts)
    else:
        res = svc.execute_generic_inquiry("InquiryY")

    assert res == return_json


def test_execute_generic_inquiry_unauthorized(monkeypatch, client):
    dummy_resp = DummyResponse(401, {})

    # Stub client._request to raise via our dummy_raise_for_status
    def fake_request(method, url, **kwargs):
        # simulate the internal raise_with_detail
        dummy_raise_for_status(dummy_resp)

    monkeypatch.setattr(client, "_request", fake_request)

    svc = InquiriesService(client)
    with pytest.raises(Exception) as exc:
        svc.execute_generic_inquiry("InquiryY")
    assert "HTTP 401" in str(exc.value)
