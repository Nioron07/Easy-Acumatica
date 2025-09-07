# tests/test_error_handling.py
"""Tests for error handling scenarios."""

import pytest
from unittest.mock import Mock, patch
import requests

from easy_acumatica import AcumaticaClient
from easy_acumatica.exceptions import AcumaticaError, AcumaticaAuthError, AcumaticaConnectionError


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_connection_error(self):
        """Test handling of connection errors."""
        # CORRECTED: The client initialization should raise a ConnectionError subtype
        with pytest.raises(AcumaticaConnectionError):
            AcumaticaClient(
                base_url="https://invalid-url-that-does-not-exist.com",
                username="test",
                password="test",
                tenant="test"
            )

    @patch('easy_acumatica.client.requests.Session')
    def test_auth_error(self, mock_session):
        """Test handling of authentication errors."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid credentials"}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        # Mock the entire session behavior for login
        mock_sess_instance = mock_session.return_value
        mock_sess_instance.post.return_value = mock_response

        with pytest.raises(AcumaticaAuthError, match="Invalid credentials"):
            AcumaticaClient(
                base_url="https://test.com",
                username="invalid",
                password="invalid",
                tenant="test"
            )