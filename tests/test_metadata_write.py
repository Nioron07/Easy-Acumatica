from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_response(content: bytes = b"<xml/>") -> MagicMock:
    resp = MagicMock()
    resp.content = content
    resp.raise_for_status.return_value = None
    return resp


# ---------------------------------------------------------------------------
# client.AcumaticaClient._fetch_gi_xml
# ---------------------------------------------------------------------------

class TestClientFetchGiXml:
    """_fetch_gi_xml on AcumaticaClient must write into self.cache_dir, not the package dir."""

    def _make_client_stub(self, cache_dir: Path) -> MagicMock:
        """Return a minimal AcumaticaClient-like object with just what _fetch_gi_xml needs."""
        from easy_acumatica.client import AcumaticaClient
        client = MagicMock(spec=AcumaticaClient)
        client.base_url = "https://acumatica.example.com"
        client.tenant = "TestTenant"
        client.username = "user"
        client._password = "pass"
        client.cache_dir = cache_dir
        client._cache_dir_overridden = True
        # Bind the real method to our stub so we test the actual implementation
        client._fetch_gi_xml = AcumaticaClient._fetch_gi_xml.__get__(client, AcumaticaClient)
        return client

    def test_writes_to_cache_dir_not_package_dir(self, tmp_path):
        """Metadata XML must land in cache_dir/.metadata, never in the package directory."""
        client = self._make_client_stub(tmp_path)
        package_dir = Path(__file__).parent.parent / "src" / "easy_acumatica"

        with patch("requests.get", return_value=_make_mock_response(b"<metadata/>")):
            result_path = client._fetch_gi_xml()

        written = Path(result_path)
        assert written.exists(), "Output file was not created"
        assert written.is_relative_to(tmp_path), (
            f"File was written to {written}, expected a path under cache_dir {tmp_path}"
        )
        assert not written.is_relative_to(package_dir), (
            f"File must NOT be written inside the package directory {package_dir}"
        )

    def test_written_under_dot_metadata_subdir(self, tmp_path):
        """The file should live in cache_dir/.metadata/."""
        client = self._make_client_stub(tmp_path)

        with patch("requests.get", return_value=_make_mock_response(b"<metadata/>")):
            result_path = client._fetch_gi_xml()

        assert Path(result_path).parent == tmp_path / ".metadata"

    def test_filename_is_odata_inquiries_schema(self, tmp_path):
        client = self._make_client_stub(tmp_path)

        with patch("requests.get", return_value=_make_mock_response(b"<x/>")):
            result_path = client._fetch_gi_xml()

        assert Path(result_path).name == "odata_inquiries_schema.xml"

    def test_file_content_matches_response(self, tmp_path):
        client = self._make_client_stub(tmp_path)
        payload = b"<inquiries>test</inquiries>"

        with patch("requests.get", return_value=_make_mock_response(payload)):
            result_path = client._fetch_gi_xml()

        assert Path(result_path).read_bytes() == payload

    def test_respects_custom_cache_dir(self, tmp_path):
        """Passing a non-default cache_dir should control where metadata lands."""
        custom_dir = tmp_path / "my_custom_cache"
        client = self._make_client_stub(custom_dir)

        with patch("requests.get", return_value=_make_mock_response(b"<x/>")):
            result_path = client._fetch_gi_xml()

        assert Path(result_path).is_relative_to(custom_dir)

    def test_raises_on_http_error(self, tmp_path):
        """HTTP errors should propagate out of _fetch_gi_xml."""
        import requests as req
        client = self._make_client_stub(tmp_path)
        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = req.HTTPError("404")

        with patch("requests.get", return_value=bad_resp):
            with pytest.raises(req.HTTPError):
                client._fetch_gi_xml()

    def test_no_override_writes_to_package_dir(self, tmp_path):
        """When cache_dir is not overridden, metadata must land in the package directory."""
        from easy_acumatica.client import AcumaticaClient
        package_dir = Path(__file__).parent.parent / "src" / "easy_acumatica"

        client = MagicMock(spec=AcumaticaClient)
        client.base_url = "https://acumatica.example.com"
        client.tenant = "TestTenant"
        client.username = "user"
        client._password = "pass"
        client.cache_dir = tmp_path / "should_not_be_used"
        client._cache_dir_overridden = False
        client._fetch_gi_xml = AcumaticaClient._fetch_gi_xml.__get__(client, AcumaticaClient)

        makedirs_calls = []
        with patch("requests.get", return_value=_make_mock_response(b"<x/>")):
            with patch("os.makedirs", side_effect=lambda p, **kw: makedirs_calls.append(p)):
                with patch("builtins.open", mock_open()):
                    client._fetch_gi_xml()

        assert makedirs_calls, "os.makedirs was never called"
        metadata_dir = makedirs_calls[0]
        assert str(package_dir) in metadata_dir, (
            f"Expected package_dir {package_dir} in makedirs call, got: {metadata_dir}"
        )
        assert "should_not_be_used" not in metadata_dir, (
            "cache_dir was used even though _cache_dir_overridden is False"
        )


# ---------------------------------------------------------------------------
# service_factory.ServiceFactory._fetch_gi_xml
# ---------------------------------------------------------------------------

class TestServiceFactoryFetchGiXml:
    """ServiceFactory._fetch_gi_xml must also write into client.cache_dir."""

    def _make_factory_stub(self, cache_dir: Path) -> MagicMock:
        from easy_acumatica.service_factory import ServiceFactory

        inner_client = MagicMock()
        inner_client.base_url = "https://acumatica.example.com"
        inner_client.tenant = "TestTenant"
        inner_client.username = "user"
        inner_client._password = "pass"
        inner_client.cache_dir = cache_dir
        inner_client._cache_dir_overridden = True

        factory = MagicMock(spec=ServiceFactory)
        factory._client = inner_client
        factory._fetch_gi_xml = ServiceFactory._fetch_gi_xml.__get__(factory, ServiceFactory)
        return factory

    def test_writes_to_cache_dir_not_package_dir(self, tmp_path):
        factory = self._make_factory_stub(tmp_path)
        package_dir = Path(__file__).parent.parent / "src" / "easy_acumatica"

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<schema/>")):
            result_path = factory._fetch_gi_xml()

        written = Path(result_path)
        assert written.exists()
        assert written.is_relative_to(tmp_path), (
            f"File written to {written}, expected under cache_dir {tmp_path}"
        )
        assert not written.is_relative_to(package_dir), (
            f"File must NOT be written inside the package directory {package_dir}"
        )

    def test_written_under_dot_metadata_subdir(self, tmp_path):
        factory = self._make_factory_stub(tmp_path)

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<x/>")):
            result_path = factory._fetch_gi_xml()

        assert Path(result_path).parent == tmp_path / ".metadata"

    def test_filename_is_odata_schema(self, tmp_path):
        factory = self._make_factory_stub(tmp_path)

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<x/>")):
            result_path = factory._fetch_gi_xml()

        assert Path(result_path).name == "odata_schema.xml"

    def test_file_content_matches_response(self, tmp_path):
        factory = self._make_factory_stub(tmp_path)
        payload = b"<schema>test</schema>"

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(payload)):
            result_path = factory._fetch_gi_xml()

        assert Path(result_path).read_bytes() == payload

    def test_respects_custom_cache_dir(self, tmp_path):
        custom_dir = tmp_path / "custom"
        factory = self._make_factory_stub(custom_dir)

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<x/>")):
            result_path = factory._fetch_gi_xml()

        assert Path(result_path).is_relative_to(custom_dir)

    def test_raises_on_http_error(self, tmp_path):
        import requests as req
        factory = self._make_factory_stub(tmp_path)
        bad_resp = MagicMock()
        bad_resp.raise_for_status.side_effect = req.HTTPError("500")

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=bad_resp):
            with pytest.raises(req.HTTPError):
                factory._fetch_gi_xml()

    def test_no_override_writes_to_package_dir(self, tmp_path):
        """When cache_dir is not overridden, metadata must land in the package directory."""
        from easy_acumatica.service_factory import ServiceFactory
        package_dir = Path(__file__).parent.parent / "src" / "easy_acumatica"

        inner_client = MagicMock()
        inner_client.base_url = "https://acumatica.example.com"
        inner_client.tenant = "TestTenant"
        inner_client.username = "user"
        inner_client._password = "pass"
        inner_client.cache_dir = tmp_path / "should_not_be_used"
        inner_client._cache_dir_overridden = False

        factory = MagicMock(spec=ServiceFactory)
        factory._client = inner_client
        factory._fetch_gi_xml = ServiceFactory._fetch_gi_xml.__get__(factory, ServiceFactory)

        makedirs_calls = []
        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<x/>")):
            with patch("os.makedirs", side_effect=lambda p, **kw: makedirs_calls.append(p)):
                with patch("builtins.open", mock_open()):
                    factory._fetch_gi_xml()

        assert makedirs_calls, "os.makedirs was never called"
        metadata_dir = makedirs_calls[0]
        assert str(package_dir) in metadata_dir, (
            f"Expected package_dir {package_dir} in makedirs call, got: {metadata_dir}"
        )
        assert "should_not_be_used" not in metadata_dir, (
            "cache_dir was used even though _cache_dir_overridden is False"
        )


# ---------------------------------------------------------------------------
# Writable cache_dir override (Lambda scenario)
# ---------------------------------------------------------------------------

class TestCacheDirOverride:
    """With cache_dir overridden, _fetch_gi_xml writes to cache_dir even if the package dir would fail."""

    def test_client_succeeds_with_writable_cache_dir_when_package_dir_readonly(self, tmp_path):
        """
        Even when the package directory is read-only, _fetch_gi_xml must
        succeed because it writes only to cache_dir (which is under tmp_path here).
        """
        from easy_acumatica.client import AcumaticaClient

        client = MagicMock(spec=AcumaticaClient)
        client.base_url = "https://acumatica.example.com"
        client.tenant = "Tenant"
        client.username = "u"
        client._password = "p"
        client.cache_dir = tmp_path / "lambda_tmp"
        client._cache_dir_overridden = True
        client._fetch_gi_xml = AcumaticaClient._fetch_gi_xml.__get__(client, AcumaticaClient)

        with patch("requests.get", return_value=_make_mock_response(b"<ok/>")):
            result = client._fetch_gi_xml()

        assert Path(result).read_bytes() == b"<ok/>"
        assert Path(result).is_relative_to(tmp_path)

    def test_factory_succeeds_with_writable_cache_dir_when_package_dir_readonly(self, tmp_path):
        from easy_acumatica.service_factory import ServiceFactory

        inner = MagicMock()
        inner.base_url = "https://acumatica.example.com"
        inner.tenant = "Tenant"
        inner.username = "u"
        inner._password = "p"
        inner.cache_dir = tmp_path / "lambda_tmp"
        inner._cache_dir_overridden = True

        factory = MagicMock(spec=ServiceFactory)
        factory._client = inner
        factory._fetch_gi_xml = ServiceFactory._fetch_gi_xml.__get__(factory, ServiceFactory)

        with patch("easy_acumatica.service_factory.requests.get",
                   return_value=_make_mock_response(b"<ok/>")):
            result = factory._fetch_gi_xml()

        assert Path(result).read_bytes() == b"<ok/>"
        assert Path(result).is_relative_to(tmp_path)
