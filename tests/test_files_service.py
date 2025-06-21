# tests/test_files_service.py

import pytest
from requests import HTTPError

from easy_acumatica import AcumaticaClient
from easy_acumatica.sub_services.files import FilesService
from easy_acumatica.sub_services.records import RecordsService
from easy_acumatica.models.filter_builder import F
from easy_acumatica.models.query_builder import QueryOptions

API_VERSION = "24.200.001"
BASE = "https://fake"
LOGIN_URL = f"{BASE}/entity/auth/login"
LOGOUT_URL = f"{BASE}/entity/auth/logout"
FILE_ID = "f1e2d3c4"
FILE_URL = f"{BASE}/entity/Default/{API_VERSION}/files/{FILE_ID}"


@pytest.fixture
def client(requests_mock):
    # Stub login/logout
    requests_mock.post(LOGIN_URL, status_code=204)
    requests_mock.post(LOGOUT_URL, status_code=204)
    return AcumaticaClient(
        base_url=BASE,
        username="u",
        password="p",
        tenant="T",
        branch="B",
        verify_ssl=False,
        persistent_login=False,
    )


@pytest.fixture
def files_svc(client):
    return FilesService(client)


# -----------------------------------------------------------------------
# get_file
# -----------------------------------------------------------------------

def test_get_file_success(requests_mock, files_svc):
    data = b"\x00\x01\x02"
    requests_mock.get(FILE_URL, status_code=200, content=data)

    result = files_svc.get_file(API_VERSION, FILE_ID)
    assert result == data

    # find only the GET to our file URL
    gets = [
        req for req in requests_mock.request_history
        if req.method == "GET" and req.url == FILE_URL
    ]
    assert gets, "No GET to file endpoint"
    last = gets[-1]
    # header should include Accept: application/octet-stream
    assert last.headers["Accept"] == "application/octet-stream"


@pytest.mark.parametrize("status, detail", [
    (404, "Not Found"),
    (500, {"error": "oops"}),
])
def test_get_file_error(requests_mock, files_svc, status, detail):
    if isinstance(detail, dict):
        requests_mock.get(FILE_URL, status_code=status, json=detail)
    else:
        requests_mock.get(FILE_URL, status_code=status, text=detail)

    with pytest.raises(RuntimeError) as exc:
        files_svc.get_file(API_VERSION, FILE_ID)
    assert str(status) in str(exc.value)
    # detail appears
    assert (detail if isinstance(detail, str) else "oops") in str(exc.value)


# -----------------------------------------------------------------------
# attach_file_to_record
# -----------------------------------------------------------------------

@pytest.mark.parametrize("template, expected_url", [
    # absolute URL template
    (f"{BASE}/entity/Default/{API_VERSION}/files/.../{{filename}}",
     f"{BASE}/entity/Default/{API_VERSION}/files/.../test.bin"),
    # leading slash
    (f"/entity/Default/{API_VERSION}/files/.../{{filename}}",
     f"{BASE}/entity/Default/{API_VERSION}/files/.../test.bin"),
    # no leading slash
    (f"entity/Default/{API_VERSION}/files/.../{{filename}}",
     f"{BASE}/entity/Default/{API_VERSION}/files/.../test.bin"),
])
def test_attach_file_to_record_url_variants(requests_mock, files_svc, template, expected_url):
    # stub the PUT on the expected_url
    requests_mock.put(expected_url, status_code=204)

    content = b"\x99\x88"
    files_svc.attach_file_to_record(template, "test.bin", content, comment=None)

    puts = [
        req for req in requests_mock.request_history
        if req.method == "PUT" and req.url == expected_url
    ]
    assert puts, f"No PUT to {expected_url}"
    last = puts[-1]
    # body and headers
    assert last.body == content
    assert last.headers["Accept"] == "application/json"
    assert last.headers["Content-Type"] == "application/octet-stream"
    # no comment header
    assert "PX-CbFileComment" not in last.headers


def test_attach_file_with_comment(requests_mock, files_svc):
    template = f"/entity/Default/{API_VERSION}/files/abc/{{filename}}"
    url = f"{BASE}/entity/Default/{API_VERSION}/files/abc/my.txt"
    requests_mock.put(url, status_code=200)

    payload = b"hello"
    files_svc.attach_file_to_record(template, "my.txt", payload, comment="NOTE")

    # find the PUT
    puts = [
        req for req in requests_mock.request_history
        if req.method == "PUT" and req.url == url
    ]
    assert puts, "No PUT with comment header"
    last = puts[-1]
    assert last.headers["PX-CbFileComment"] == "NOTE"


@pytest.mark.parametrize("status", [400, 422, 500])
def test_attach_file_error(requests_mock, files_svc, status):
    template = f"/entity/Default/{API_VERSION}/files/X/{{filename}}"
    url = f"{BASE}/entity/Default/{API_VERSION}/files/X/doc.pdf"
    # return a JSON error
    requests_mock.put(url, status_code=status, json={"error": "fail"})
    with pytest.raises(RuntimeError) as exc:
        files_svc.attach_file_to_record(template, "doc.pdf", b"x", comment=None)
    assert "fail" in str(exc.value)


# -----------------------------------------------------------------------
# delete_file
# -----------------------------------------------------------------------

def test_delete_file_success(requests_mock, files_svc):
    """Tests successful file deletion (204 No Content)."""
    requests_mock.delete(FILE_URL, status_code=204)

    # This call should complete without raising an error
    result = files_svc.delete_file(API_VERSION, FILE_ID)
    assert result is None

    # Verify that a DELETE request was made to the correct URL
    deletes = [
        req for req in requests_mock.request_history
        if req.method == "DELETE" and req.url == FILE_URL
    ]
    assert deletes, "No DELETE request was made to the file endpoint"
    last = deletes[-1]
    assert last.headers["Accept"] == "application/json"

def test_delete_file_not_found_error(requests_mock, files_svc):
    """Tests that a 404 error during deletion raises a RuntimeError."""
    requests_mock.delete(FILE_URL, status_code=404, text="File not found")

    with pytest.raises(RuntimeError) as exc:
        files_svc.delete_file(API_VERSION, FILE_ID)
    
    assert "404" in str(exc.value)
    assert "File not found" in str(exc.value)

# -----------------------------------------------------------------------
# get_file_comments_by_key_field & by_id
# -----------------------------------------------------------------------

def test_get_file_comments_by_key_field(monkeypatch, files_svc):
    # stub RecordsService.get_record_by_key_field
    fake = {
        "files": [
            {"id": "1", "filename": "a.txt", "href": "/x/1", "comment": "c1"},
            {"id": "2", "filename": "b.txt", "href": "/x/2"},
        ]
    }
    monkeypatch.setattr(
        RecordsService,
        "get_record_by_key_field",
        lambda self, api, ent, key, val, options=None: fake
    )

    comments = files_svc.get_file_comments_by_key_field(API_VERSION, "Foo", "K", "V")
    assert comments == fake["files"]


def test_get_file_comments_by_id(monkeypatch, files_svc):
    fake = {
        "files": [
            {"id": "9", "filename": "z.txt", "href": "/y/9", "comment": "Zed"}
        ]
    }
    monkeypatch.setattr(
        RecordsService,
        "get_record_by_id",
        lambda self, api, ent, rec_id, options=None: fake
    )

    comments = files_svc.get_file_comments_by_id(API_VERSION, "Bar", "REC123")
    assert comments == fake["files"]
