# test_client_comprehensive.py

import json
import pickle
import tempfile
import time
import xml.etree.ElementTree as ET
from pathlib import Path
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
            cache_methods=False  # Disable caching for this test
        )

        # Verify that the client stored the correct (latest) version
        assert client.endpoints["Default"]["version"] == LATEST_DEFAULT_VERSION
        assert client.endpoint_version == LATEST_DEFAULT_VERSION

        # Test that API calls work with auto-detected version
        result = client.tests.get_by_id("123")
        assert result["id"] == "123"
        assert result["Name"]["value"] == "Specific Test Item"

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
        result = client.tests.get_by_id("223")  # Different ID for old version
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

        # Check that the Test service exists
        assert hasattr(client, 'tests'), "Tests service should be available"

        # Check that expected methods exist
        expected_methods = [
            'get_list', 'get_by_id', 'put_entity', 'delete_by_id',
            'invoke_action_test_action', 'get_ad_hoc_schema', 'put_file'
        ]

        for method_name in expected_methods:
            assert hasattr(client.tests, method_name), f"Method {method_name} should exist"

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

        # Check that inquiries service exists
        assert "Inquirie" in client._service_instances, "Inquiries service should be created"

        inquiries_service = client._service_instances["Inquirie"]

        # Check that inquiry methods are generated based on mock XML
        expected_inquiries = [
            'account_details', 'customer_list', 'inventory_items',
            'gl_trial_balance', 'ar_customer_balance_summary', 'in_inventory_summary'
        ]

        for inquiry_method in expected_inquiries:
            assert hasattr(inquiries_service, inquiry_method), f"Inquiry method {inquiry_method} should exist"

        # Test calling an inquiry
        result = inquiries_service.account_details()
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

        # Check that TestModel exists
        assert hasattr(client.models, 'TestModel'), "TestModel should be generated"

        # Create an instance and verify it works
        test_model = client.models.TestModel(
            Name="Test Name",
            Value="Test Value",
            IsActive=True
        )

        # Test that it has the to_acumatica_payload method
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
    def base_client_config(self, live_server_url):
        """Base configuration for client creation."""
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_cache_disabled_no_files_created(self, base_client_config, temp_cache_dir):
        """Test that no cache files are created when caching is disabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=False,
            cache_dir=temp_cache_dir
        )

        # Verify no cache files exist
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 0, "No cache files should be created when caching is disabled"

        client.close()

    def test_cache_enabled_creates_cache_file(self, base_client_config, temp_cache_dir):
        """Test that cache file is created when caching is enabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True  # Force initial cache creation
        )

        # Verify cache file exists
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1, "One cache file should be created"

        # Verify cache file has expected structure
        with open(cache_files[0], 'rb') as f:
            cache_data = pickle.load(f)

        assert cache_data['version'] == '1.1', "Cache should use latest version format"
        assert 'model_hashes' in cache_data
        assert 'service_hashes' in cache_data
        assert 'inquiry_hashes' in cache_data
        assert 'models' in cache_data

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
        """Base configuration for client creation."""
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_cache_warm_start_performance(self, base_client_config, temp_cache_dir):
        """Test that warm cache starts are significantly faster than cold starts."""
        # First run - cold start with cache creation
        start_time = time.time()
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        cold_start_time = time.time() - start_time
        
        # Verify client works correctly
        assert len(client1.list_models()) > 0
        assert len(client1.list_services()) > 0
        client1.close()

        # Second run - warm start using existing cache
        start_time = time.time()
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=False
        )
        warm_start_time = time.time() - start_time

        # Verify client works correctly
        assert len(client2.list_models()) > 0
        assert len(client2.list_services()) > 0

        # Check cache statistics
        stats = client2.get_performance_stats()
        assert stats['cache_hits'] > 0, "Should have cache hits on warm start"

        client2.close()

        # Performance assertion - warm start should be faster
        print(f"\nCold start: {cold_start_time:.2f}s, Warm start: {warm_start_time:.2f}s")
        assert warm_start_time < cold_start_time, "Warm start should be faster than cold start"

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
        # Create cache with very short TTL
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            cache_ttl_hours=0.001,  # Very short TTL (about 3.6 seconds)
            force_rebuild=True
        )
        client1.close()

        # Wait for TTL to expire
        time.sleep(4)

        # Create new client - should rebuild due to expired TTL
        start_time = time.time()
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            cache_ttl_hours=0.001,
            force_rebuild=False  # Don't force, but TTL should trigger rebuild
        )
        rebuild_time = time.time() - start_time

        stats = client2.get_performance_stats()
        client2.close()

        # Should have cache misses due to TTL expiration
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
    def base_client_config(self, live_server_url):
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30
        }

    def test_performance_stats_no_cache(self, base_client_config, temp_cache_dir):
        """Test performance stats when caching is disabled."""
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=False,
            cache_dir=temp_cache_dir
        )

        stats = client.get_performance_stats()
        
        # Verify expected stats structure
        expected_keys = [
            'startup_time', 'cache_enabled', 'cache_hits', 'cache_misses',
            'model_count', 'service_count', 'endpoint_count'
        ]
        
        for key in expected_keys:
            assert key in stats, f"Stats should contain {key}"

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

    def test_cache_with_environment_loading(self, base_client_config, temp_cache_dir):
        """Test that caching works with environment variable loading."""
        # Create a temporary .env file
        env_file = temp_cache_dir / ".env"
        env_content = f"""
ACUMATICA_URL={base_client_config['base_url']}
ACUMATICA_USERNAME={base_client_config['username']}
ACUMATICA_PASSWORD={base_client_config['password']}
ACUMATICA_TENANT={base_client_config['tenant']}
ACUMATICA_CACHE_METHODS=true
ACUMATICA_CACHE_TTL_HOURS=24
"""
        env_file.write_text(env_content)

        # Create client with env file
        client = AcumaticaClient(
            env_file=env_file,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )

        # Should have loaded cache settings from env
        stats = client.get_performance_stats()
        assert stats['cache_enabled'] is True

        # Should work normally
        assert len(client.list_models()) > 0

        client.close()