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
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30,
            'cache_methods': True,
            'force_rebuild': False
        }

    def test_schema_change_triggers_differential_update(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test that schema changes trigger proper differential updates."""
        
        # Step 1: Create initial cache with v1 schema
        client1 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        initial_models = client1.list_models()
        initial_services = client1.list_services()
        initial_stats = client1.get_performance_stats()
        
        print(f"Initial: {len(initial_models)} models, {len(initial_services)} services")
        client1.close()

        # Step 2: Change server schema to v2
        requests.post(f"{live_server_url}/test/schema/version", json={"version": "v2"})
        
        # Step 3: Create new client - should detect schema changes and update differentially
        start_time = time.time()
        client2 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir
        )
        update_time = time.time() - start_time
        
        updated_models = client2.list_models()
        updated_services = client2.list_services()
        updated_stats = client2.get_performance_stats()
        
        print(f"Updated: {len(updated_models)} models, {len(updated_services)} services")
        print(f"Update time: {update_time:.2f}s")
        
        # Verify changes were detected and handled
        assert len(updated_models) > len(initial_models), "Should have more models after schema change"
        assert len(updated_services) > len(initial_services), "Should have more services after schema change"
        
        # Verify new models exist
        assert 'ExtendedTestModel' in updated_models, "New model should be available"
        assert 'ExtendedTest' in updated_services, "New service should be available"
        
        # Verify cache statistics show differential update
        assert updated_stats['cache_hits'] > 0, "Should have some cache hits from unchanged components"
        assert updated_stats['cache_misses'] > 0, "Should have cache misses from changed components"
        
        client2.close()

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
        return {
            'base_url': live_server_url,
            'username': 'test_user',
            'password': 'test_password',
            'tenant': 'test_tenant',
            'timeout': 30,
            'cache_methods': True,
            'force_rebuild': False
        }

    def test_inquiry_xml_change_triggers_update(self, base_client_config, temp_cache_dir, live_server_url, reset_server_state):
        """Test that changes to inquiry XML trigger differential updates."""
        
        # Create initial cache with v1 XML
        client1 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        
        # Get inquiries service and verify initial inquiries
        inquiries_service = client1._service_instances.get("Inquirie")
        if inquiries_service:
            # Check that original inquiries exist
            assert hasattr(inquiries_service, 'account_details'), "Should have account_details inquiry"
            assert hasattr(inquiries_service, 'customer_list'), "Should have customer_list inquiry"
            assert hasattr(inquiries_service, 'inventory_items'), "Should have inventory_items inquiry"
            
            # Check that new inquiries don't exist yet
            assert not hasattr(inquiries_service, 'vendor_list'), "Should not have vendor_list inquiry yet"
            assert not hasattr(inquiries_service, 'pm_project_list'), "Should not have pm_project_list inquiry yet"
        
        client1.close()

        # Change XML version to add new inquiries
        requests.post(f"{live_server_url}/test/xml/version", json={"version": "v2"})
        
        # Create new client - should detect XML changes and update inquiries
        client2 = AcumaticaClient(
            **base_client_config,
            cache_dir=temp_cache_dir
        )
        
        # Verify inquiries were updated
        inquiries_service = client2._service_instances.get("Inquirie")
        if inquiries_service:
            # Original inquiries should still exist
            assert hasattr(inquiries_service, 'account_details'), "Original inquiry should still exist"
            assert hasattr(inquiries_service, 'customer_list'), "Original inquiry should still exist"
            
            # New inquiries should be added
            assert hasattr(inquiries_service, 'vendor_list'), "New inquiry should be added"
            assert hasattr(inquiries_service, 'pm_project_list'), "New inquiry should be added"
            
            # Test that new inquiry works
            vendor_result = inquiries_service.vendor_list()
            assert 'value' in vendor_result, "New inquiry should return data"
        
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
        
        # Create initial cache
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        client1.close()
        
        # Simulate network interruption by using invalid URL
        with patch.object(AcumaticaClient, '_fetch_schema') as mock_fetch:
            mock_fetch.side_effect = requests.exceptions.ConnectionError("Network error")
            
            # Client should fall back to cache when schema fetch fails
            client2 = AcumaticaClient(
                **base_client_config,
                cache_methods=True,
                cache_dir=temp_cache_dir,
                force_rebuild=False
            )
            
            # Should still have models and services from cache
            assert len(client2.list_models()) > 0, "Should have models from cache"
            assert len(client2.list_services()) > 0, "Should have services from cache"
            
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


class TestCachePerformanceOptimization:
    """Test cache performance optimizations and measurements."""
    
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

    def test_cache_vs_no_cache_performance(self, base_client_config, temp_cache_dir):
        """Comprehensive performance comparison between cached and non-cached clients."""
        
        results = {}
        
        # Test 1: No cache (baseline)
        times = []
        for i in range(3):
            start_time = time.time()
            client = AcumaticaClient(
                **base_client_config,
                cache_methods=False
            )
            elapsed = time.time() - start_time
            times.append(elapsed)
            client.close()
        
        results['no_cache'] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
        
        # Test 2: Cache enabled - first run (cold)
        start_time = time.time()
        client_cold = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        cold_time = time.time() - start_time
        client_cold.close()
        
        results['cache_cold'] = {
            'avg_time': cold_time,
            'min_time': cold_time,
            'max_time': cold_time
        }
        
        # Test 3: Cache enabled - warm runs
        times = []
        for i in range(3):
            start_time = time.time()
            client = AcumaticaClient(
                **base_client_config,
                cache_methods=True,
                cache_dir=temp_cache_dir,
                force_rebuild=False
            )
            elapsed = time.time() - start_time
            times.append(elapsed)
            
            # Verify cache is working
            stats = client.get_performance_stats()
            assert stats['cache_hits'] > 0, f"Run {i+1} should have cache hits"
            
            client.close()
        
        results['cache_warm'] = {
            'avg_time': sum(times) / len(times),
            'min_time': min(times),
            'max_time': max(times)
        }
        
        # Performance assertions
        print(f"\nPerformance Results:")
        print(f"No cache average: {results['no_cache']['avg_time']:.2f}s")
        print(f"Cache cold: {results['cache_cold']['avg_time']:.2f}s")  
        print(f"Cache warm average: {results['cache_warm']['avg_time']:.2f}s")
        
        # Warm cache should be significantly faster than no cache
        speedup_factor = results['no_cache']['avg_time'] / results['cache_warm']['avg_time']
        print(f"Speedup factor: {speedup_factor:.1f}x")
        
        assert speedup_factor > 1.1, f"Cache should provide at least 1.1x speedup, got {speedup_factor:.1f}x"
        
        # Warm cache should be faster than cold cache
        assert results['cache_warm']['avg_time'] < results['cache_cold']['avg_time'], \
            "Warm cache should be faster than cold cache"

    def test_differential_vs_full_rebuild_performance(self, base_client_config, temp_cache_dir, live_server_url):
        """Test performance difference between differential updates and full rebuilds."""
        
        # Create initial cache
        start_time = time.time()
        client1 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True
        )
        initial_build_time = time.time() - start_time
        client1.close()
        
        # Change schema slightly
        requests.post(f"{live_server_url}/test/schema/version", json={"version": "v2"})
        
        # Test differential update
        start_time = time.time()
        client2 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=False  # Should do differential update
        )
        differential_time = time.time() - start_time
        client2.close()
        
        # Test full rebuild for comparison
        start_time = time.time()
        client3 = AcumaticaClient(
            **base_client_config,
            cache_methods=True,
            cache_dir=temp_cache_dir,
            force_rebuild=True  # Force full rebuild
        )
        full_rebuild_time = time.time() - start_time
        client3.close()
        
        print(f"\nRebuild Performance:")
        print(f"Initial build: {initial_build_time:.2f}s")
        print(f"Differential update: {differential_time:.2f}s")
        print(f"Full rebuild: {full_rebuild_time:.2f}s")
        
        # Differential update should be faster than full rebuild
        # (though this might not always be true for small schemas)
        improvement_ratio = full_rebuild_time / differential_time
        print(f"Differential improvement: {improvement_ratio:.1f}x")
        
        # At minimum, differential shouldn't be significantly slower
        assert differential_time <= full_rebuild_time * 1.5, \
            "Differential update shouldn't be much slower than full rebuild"