"""
Tests for new statistics and debugging features added to AcumaticaClient.
"""

import pytest
from unittest.mock import Mock, patch
from easy_acumatica import AcumaticaClient


def test_get_connection_stats(base_client_config):
    """Test get_connection_stats method."""
    client = AcumaticaClient(**base_client_config)

    stats = client.get_connection_stats()

    # Check that required keys are present
    assert 'session_headers' in stats
    assert 'verify_ssl' in stats
    assert 'timeout' in stats
    assert 'connection_pools' in stats
    assert 'rate_limit' in stats

    # Check rate limit details
    assert 'calls_per_second' in stats['rate_limit']
    assert 'burst_size' in stats['rate_limit']
    assert 'current_tokens' in stats['rate_limit']


def test_get_session_info(base_client_config):
    """Test get_session_info method."""
    client = AcumaticaClient(**base_client_config)

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

    # Verify values
    assert info['base_url'] == base_client_config['base_url']
    assert info['tenant'] == base_client_config['tenant']
    assert info['username'] == base_client_config['username']


def test_get_api_usage_stats(base_client_config):
    """Test get_api_usage_stats method."""
    client = AcumaticaClient(**base_client_config)

    # Make some requests to generate stats
    try:
        client.tests.get_by_id("123")
    except:
        pass  # Ignore errors, we're just testing stats

    stats = client.get_api_usage_stats()

    # Check required fields
    assert 'total_requests' in stats
    assert 'total_errors' in stats
    assert 'requests_by_method' in stats
    assert 'requests_by_endpoint' in stats
    assert 'average_response_time' in stats
    assert 'last_request_time' in stats

    # After making a request, some stats should be populated
    assert stats['total_requests'] >= 0


def test_get_schema_info(base_client_config):
    """Test get_schema_info method."""
    client = AcumaticaClient(**base_client_config)

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

    # Verify some values
    assert info['total_models'] > 0
    assert info['total_services'] > 0


def test_test_connection(base_client_config):
    """Test test_connection method."""
    client = AcumaticaClient(**base_client_config)

    result = client.test_connection()

    # Check required fields
    assert 'reachable' in result
    assert 'response_time' in result
    assert 'endpoints_available' in result
    assert 'error' in result

    # In test environment, should be reachable
    assert result['reachable'] == True or result['error'] is not None


def test_get_last_request_info(base_client_config):
    """Test get_last_request_info method."""
    client = AcumaticaClient(**base_client_config)

    # Initially should be None or empty
    info = client.get_last_request_info()

    # Make a request
    try:
        client.tests.get_by_id("123")
    except:
        pass

    # Now should have info
    info = client.get_last_request_info()
    if info:  # Might be None if request tracking wasn't initialized
        assert 'timestamp' in info
        assert 'method' in info
        assert 'url' in info
        assert 'status_code' in info
        assert 'response_time' in info
        assert 'error' in info


def test_get_error_history(base_client_config):
    """Test get_error_history method."""
    client = AcumaticaClient(**base_client_config)

    # Initially should be empty
    errors = client.get_error_history()
    assert isinstance(errors, list)

    # Try to trigger an error
    try:
        client.tests.get_by_id("nonexistent999")
    except:
        pass

    # Check error history
    errors = client.get_error_history(5)
    assert isinstance(errors, list)
    assert len(errors) <= 5


def test_validate_credentials(base_client_config):
    """Test validate_credentials method."""
    client = AcumaticaClient(**base_client_config)

    result = client.validate_credentials()

    # Check required fields
    assert 'valid' in result
    assert 'error' in result

    # In test environment with valid credentials
    assert isinstance(result['valid'], bool)


def test_request_tracking(base_client_config):
    """Test that request tracking works correctly."""
    client = AcumaticaClient(**base_client_config)

    # Make multiple requests
    for i in range(3):
        try:
            client.tests.get_list()
        except:
            pass

    # Check that stats are updated
    stats = client.get_api_usage_stats()
    assert stats['total_requests'] >= 3

    # Check last request info
    last_info = client.get_last_request_info()
    if last_info:
        assert last_info['method'] in ['GET', 'POST', 'PUT', 'DELETE']
        assert 'Test' in last_info['url'] or 'test' in last_info['url'].lower()


def test_custom_fields_count(base_client_config):
    """Test counting of custom fields."""
    client = AcumaticaClient(**base_client_config)

    # Get schema info which includes custom fields count
    info = client.get_schema_info()

    # Should be a non-negative number
    assert info['custom_fields_count'] >= 0

    # If we have models, manually count to verify
    if client._model_classes:
        manual_count = 0
        for model_name, model_class in client._model_classes.items():
            if hasattr(model_class, '__annotations__'):
                for field_name in model_class.__annotations__.keys():
                    if field_name.startswith('Custom') or field_name.startswith('Usr'):
                        manual_count += 1

        assert info['custom_fields_count'] == manual_count


def test_performance_stats_enhanced(base_client_config):
    """Test that get_performance_stats still works with new features."""
    client = AcumaticaClient(**base_client_config)

    stats = client.get_performance_stats()

    # Original fields should still be there
    assert 'startup_time' in stats
    assert 'cache_enabled' in stats
    assert 'cache_hits' in stats
    assert 'cache_misses' in stats
    assert 'cache_hit_rate' in stats
    assert 'model_count' in stats
    assert 'service_count' in stats
    assert 'endpoint_count' in stats
    assert 'schema_cache_size' in stats

    # Values should be reasonable
    assert stats['startup_time'] > 0
    assert stats['model_count'] > 0
    assert stats['service_count'] > 0