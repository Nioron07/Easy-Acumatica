
# tests/test_utils.py
"""Tests for utility functions."""

import pytest
import time
from unittest.mock import Mock, patch
import requests

from easy_acumatica.utils import retry_on_error, RateLimiter, validate_entity_id
from easy_acumatica.exceptions import AcumaticaError


class TestRetryDecorator:
    """Test the retry_on_error decorator."""
    
    def test_successful_call_no_retry(self):
        """Test that successful calls don't trigger retries."""
        mock_func = Mock(return_value="success")
        decorated = retry_on_error(max_attempts=3)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 1
    
    def test_retry_on_exception(self):
        """Test that function retries on specified exceptions."""
        mock_func = Mock(side_effect=[requests.RequestException(), "success"])
        decorated = retry_on_error(max_attempts=3, delay=0.01)(mock_func)
        
        result = decorated()
        
        assert result == "success"
        assert mock_func.call_count == 2
    
    def test_max_retries_exceeded(self):
        """Test that exception is raised after max retries."""
        mock_func = Mock(side_effect=requests.RequestException())
        decorated = retry_on_error(max_attempts=3, delay=0.01)(mock_func)
        
        with pytest.raises(requests.RequestException):
            decorated()
        
        assert mock_func.call_count == 3


class TestRateLimiter:
    """Test the RateLimiter class."""
    
    def test_rate_limiting(self):
        """Test that rate limiter enforces call intervals."""
        # Create a limiter with no burst capacity to force delays
        limiter = RateLimiter(calls_per_second=10.0, burst_size=1)
        mock_func = Mock(return_value="result")
        decorated = limiter(mock_func)
        
        start_time = time.time()
        
        # Make 3 rapid calls - the first is free, next 2 should be delayed
        for _ in range(3):
            decorated()
        
        elapsed_time = time.time() - start_time
        
        # At 10 calls/sec with burst_size=1, we expect:
        # - First call: immediate (uses the 1 token)
        # - Second call: waits ~0.1s (to accumulate 1 token)
        # - Third call: waits ~0.1s (to accumulate 1 token)
        # Total: ~0.2s
        assert elapsed_time >= 0.15, f"Expected at least 0.15s, but got {elapsed_time:.3f}s"
        assert mock_func.call_count == 3


class TestValidateEntityId:
    """Test the validate_entity_id function."""
    
    def test_single_id(self):
        """Test validation of single entity ID."""
        assert validate_entity_id("123") == "123"
    
    def test_list_of_ids(self):
        """Test validation of multiple entity IDs."""
        assert validate_entity_id(["123", "456", "789"]) == "123,456,789"
    
    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Entity ID cannot be empty"):
            validate_entity_id("")
    
    def test_empty_list_raises_error(self):
        """Test that empty list raises ValueError."""
        with pytest.raises(ValueError, match="Entity ID list cannot be empty"):
            validate_entity_id([])
    
    def test_invalid_type_raises_error(self):
        """Test that invalid type raises TypeError."""
        with pytest.raises(TypeError):
            validate_entity_id(123)