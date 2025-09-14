# tests/test_caching.py

import time
import pytest
import requests
from easy_acumatica import AcumaticaClient

def test_initial_cache_creation(base_client_config, temp_cache_dir, reset_server_state):
    """Tests that a cache file is created on the first run when caching is enabled."""
    client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    
    # Check performance stats for cache miss
    stats = client.get_performance_stats()
    assert stats['cache_misses'] == 1
    assert stats['cache_hits'] == 0
    
    # Check that a cache file was created
    cache_key = client._get_cache_key()
    cache_file = temp_cache_dir / f"{cache_key}.pkl"
    assert cache_file.exists()

def test_cache_hit_on_second_run(base_client_config, temp_cache_dir, reset_server_state):
    """Tests that the cache is used on a subsequent run."""
    # First run to create the cache
    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    
    # Second run should use the cache
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    stats2 = client2.get_performance_stats()
    
    # Assert cache hit
    assert stats2['cache_hits'] > 0
    assert stats2['cache_misses'] == 0

def test_differential_update_on_schema_change(base_client_config, temp_cache_dir, reset_server_state):
    """Tests that the cache is updated differentially when the OpenAPI schema changes."""
    # First run with schema v1
    client1 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    assert not hasattr(client1.models, "ExtendedTestModel")
    assert not hasattr(client1, "extended_tests")

    # Change the schema version on the mock server
    requests.post(f"{base_client_config['base_url']}/test/schema/version", json={"version": "v2"})

    # Second run should detect changes and rebuild affected components
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    
    # Check for new models and services from schema v2
    assert hasattr(client2.models, "ExtendedTestModel")
    assert hasattr(client2, "extended_tests")
    assert "NewField" in client2.get_model_info("TestModel")['fields']
    
    # Check stats for a partial cache miss
    stats2 = client2.get_performance_stats()
    assert stats2['cache_misses'] == 1
    assert stats2['cache_hits'] > 0  # Should have hits for unchanged components

def test_differential_update_on_inquiry_change(base_client_config, temp_cache_dir, reset_server_state):
    """Tests that the cache is updated when the Generic Inquiry XML changes."""
    # First run with XML v1
    client1 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    assert hasattr(client1.inquiries, "Inventory_Items")
    assert not hasattr(client1.inquiries, "Vendor_List")

    # Change the XML version on the mock server
    requests.post(f"{base_client_config['base_url']}/test/xml/version", json={"version": "v2"})

    # Second run should detect changes and rebuild the inquiries service
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    
    # Check for inquiry method changes from XML v2
    assert hasattr(client2.inquiries, "Vendor_List")  # New inquiry
    assert hasattr(client2.inquiries, "PM_Project_List") # New inquiry
    assert not hasattr(client2.inquiries, "IN_Inventory_Summary") # Removed inquiry

def test_force_rebuild_ignores_cache(base_client_config, temp_cache_dir, reset_server_state):
    """Tests that force_rebuild=True ignores a valid cache and rebuilds everything."""
    # First run to create a valid cache
    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)

    # Second run with force_rebuild
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir, force_rebuild=True)
    
    # Check for a cache miss, indicating a full rebuild
    stats2 = client2.get_performance_stats()
    assert stats2['cache_misses'] == 1
    assert stats2['cache_hits'] == 0