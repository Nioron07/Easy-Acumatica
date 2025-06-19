# tests/test_helpers.py
import pytest
import requests
from easy_acumatica.helpers import _raise_with_detail, auth_error_msg


def make_response(status: int, content: bytes, content_type: str = None) -> requests.Response:
    """Helper to build a Response with given status and raw body."""
    resp = requests.Response()
    resp.status_code = status
    resp._content = content
    if content_type:
        resp.headers['Content-Type'] = content_type
    return resp


def test_no_error_on_2xx():
    resp = make_response(200, b'anything')
    # Should not raise
    assert _raise_with_detail(resp) is None


@pytest.mark.parametrize(
    "body,detail_key",
    [
        (b'{"exceptionMessage":"X detail"}', "X detail"),
        (b'{"message":"M detail"}', "M detail"),
        (b'{"foo":"bar"}', '{"foo": "bar"}'),  # generic dict → json.dumps
    ]
)
def test_json_dict_error_fields(body, detail_key):
    resp = make_response(500, body, "application/json")
    with pytest.raises(RuntimeError) as exc:
        _raise_with_detail(resp)
    expected = auth_error_msg.format(code=500, detail=detail_key)
    assert str(exc.value) == expected
    # original HTTPError should be __cause__
    assert isinstance(exc.value.__cause__, requests.HTTPError)


def test_json_list_error():
    resp = make_response(502, b'[1,2,3]', "application/json")
    with pytest.raises(RuntimeError) as exc:
        _raise_with_detail(resp)
    expected = auth_error_msg.format(code=502, detail="[1, 2, 3]")
    assert str(exc.value) == expected


def test_json_scalar_error():
    resp = make_response(503, b'42', "application/json")
    with pytest.raises(RuntimeError) as exc:
        _raise_with_detail(resp)
    expected = auth_error_msg.format(code=503, detail="42")
    assert str(exc.value) == expected


def test_plain_text_error():
    resp = make_response(404, b"Not found", "text/plain")
    with pytest.raises(RuntimeError) as exc:
        _raise_with_detail(resp)
    expected = auth_error_msg.format(code=404, detail="Not found")
    assert str(exc.value) == expected


def test_empty_body_error():
    resp = make_response(400, b"", "text/plain")
    with pytest.raises(RuntimeError) as exc:
        _raise_with_detail(resp)
    # no text → fallback to status code
    expected = auth_error_msg.format(code=400, detail="400")
    assert str(exc.value) == expected
