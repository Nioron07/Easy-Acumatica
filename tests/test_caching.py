# test_differential_caching_advanced.py

import json
import pickle
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest
import requests
from easy_acumatica import AcumaticaClient


class TestSchemaChangeDifferentialCaching:
    """Test differential caching when schema changes occur."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        # CORRECTED: Removed force_rebuild from the base config to avoid conflicts
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30,
            'cache_methods': True,
        }

    def test_schema_change_triggers_differential_update(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test that schema changes trigger proper differential updates."""
        client1 = AcumaticaClient(**base_client_config, cache_dir=temp_cache_dir, force_rebuild=True)
        initial_models = client1.list_models()
        client1.close()

        requests.post(f"{live_server_url}/test/schema/version", json={"version": "v2"})

        client2 = AcumaticaClient(**base_client_config, cache_dir=temp_cache_dir, force_rebuild=False)
        updated_models = client2.list_models()
        updated_stats = client2.get_performance_stats()
        client2.close()

        assert len(updated_models) > len(initial_models)
        assert 'ExtendedTestModel' in updated_models
        assert updated_stats['cache_hits'] > 0
        assert updated_stats['cache_misses'] > 0


    def test_model_addition_differential_caching(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test differential caching when new models are added."""
        
        # Create initial cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        # Verify initial state
        assert 'TestModel' in client1.list_models()
        assert 'ExtendedTestModel' not in client1.list_models()
        client1.close()

        # Change schema to add new model
        requests.post(f"{live_server_url}/test/schema/version", json={"version": "v2"})
        
        # Create new client - should add new model via differential update
        client2 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir
        )
        
        # Verify new model was added
        models = client2.list_models()
        assert 'TestModel' in models, "Original model should still exist"
        assert 'ExtendedTestModel' in models, "New model should be added"
        
        # Test that new model works
        extended_model = client2.models.ExtendedTestModel(
            Name="Extended Test",
            ExtensionField="Extension Value",
            Priority=1
        )
        
        payload = extended_model.to_acumatica_payload()
        assert 'ExtensionField' in payload
        assert payload['ExtensionField']['value'] == "Extension Value"
        
        client2.close()

    def test_service_addition_differential_caching(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test differential caching when new services are added."""
        
        # Create initial cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        services = client1.list_services()
        assert 'Test' in services
        assert 'ExtendedTest' not in services
        assert not hasattr(client1, 'extended_tests')
        client1.close()

        # Change schema to add new service
        requests.post(f"{live_server_url}/test/schema/version", json={"version": "v2"})
        
        # Create new client - should add new service
        client2 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir
        )
        
        updated_services = client2.list_services()
        assert 'Test' in updated_services, "Original service should still exist"
        assert 'ExtendedTest' in updated_services, "New service should be added"
        
        # Verify service attribute exists and has expected methods
        assert hasattr(client2, 'extended_tests'), "Extended test service should be available"
        
        extended_service = client2.extended_tests
        assert hasattr(extended_service, 'get_list'), "Service should have get_list method"
        assert hasattr(extended_service, 'put_entity'), "Service should have put_entity method"
        
        client2.close()


class TestInquiryDifferentialCaching:
    """Test differential caching for Generic Inquiries."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def base_client_config(self, live_server_url):
        # CORRECTED: Removed force_rebuild from the base config
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30,
            'cache_methods': True,
        }

    def test_inquiry_xml_change_triggers_update(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test that changes to inquiry XML trigger differential updates."""
        client1 = AcumaticaClient(**base_client_config, cache_dir=temp_cache_dir, force_rebuild=True)
        inquiries_service1 = client1._service_instances.get("Inquirie")
        assert hasattr(inquiries_service1, 'IN_Inventory_Summary')
        assert not hasattr(inquiries_service1, 'Vendor_List')
        client1.close()

        requests.post(f"{live_server_url}/test/xml/version", json={"version": "v2"})

        client2 = AcumaticaClient(**base_client_config, cache_dir=temp_cache_dir, force_rebuild=False)
        inquiries_service2 = client2._service_instances.get("Inquirie")
        assert not hasattr(inquiries_service2, 'IN_Inventory_Summary')
        assert hasattr(inquiries_service2, 'Vendor_List')
        client2.close()

    def test_inquiry_removal_differential_caching(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test that inquiry removals are handled correctly."""
        
        # Create initial cache 
        client1 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        inquiries_service = client1._service_instances.get("Inquirie")
        if inquiries_service:
            # Verify original inquiry exists
            assert hasattr(inquiries_service, 'in_inventory_summary'), "Should have inventory summary inquiry"
        
        client1.close()

        # Change to v2 XML which removes the inventory summary inquiry
        requests.post(f"{live_server_url}/test/xml/version", json={"version": "v2"})
        
        client2 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir
        )
        
        inquiries_service = client2._service_instances.get("Inquirie")
        if inquiries_service:
            # Removed inquiry should no longer exist
            assert not hasattr(inquiries_service, 'in_inventory_summary'), "Removed inquiry should be gone"
            
            # Other inquiries should still exist
            assert hasattr(inquiries_service, 'account_details'), "Other inquiries should remain"
        
        client2.close()


class TestCacheConsistencyAndReliability:
    """Test cache consistency and reliability under various conditions."""
    
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

    def test_concurrent_cache_access(self, base_client_config, temp_cache_dir):
        """Test that cache handles concurrent access gracefully."""
        import threading
        import queue
        
        results = queue.Queue()
        errors = queue.Queue()
        
        def create_client(thread_id):
            try:
                client = AcumaticaClient(
                    **base_client_config,
                    cache_methods=True,
                    cache_dir=temp_cache_dir,
                    force_rebuild=(thread_id == 0)  # Only first thread forces rebuild
                )
                
                models = len(client.list_models())
                services = len(client.list_services())
                
                results.put((thread_id, models, services, "success"))
                client.close()
                
            except Exception as e:
                errors.put((thread_id, str(e)))
        
        # Create multiple threads trying to access cache simultaneously
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_client, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=30)
        
        # Verify results
        assert errors.qsize() == 0, f"Should have no errors, but got: {list(errors.queue)}"
        assert results.qsize() == 5, "All threads should complete successfully"
        
        # Verify all threads got consistent results
        thread_results = list(results.queue)
        model_counts = [result[1] for result in thread_results]
        service_counts = [result[2] for result in thread_results]
        
        # All should have same counts (cache consistency)
        assert len(set(model_counts)) == 1, f"Model counts should be consistent: {model_counts}"
        assert len(set(service_counts)) == 1, f"Service counts should be consistent: {service_counts}"

    def test_cache_recovery_from_corruption(self, base_client_config, temp_cache_dir):
        """Test that client recovers gracefully from cache corruption."""
        
        # Create initial valid cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        initial_models = len(client1.list_models())
        initial_services = len(client1.list_services())
        client1.close()
        
        # Corrupt the cache file
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1, "Should have one cache file"
        
        with open(cache_files[0], 'w') as f:
            f.write("corrupted cache data - not valid pickle")
        
        # Create new client - should handle corruption gracefully
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=False  # Don't force, let it detect corruption
        )
        
        # Should recover and have same functionality
        recovered_models = len(client2.list_models())
        recovered_services = len(client2.list_services())
        
        assert recovered_models == initial_models, "Should recover all models"
        assert recovered_services == initial_services, "Should recover all services"
        
        # Cache should be working again
        stats = client2.get_performance_stats()
        assert stats['cache_enabled'] is True, "Cache should be enabled"
        
        client2.close()

    def test_cache_with_network_interruption(self, base_client_config, temp_cache_dir, live_server_url):
        """Test cache behavior when network issues occur during initialization."""
        client1 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir, force_rebuild=True)
        client1.close()

        with patch.object(AcumaticaClient, '_fetch_schema', side_effect=requests.exceptions.ConnectionError("Network error")):
            with patch.object(AcumaticaClient, '_fetch_gi_xml', side_effect=requests.exceptions.ConnectionError("Network error")):
                client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir, force_rebuild=False)
                assert len(client2.list_models()) > 0
                assert len(client2.list_services()) > 0
                client2.close()

    def test_cache_disk_space_handling(self, base_client_config, temp_cache_dir):
        """Test cache behavior when disk space is limited."""
        
        # This is a conceptual test - in practice, you'd need to simulate disk full condition
        # For now, we'll test cache file size limits
        
        client = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        # Verify cache file was created and has reasonable size
        cache_files = list(temp_cache_dir.glob("*.pkl"))
        assert len(cache_files) == 1, "Should have cache file"
        
        cache_size = cache_files[0].stat().st_size
        assert cache_size > 100, "Cache file should have substantial content"
        assert cache_size < 10 * 1024 * 1024, "Cache file shouldn't be excessively large (>10MB)"
        
        client.close()