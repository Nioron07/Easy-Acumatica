# tests/test_caching.py

import gzip
import json
import os
import time

import pytest
import requests

from easy_acumatica import AcumaticaClient


def _swagger_count(base_url: str) -> int:
    """Read the mock server's swagger.json request counter."""
    return requests.get(f"{base_url}/test/swagger-count").json()["count"]


def _schema_cache_file(client) -> "os.PathLike":
    return client._schema_cache_path()

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
    assert not hasattr(client1, "extended_test")

    # Change the schema version on the mock server
    requests.post(f"{base_client_config['base_url']}/test/schema/version", json={"version": "v2"})

    # Admin workflow: schema was changed server-side, invalidate local schema cache.
    client1.refresh_schema()

    # Second run should detect changes and rebuild affected components
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    
    # Check for new models and services from schema v2
    assert hasattr(client2.models, "ExtendedTestModel")
    assert hasattr(client2, "extended_test")
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


# --- Schema JSON disk cache tests -------------------------------------------


def test_schema_cache_file_created_on_first_fetch(base_client_config, temp_cache_dir, reset_server_state):
    """The gzipped schema file is written to cache_dir after first init."""
    client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    schema_file = _schema_cache_file(client)

    assert schema_file.exists()
    assert schema_file.parent == temp_cache_dir  # in cache_dir, not package dir
    assert schema_file.suffix == ".gz"

    # Round-trip: gzipped JSON is readable and matches what the factories consumed.
    with gzip.open(schema_file, "rt", encoding="utf-8") as f:
        data = json.load(f)
    assert "paths" in data
    assert "components" in data


def test_schema_cache_hit_skips_network(base_client_config, temp_cache_dir, reset_server_state):
    """Second init against the same cache_dir must not hit /swagger.json."""
    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    count_after_first = _swagger_count(base_client_config["base_url"])
    assert count_after_first >= 1

    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    count_after_second = _swagger_count(base_client_config["base_url"])

    assert count_after_second == count_after_first, (
        "Second init should have served the schema from disk, not the network"
    )


def test_schema_cache_ttl_expiry_refetches(base_client_config, temp_cache_dir, reset_server_state):
    """Backdating the schema file's mtime past TTL forces a network refetch."""
    client1 = AcumaticaClient(
        **base_client_config, cache_methods=True, cache_dir=temp_cache_dir,
        schema_cache_ttl_hours=1,
    )
    schema_file = _schema_cache_file(client1)
    assert schema_file.exists()
    count_after_first = _swagger_count(base_client_config["base_url"])

    # Age the file 2 hours into the past - past the 1h TTL.
    old = time.time() - 2 * 3600
    os.utime(schema_file, (old, old))

    AcumaticaClient(
        **base_client_config, cache_methods=True, cache_dir=temp_cache_dir,
        schema_cache_ttl_hours=1,
    )

    assert _swagger_count(base_client_config["base_url"]) > count_after_first


def test_refresh_schema_forces_refetch(base_client_config, temp_cache_dir, reset_server_state):
    """After refresh_schema(), the next init must hit the network."""
    client1 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    count_after_first = _swagger_count(base_client_config["base_url"])

    client1.refresh_schema()
    assert not _schema_cache_file(client1).exists()

    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)

    assert _swagger_count(base_client_config["base_url"]) > count_after_first


def test_refresh_schema_preserves_pickle(base_client_config, temp_cache_dir, reset_server_state):
    """refresh_schema() must keep the pickle so the differential cache can
    compare its hashes against the refetched schema and reuse unchanged work."""
    client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    cache_key = client._get_cache_key()
    pickle_file = temp_cache_dir / f"{cache_key}.pkl"
    schema_file = _schema_cache_file(client)
    assert pickle_file.exists() and schema_file.exists()

    client.refresh_schema()

    assert pickle_file.exists(), "pickle must remain so differential reuse works"
    assert not schema_file.exists(), "schema file must be removed"


def test_force_rebuild_bypasses_schema_cache(base_client_config, temp_cache_dir, reset_server_state):
    """force_rebuild=True must refetch the schema even when the disk file is fresh."""
    AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    count_after_first = _swagger_count(base_client_config["base_url"])

    AcumaticaClient(
        **base_client_config, cache_methods=True, cache_dir=temp_cache_dir,
        force_rebuild=True,
    )

    assert _swagger_count(base_client_config["base_url"]) > count_after_first


def test_corrupt_schema_cache_falls_back_to_network(base_client_config, temp_cache_dir, reset_server_state):
    """Garbage bytes in the schema file must not crash init - refetch instead."""
    client1 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    schema_file = _schema_cache_file(client1)
    schema_file.write_bytes(b"this is not valid gzip")
    count_after_corrupt = _swagger_count(base_client_config["base_url"])

    # Should succeed without raising; second init detects corruption and refetches.
    client2 = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)

    assert _swagger_count(base_client_config["base_url"]) > count_after_corrupt
    # File is rewritten with a valid gzip payload after the refetch.
    with gzip.open(_schema_cache_file(client2), "rt", encoding="utf-8") as f:
        json.load(f)


def test_schema_hash_differs_for_same_shape_different_content():
    """Regression: counts-only hashing collided on schemas with identical
    endpoint counts but different content. The fix hashes the full schema."""
    from easy_acumatica.client import AcumaticaClient

    # Build two schemas with IDENTICAL path and schema counts but different content.
    schema_a = {
        "info": {"title": "A"},
        "paths": {"/foo": {"get": {"operationId": "getFoo"}}},
        "components": {"schemas": {"Foo": {"type": "object"}}},
    }
    schema_b = {
        "info": {"title": "A"},  # same info
        "paths": {"/bar": {"get": {"operationId": "getBar"}}},  # different path
        "components": {"schemas": {"Foo": {"type": "object"}}},
    }

    # Bypass __init__ - _calculate_schema_hash only reads its argument.
    client = AcumaticaClient.__new__(AcumaticaClient)
    assert client._calculate_schema_hash(schema_a) != client._calculate_schema_hash(schema_b)


def test_pickle_ttl_uses_file_mtime_not_embedded_timestamp(
    base_client_config, temp_cache_dir, reset_server_state
):
    """Regression: TTL was computed from an embedded timestamp, which breaks
    if the system clock goes backward. The fix reads the file mtime."""
    client = AcumaticaClient(
        **base_client_config, cache_methods=True, cache_dir=temp_cache_dir,
        cache_ttl_hours=1,
    )
    pickle_file = temp_cache_dir / f"{client._get_cache_key()}.pkl"
    assert pickle_file.exists()

    # Tamper with the embedded timestamp to be in the FUTURE (would trick the
    # old time.time()-timestamp check into thinking the file is fresh/negative-age).
    # The mtime-based check ignores this field entirely.
    import pickle as _pickle
    with open(pickle_file, 'rb') as f:
        data = _pickle.load(f)
    data['timestamp'] = time.time() + 10 * 3600  # 10h in the future
    with open(pickle_file, 'wb') as f:
        _pickle.dump(data, f)

    # Backdate mtime past TTL - this is the ONLY signal the fixed loader trusts.
    old = time.time() - 2 * 3600
    os.utime(pickle_file, (old, old))

    loaded = client._load_differential_cache(pickle_file)
    assert loaded is None, "mtime-based TTL must invalidate despite tampered embedded timestamp"


def test_concurrent_refresh_schema_is_safe(
    base_client_config, temp_cache_dir, reset_server_state
):
    """Regression: cache I/O is now guarded by a lock. Concurrent refresh_schema
    calls from multiple threads must not raise or corrupt state."""
    import threading as _threading

    client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    errors = []

    def worker():
        try:
            for _ in range(10):
                client.refresh_schema()
        except Exception as e:
            errors.append(e)

    threads = [_threading.Thread(target=worker) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert errors == []


def test_schema_cache_readonly_fs_degrades_gracefully(
    base_client_config, temp_cache_dir, reset_server_state, monkeypatch
):
    """If the filesystem refuses writes, init still succeeds by fetching every time."""
    real_gzip_open = gzip.open

    def failing_gzip_open(path, mode="rb", *args, **kwargs):
        if "w" in mode or "a" in mode or "x" in mode:
            raise PermissionError("read-only filesystem")
        return real_gzip_open(path, mode, *args, **kwargs)

    monkeypatch.setattr("easy_acumatica.client.gzip.open", failing_gzip_open)

    # Should not raise despite the write error.
    client = AcumaticaClient(**base_client_config, cache_methods=True, cache_dir=temp_cache_dir)
    assert not _schema_cache_file(client).exists()  # no file was written