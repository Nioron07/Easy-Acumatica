# tests/test_error_handling.py
"""Tests for error handling scenarios."""

import pytest
from unittest.mock import Mock, patch
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.exceptions import AcumaticaError, AcumaticaAuthError


class TestErrorHandling:
    """Test error handling in various scenarios."""
    
    def test_connection_error(self):
        """Test handling of connection errors."""
        # The enhanced client wraps connection errors in AcumaticaAuthError
        with pytest.raises(AcumaticaAuthError) as exc_info:
            client = AcumaticaClient(
                base_url="https://invalid-url-that-does-not-exist.com",
                username="test",
                password="test",
                tenant="test"
            )
        
        # Check that the error message mentions the connection issue
        assert "404" in str(exc_info.value) or "Not Found" in str(exc_info.value)
    
    @patch('easy_acumatica.client.requests.Session')
    def test_auth_error(self, mock_session):
        """Test handling of authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid credentials"}
        mock_response.raise_for_status.side_effect = requests.HTTPError()
        
        mock_session.return_value.post.return_value = mock_response
        
        with pytest.raises(AcumaticaError, match="Invalid credentials"):
            client = AcumaticaClient(
                base_url="https://test.com",
                username="invalid",
                password="invalid",
                tenant="test"
            )
    
    def test_malformed_schema(self, live_server_url):
        """Test handling of malformed API schema."""
        # This would require modifying the mock server to return bad data
        # Implementation depends on specific error scenarios to test
        pass