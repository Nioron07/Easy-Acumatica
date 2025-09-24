# test_client_comprehensive.py

import json
import pickle
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
import requests
from unittest.mock import patch, mock_open

import pytest
from easy_acumatica import AcumaticaClient

# Constants from the mock server for verification
LATEST_DEFAULT_VERSION = "24.200.001"
OLD_DEFAULT_VERSION = "23.200.001"


class TestClientBasicFeatures:
    """Test basic client functionality and version detection."""
    
    def test_auto_detects_latest_endpoint_version(self, live_server_url):
        """
        Tests that the client, when no version is specified, automatically
        finds and uses the LATEST version of the endpoint from the server list.
        """
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            endpoint_name="Default",
            cache_methods=False
        )

        assert client.endpoints["Default"]["version"] == LATEST_DEFAULT_VERSION
        assert client.endpoint_version == LATEST_DEFAULT_VERSION
        result = client.tests.get_by_id("123")
        assert result["id"] == "123"
        client.close()
        print(f"\n✅ Client successfully auto-detected latest version: {LATEST_DEFAULT_VERSION}")


    def test_uses_specified_endpoint_version(self, live_server_url):
        """
        Tests that the client uses the EXPLICITLY provided version, even if it's
        not the latest one available on the server.
        """
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            endpoint_name="Default",
            endpoint_version=OLD_DEFAULT_VERSION,  # Specify the older version
            cache_methods=False
        )

        # The client's endpoint_version should be the specified one
        assert client.endpoint_version == OLD_DEFAULT_VERSION

        # Test API call with specified version
        result = client.tests.get_by_id("223") 
        assert result["id"] == "223"
        assert result["Name"]["value"] == "Old Specific Test Item"

        client.close()
        print(f"\n✅ Client correctly used specified version: {OLD_DEFAULT_VERSION}")

    def test_service_methods_generated(self, live_server_url):
        """Test that service methods are properly generated from schema."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            cache_methods=False
        )

        assert hasattr(client, 'tests')
        expected_methods = [
            'get_list', 'get_by_id', 'put_entity', 'delete_by_id',
            'invoke_action_test_action', 'get_ad_hoc_schema', 'put_file'
        ]
        for method_name in expected_methods:
            assert hasattr(client.tests, method_name)
        client.close()

    def test_inquiry_service_generated(self, live_server_url):
        """Test that inquiry service and methods are properly generated."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            cache_methods=False
        )

        assert "Inquiries" in client._service_instances
        inquiries_service = client._service_instances["Inquiries"]

        expected_inquiries = [
            'Account_Details', 'Customer_List', 'Inventory_Items',
            'GL_Trial_Balance', 'AR_Customer_Balance_Summary', 'IN_Inventory_Summary'
        ]
        for inquiry_method in expected_inquiries:
            assert hasattr(inquiries_service, inquiry_method), f"Inquiry method {inquiry_method} should exist"

        result = inquiries_service.Account_Details()
        assert 'value' in result
        assert len(result['value']) > 0
        client.close()


class TestModelGeneration:
    """Test dynamic model generation from schema."""
    
    def test_models_generated_from_schema(self, live_server_url):
        """Test that models are properly generated from OpenAPI schema."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            cache_methods=False
        )
        assert hasattr(client.models, 'TestModel')
        test_model = client.models.TestModel(Name="Test Name", Value="Test Value", IsActive=True)
        payload = test_model.to_acumatica_payload()
        assert 'Name' in payload
        assert payload['Name']['value'] == "Test Name"
        client.close()


class TestCachingBasic:
    """Test basic caching functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Provide a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url, monkeypatch):
        """Base configuration for client creation with isolated env."""
        monkeypatch.delenv("ACUMATICA_CACHE_METHODS", raising=False)
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_cache_disabled_no_files_created(self, base_client_config, temp_cache_dir):
        """Test that no cache files are created when caching is disabled."""
        client = AcumaticaClient(**base_client_config, cache_methods=False, cache_dir=temp_cache_dir)
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 0, "No .pkl cache files should be created when caching is disabled"
        client.close()

    def test_cache_enabled_creates_cache_file(self, base_client_config, temp_cache_dir):
        """Test that cache file is created when caching is enabled."""
        client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir, force_rebuild=True)
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1, "One cache file should be created"
        with open(cache_files[0], 'rb') as f:
            cache_data = pickle.load(f)
        assert cache_data['version'] == '1.1'
        assert 'model_hashes' in cache_data
        client.close()


class TestDifferentialCaching:
    """Test differential caching functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Provide a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_force_rebuild_updates_cache(self, base_client_config, temp_cache_dir):
        """Test that force rebuild properly updates the cache."""
        # Create initial cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        initial_stats = client1.get_performance_stats()
        client1.close()

        # Force rebuild
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        rebuild_stats = client2.get_performance_stats()
        client2.close()

        # Both should have similar model/service counts
        assert initial_stats['model_count'] == rebuild_stats['model_count']
        assert initial_stats['service_count'] == rebuild_stats['service_count']

    def test_cache_ttl_expiration(self, base_client_config, temp_cache_dir):
        """Test that cache respects TTL settings."""
        # Patch time.time to control cache age deterministically
        initial_time = time.time()
        with patch('time.time', return_value=initial_time):
            client1 = AcumaticaClient(
                **base_client_config,
                cache_methods=True,
                cache_dir=temp_cache_dir,
                cache_ttl_hours=1,
                force_rebuild=True
            )
            client1.close()

        # Simulate time passing beyond the TTL
        expired_time = initial_time + 3601  # 1 hour + 1 second
        with patch('time.time', return_value=expired_time):
            client2 = AcumaticaClient(
                **base_client_config,
                cache_methods=True,
                cache_dir=temp_cache_dir,
                cache_ttl_hours=1,
                force_rebuild=False
            )
            stats = client2.get_performance_stats()
            client2.close()

        assert stats['cache_misses'] > 0, "Should have cache misses due to TTL expiration"

    def test_different_endpoints_different_caches(self, base_client_config, temp_cache_dir):
        """Test that different endpoint configurations use different cache files."""
        # Create client with Default endpoint
        client1 = AcumaticaClient(
            **base_client_config,
            endpoint_name="Default",
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        client1.close()

        # Create client with different version - should create separate cache
        client2 = AcumaticaClient(
            **base_client_config,
            endpoint_version=OLD_DEFAULT_VERSION,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        client2.close()

        # Should have different cache files
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 2, "Should have separate cache files for different configurations"

    def test_cache_handles_invalid_data(self, base_client_config, temp_cache_dir):
        """Test that client handles corrupted or invalid cache data gracefully."""
        # Create a corrupted cache file
        cache_key = "test_cache"
        cache_file = temp_cache_dir / f"{cache_key}.pkl"
        
        # Write invalid data
        with open(cache_file, 'w') as f:
            f.write("invalid cache data")

        # Client should handle this gracefully and rebuild
        with patch.object(AcumaticaClient, '_get_cache_key', return_value=cache_key):
            client = AcumaticaClient(
                **base_client_config,
                cache_methods=True,
                cache_dir=temp_cache_dir,
                force_rebuild=False
            )

            # Should work despite corrupted cache
            assert len(client.list_models()) > 0
            client.close()


class TestDifferentialCachingAdvanced:
    """Advanced differential caching tests."""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_model_hash_calculation(self, base_client_config, temp_cache_dir):
        """Test that model hashes are calculated correctly."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Access private method to test hash calculation
        schema = client._fetch_schema(client.endpoint_name, client.endpoint_version)
        model_hashes = client._calculate_model_hashes(schema)

        # Should have hashes for models (excluding primitive wrappers)
        assert len(model_hashes) > 0
        assert 'TestModel' in model_hashes
        assert isinstance(model_hashes['TestModel'], str)
        assert len(model_hashes['TestModel']) == 32  # MD5 hash length

        client.close()

    def test_service_hash_calculation(self, base_client_config, temp_cache_dir):
        """Test that service hashes are calculated correctly."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        schema = client._fetch_schema(client.endpoint_name, client.endpoint_version)
        service_hashes = client._calculate_service_hashes(schema)

        # Should have hashes for services
        assert len(service_hashes) > 0
        assert 'Test' in service_hashes
        assert isinstance(service_hashes['Test'], str)
        assert len(service_hashes['Test']) == 32  # MD5 hash length

        client.close()

    def test_inquiry_hash_calculation(self, base_client_config, temp_cache_dir):
        """Test that inquiry hashes are calculated correctly."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Get the XML file path from the client's metadata directory
        xml_files = list((Path(client.__module__).parent / ".metadata").glob("*.xml"))
        if xml_files:
            xml_path = str(xml_files[0])
            inquiry_hashes = client._calculate_inquiry_hashes(xml_path)

            # Should have hashes for inquiries
            assert len(inquiry_hashes) > 0
            
            # Check some expected inquiries from mock XML
            expected_inquiries = ["Account Details", "Customer List", "Inventory Items"]
            for inquiry in expected_inquiries:
                if inquiry in inquiry_hashes:
                    assert isinstance(inquiry_hashes[inquiry], str)
                    assert len(inquiry_hashes[inquiry]) == 32  # MD5 hash length

        client.close()

    def test_cache_structure_validation(self, base_client_config, temp_cache_dir):
        """Test that saved cache has correct structure."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        client.close()

        # Load and validate cache structure
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1

        with open(cache_files[0], 'rb') as f:
            cache_data = pickle.load(f)

        # Validate cache structure
        required_keys = [
            'version', 'timestamp', 'schema_hash', 'model_hashes',
            'service_hashes', 'inquiry_hashes', 'models', 
            'service_definitions', 'inquiry_definitions', 'endpoint_info'
        ]

        for key in required_keys:
            assert key in cache_data, f"Cache should contain {key}"

        # Validate endpoint info
        endpoint_info = cache_data['endpoint_info']
        assert endpoint_info['name'] == 'Default'
        assert endpoint_info['base_url'] == base_client_config['base_url']
        assert endpoint_info['tenant'] == base_client_config['tenant']

    @patch('easy_acumatica.client.AcumaticaClient._fetch_gi_xml')
    def test_inquiry_xml_not_available(self, mock_fetch_xml, base_client_config, temp_cache_dir):
        """Test that client handles gracefully when inquiry XML is not available."""
        # Mock XML fetch to raise an exception
        mock_fetch_xml.side_effect = Exception("XML not available")

        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Client should still work, just without inquiries
        assert len(client.list_models()) > 0
        assert len(client.list_services()) > 0
        
        # Inquiries service might not exist or be empty
        stats = client.get_performance_stats()
        assert stats['model_count'] > 0

        client.close()


class TestCachePerformanceMetrics:
    """Test cache performance metrics and statistics."""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url, monkeypatch):
        """Base configuration with isolated env."""
        monkeypatch.delenv("ACUMATICA_CACHE_METHODS", raising=False)
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_performance_stats_no_cache(self, base_client_config, temp_cache_dir):
        """Test performance stats when caching is disabled."""
        client = AcumaticaClient(**base_client_config, cache_methods=False, cache_dir=temp_cache_dir)
        stats = client.get_performance_stats()
        assert stats['cache_enabled'] is False
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0
        client.close()

    def test_performance_stats_with_cache(self, base_client_config, temp_cache_dir):
        """Test performance stats when caching is enabled."""
        # First run - populate cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        client1.close()

        # Second run - use cache
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=False
        )

        stats = client2.get_performance_stats()

        assert stats['cache_enabled'] is True
        assert stats['startup_time'] > 0
        assert stats['model_count'] > 0
        assert stats['service_count'] > 0

        client2.close()

    def test_cache_stats_detailed(self, base_client_config, temp_cache_dir):
        """Test detailed cache statistics."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        cache_stats = client.get_cache_stats()

        # Should have additional cache-specific stats
        expected_additional_keys = [
            'cache_file_exists', 'cache_file_size_bytes', 
            'cache_file_path', 'differential_caching'
        ]

        for key in expected_additional_keys:
            assert key in cache_stats, f"Cache stats should contain {key}"

        assert cache_stats['cache_file_exists'] is True
        assert cache_stats['cache_file_size_bytes'] > 0
        assert cache_stats['differential_caching'] is True

        client.close()

    def test_utility_methods_work_with_cache(self, base_client_config, temp_cache_dir):
        """Test that utility methods work correctly with caching enabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Test list methods
        models = client.list_models()
        services = client.list_services()

        assert len(models) > 0
        assert len(services) > 0
        assert 'TestModel' in models
        assert 'Test' in services

        # Test search methods
        test_models = client.search_models('test')
        test_services = client.search_services('test')

        assert len(test_models) > 0
        assert len(test_services) > 0

        # Test info methods
        if 'TestModel' in models:
            model_info = client.get_model_info('TestModel')
            assert 'name' in model_info
            assert 'fields' in model_info

        if 'Test' in services:
            service_info = client.get_service_info('Test')
            assert 'name' in service_info
            assert 'methods' in service_info

        client.close()


class TestCacheClearAndMaintenance:
    """Test cache clearing and maintenance functionality."""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_clear_cache_functionality(self, base_client_config, temp_cache_dir):
        """Test that clear_cache works correctly."""
        # Create cache
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Verify cache exists
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) > 0, "Cache files should exist"

        # Clear cache
        client.clear_cache()

        # Verify cache is cleared (directory should be empty or recreated)
        cache_files_after = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files_after) == 0, "Cache files should be cleared"

        # Stats should reflect cleared cache
        stats = client.get_performance_stats()
        assert stats['cache_hits'] == 0
        assert stats['cache_misses'] == 0

        client.close()

    def test_help_system_works(self, base_client_config, temp_cache_dir, capsys):
        """Test that the help system works with caching enabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Test general help
        client.help()
        captured = capsys.readouterr()
        assert "AcumaticaClient Help" in captured.out
        assert "Cache: enabled" in captured.out

        # Test specific help topics
        client.help('cache')
        captured = capsys.readouterr()
        assert "Caching System Help" in captured.out
        assert "Status: Enabled" in captured.out

        client.help('performance')
        captured = capsys.readouterr()
        assert "Performance Help" in captured.out

        client.close()


# Integration test combining multiple features
class TestCacheIntegration:
    """Integration tests for cache with other features."""

    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_cached_client_api_operations(self, base_client_config, temp_cache_dir):
        """Test that API operations work correctly with caching enabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Test basic API operations work with cached client
        result = client.tests.get_list()
        assert isinstance(result, list)
        assert len(result) > 0

        # Test specific entity retrieval
        entity = client.tests.get_by_id("123")
        assert entity["id"] == "123"

        # Test model creation and API call
        test_model = client.models.TestModel(
            Name="Cache Test",
            Value="Test Value",
            IsActive=True
        )

        # Test PUT operation
        put_result = client.tests.put_entity(test_model)
        assert "id" in put_result

        client.close()

    def test_cache_with_environment_loading(self, live_server_url, temp_cache_dir, monkeypatch):
        """Test that caching works with environment variable loading."""
        monkeypatch.setenv("ACUMATICA_URL", live_server_url)
        monkeypatch.setenv("ACUMATICA_USERNAME", "test_user")
        monkeypatch.setenv("ACUMATICA_PASSWORD", "test_password")
        monkeypatch.setenv("ACUMATICA_TENANT", "test_tenant")
        monkeypatch.setenv("ACUMATICA_CACHE_METHODS", "true")
        monkeypatch.setenv("ACUMATICA_CACHE_TTL_HOURS", "24")

        client = AcumaticaClient(
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        stats = client.get_performance_stats()
        assert stats['cache_enabled'] is True
        assert len(client.list_models()) > 0
        client.close()


class TestNewStatisticsFeatures:
    """Test all new statistics and debugging features added to AcumaticaClient."""

    @pytest.fixture
    def client(self, live_server_url, reset_server_state):
        """Provide a client instance for testing."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            cache_methods=False
        )
        yield client
        client.close()

    def test_get_connection_stats(self, client):
        """Test get_connection_stats method returns proper metrics."""
        stats = client.get_connection_stats()

        # Check required fields
        assert 'session_headers' in stats
        assert 'verify_ssl' in stats
        assert 'timeout' in stats
        assert 'connection_pools' in stats
        assert 'rate_limit' in stats

        # Check rate limit structure
        assert 'calls_per_second' in stats['rate_limit']
        assert 'burst_size' in stats['rate_limit']
        assert 'current_tokens' in stats['rate_limit']

        # Verify types
        assert isinstance(stats['verify_ssl'], bool)
        assert isinstance(stats['timeout'], (int, float))
        assert stats['rate_limit']['calls_per_second'] > 0

    def test_get_session_info(self, client):
        """Test get_session_info method returns session details."""
        info = client.get_session_info()

        # Check required fields
        assert 'base_url' in info
        assert 'tenant' in info
        assert 'username' in info
        assert 'endpoint' in info
        assert 'logged_in' in info
        assert 'persistent_login' in info
        assert 'retry_on_idle_logout' in info
        assert 'session_age' in info

        # Verify values match configuration
        assert info['base_url'] == client.base_url
        assert info['tenant'] == client.tenant
        assert info['username'] == client.username
        assert isinstance(info['logged_in'], bool)
        assert info['session_age'] >= 0

    def test_get_api_usage_stats(self, client):
        """Test get_api_usage_stats tracks API calls properly."""
        client.reset_statistics() # Reset for a clean test
        # Make some test requests
        client.tests.get_list()
        client.tests.get_by_id("123")

        stats = client.get_api_usage_stats()

        # Check required fields
        assert 'total_requests' in stats
        assert 'total_errors' in stats
        assert 'requests_by_method' in stats
        assert 'requests_by_endpoint' in stats
        assert 'average_response_time' in stats
        assert 'last_request_time' in stats

        # After making requests, stats should be populated
        assert stats['total_requests'] == 2
        assert 'GET' in stats['requests_by_method']
        assert 'Test' in stats['requests_by_endpoint']
        assert stats['requests_by_method']['GET'] == 2
        assert stats['requests_by_endpoint']['Test'] == 2

    def test_get_schema_info(self, client):
        """Test get_schema_info returns model and schema details."""
        info = client.get_schema_info()

        # Check required fields
        assert 'endpoint_name' in info
        assert 'endpoint_version' in info
        assert 'available_endpoints' in info
        assert 'total_models' in info
        assert 'total_services' in info
        assert 'custom_fields_count' in info
        assert 'schema_cache_size_bytes' in info
        assert 'cache_directory' in info
        assert 'cache_ttl_hours' in info

        # Verify reasonable values
        assert info['total_models'] > 0
        assert info['total_services'] > 0
        assert info['custom_fields_count'] >= 0
        assert isinstance(info['available_endpoints'], list)

    def test_test_connection(self, client):
        """Test test_connection method checks server connectivity."""
        result = client.test_connection()

        # Check required fields
        assert 'reachable' in result
        assert 'response_time' in result
        assert 'endpoints_available' in result
        assert 'error' in result

        # In test environment should be reachable
        assert result['reachable'] is True
        assert result['response_time'] > 0
        assert result['endpoints_available'] is True
        assert result['error'] is None

    def test_validate_credentials(self, client):
        """Test validate_credentials checks auth status."""
        result = client.validate_credentials()

        # Check required fields
        assert 'valid' in result
        assert 'error' in result

        # In test environment with valid creds
        assert result['valid'] is True
        assert result['error'] is None

    def test_get_last_request_info(self, client):
        """Test get_last_request_info tracks last API call."""
        client.tests.get_by_id("123")

        # Now should have info
        info = client.get_last_request_info()
        assert info is not None
        assert 'timestamp' in info
        assert 'method' in info
        assert 'url' in info
        assert 'status_code' in info
        assert 'response_time' in info
        assert 'error' in info

        # Verify it's tracking our request
        assert info['method'] == 'GET'
        assert 'Test/123' in info['url']
        assert info['status_code'] == 200

    def test_get_error_history(self, client):
        """Test get_error_history tracks errors properly."""
        client.reset_statistics()
        initial_count = len(client.get_error_history())

        # Try to trigger an error
        with pytest.raises(Exception):
            client.tests.get_by_id("NONEXISTENT999")

        # Check error history
        errors = client.get_error_history(5)
        assert len(errors) > initial_count

        # Check error structure
        error = errors[0]
        assert 'timestamp' in error
        assert 'method' in error
        assert 'url' in error
        assert 'message' in error
        assert error['status_code'] == 404

    def test_enable_request_history(self, client):
        """Test request history tracking can be enabled/disabled."""
        client.enable_request_history(max_items=10)

        for i in range(3):
            client.tests.get_list()

        history = client.get_request_history(limit=5)
        assert isinstance(history, list)
        assert len(history) == 3

        # Check request structure
        request = history[0]
        assert 'timestamp' in request
        assert 'method' in request
        assert 'url' in request
        assert 'status_code' in request
        assert 'response_time' in request

    def test_get_health_status(self, client):
        """Test get_health_status provides overall health metrics."""
        status = client.get_health_status()

        # Check required fields
        assert 'status' in status
        assert 'connection_reachable' in status
        assert 'logged_in' in status
        assert 'error_rate_percent' in status

        # Check status value
        assert status['status'] in ['healthy', 'warning', 'degraded', 'unhealthy']
        assert status['connection_reachable'] is True
        assert status['logged_in'] is True

    def test_get_rate_limit_status(self, client):
        """Test get_rate_limit_status returns rate limiting info."""
        status = client.get_rate_limit_status()

        # Check required fields
        assert 'calls_per_second' in status
        assert 'burst_size' in status
        assert 'tokens_available' in status
        assert 'tokens_percent' in status
        assert 'last_call_time' in status

        # Verify rate limiter is configured
        assert status['calls_per_second'] > 0
        assert status['burst_size'] >= status['calls_per_second']
        assert status['tokens_available'] > 0

    def test_reset_statistics(self, client):
        """Test reset_statistics clears tracked metrics."""
        client.tests.get_list()

        stats_before = client.get_api_usage_stats()
        assert stats_before['total_requests'] > 0

        client.reset_statistics()

        stats_after = client.get_api_usage_stats()
        assert stats_after['total_requests'] == 0
        assert stats_after['total_errors'] == 0
        assert len(stats_after['requests_by_method']) == 0
        assert len(stats_after['requests_by_endpoint']) == 0

class TestCustomEndpoints:
    def test_client_respects_custom_endpoint_for_entities(self, live_server_url, reset_server_state):
        """
        Validates that a custom 'endpoint_name' in the client configuration is
        used for standard entity API calls, resolving the original bug.
        """
        # ARRANGE: Initialize the client with a non-default endpoint name
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant",
            endpoint_name="Custom",  # Use the custom endpoint defined in the mock server
            cache_methods=False
        )

        # ASSERT INITIAL STATE: Check if the client is configured as expected
        assert client.endpoint_name == "Custom"
        assert "Custom" in client.endpoints
        assert client.endpoint_version is not None, "Client should auto-detect the version for the custom endpoint."

        # ACT: Call a service method. The mock server is configured to return a
        # unique response only for requests sent to the '/entity/Custom/...' URL.
        result = client.tests.get_by_id("CUST-01")

        # ASSERT RESULT: Verify that we received the unique response from the custom endpoint,
        # proving the request was routed correctly.
        assert result is not None
        assert isinstance(result, dict)
        assert result.get("source") == "Custom Endpoint", "Response should originate from the custom endpoint."
        assert result.get("id") == "CUST-01"

        print("\\n Client correctly routed a standard entity request to the custom endpoint.")
        client.close()

    def test_client_respects_custom_endpoint_for_inquiries(self, live_server_url, reset_server_state):
            """
            Validates that a custom 'endpoint_name' is also correctly used for
            Generic Inquiry calls.
            """
            # ARRANGE: Tell the mock server to use the XML schema that includes "Vendor_List"
            requests.post(f"{live_server_url}/test/xml/version", json={"version": "v2"})

            # ARRANGE: Initialize the client with the custom endpoint
            client = AcumaticaClient(
                base_url=live_server_url,
                username="test_user",
                password="test_password",
                tenant="test_tenant",
                endpoint_name="Custom",
                cache_methods=False
            )

            # ACT: Call a generic inquiry.
            result = client.inquiries.Vendor_List()

            # ASSERT: Check for the unique response from the custom inquiry endpoint.
            assert result is not None
            assert isinstance(result, dict)
            assert result.get("source") == "Custom Inquiry Endpoint"
            assert len(result.get("value", [])) == 1
            assert result["value"][0]["VendorID"]["value"] == "V-CUSTOM-01"

            print("\n Client correctly routed a Generic Inquiry request to the custom endpoint.")
            client.close()
