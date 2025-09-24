# tests/test_exceptions.py
"""Comprehensive tests for the exception system."""

import pytest
from unittest.mock import Mock, patch
import requests
import json
from datetime import datetime, timezone

from easy_acumatica import (
    AcumaticaClient,
    AcumaticaError,
    AcumaticaAuthError,
    AcumaticaConnectionError,
    AcumaticaNotFoundError,
    AcumaticaValidationError,
    AcumaticaBusinessRuleError,
    AcumaticaConcurrencyError,
    AcumaticaServerError,
    AcumaticaTimeoutError,
    AcumaticaRateLimitError,
    AcumaticaConfigError,
    AcumaticaSchemaError,
    AcumaticaBatchError,
    AcumaticaRetryExhaustedError,
    ErrorCode
)
from easy_acumatica.exceptions import parse_api_error, enhance_exception_with_request_context


class TestExceptionHierarchy:
    """Test the exception class hierarchy and basic functionality."""

    def test_base_exception_with_full_context(self):
        """Test AcumaticaError with all context fields."""
        error = AcumaticaError(
            message="Test error",
            error_code=ErrorCode.BAD_REQUEST,
            status_code=400,
            operation="test_operation",
            entity="Customer",
            entity_id="CUST001",
            request_data={"field": "value"},
            response_data={"error": "details"},
            suggestions=["Try this", "Or that"]
        )

        assert error.message == "Test error"
        assert error.error_code == ErrorCode.BAD_REQUEST
        assert error.status_code == 400
        assert error.operation == "test_operation"
        assert error.entity == "Customer"
        assert error.entity_id == "CUST001"
        assert error.request_data == {"field": "value"}
        assert error.response_data == {"error": "details"}
        assert len(error.suggestions) == 2
        assert isinstance(error.timestamp, datetime)

        # Test string representation
        str_repr = str(error)
        assert "[400]" in str_repr
        assert "Test error" in str_repr

        # Test detailed message
        detailed = error.get_detailed_message()
        assert "Test error" in detailed
        assert "Error Code: 400" in detailed
        assert "Operation: test_operation" in detailed
        assert "Entity: Customer (ID: CUST001)" in detailed
        assert "Try this" in detailed

    def test_auth_error_suggestions(self):
        """Test that AcumaticaAuthError includes authentication suggestions."""
        error = AcumaticaAuthError("Invalid credentials", status_code=401)

        assert error.status_code == 401
        assert any("username and password" in s for s in error.suggestions)
        assert any("session has expired" in s for s in error.suggestions)
        assert any("tenant name" in s for s in error.suggestions)

    def test_not_found_error_auto_message(self):
        """Test AcumaticaNotFoundError auto-generates message."""
        error = AcumaticaNotFoundError(
            "",  # Empty message
            resource_type="SalesOrder",
            resource_id="SO001"
        )

        assert error.message == "SalesOrder with ID 'SO001' was not found"
        assert error.status_code == 404
        assert error.error_code == ErrorCode.NOT_FOUND

    def test_validation_error_with_field_errors(self):
        """Test AcumaticaValidationError with field-level errors."""
        field_errors = {
            "CustomerID": "Customer does not exist",
            "Amount": ["Must be positive", "Exceeds credit limit"]
        }

        error = AcumaticaValidationError(
            "",  # Auto-generate from field errors
            field_errors=field_errors
        )

        assert "CustomerID: Customer does not exist" in error.message
        assert "Amount: Must be positive" in error.message
        assert "Amount: Exceeds credit limit" in error.message
        assert error.error_code == ErrorCode.VALIDATION_ERROR

    def test_server_error_default_message(self):
        """Test AcumaticaServerError with default message."""
        error = AcumaticaServerError(status_code=500)

        assert "Server error (500)" in error.message
        assert error.error_code == ErrorCode.INTERNAL_SERVER_ERROR
        assert any("temporary issue" in s for s in error.suggestions)

        # Test 503 specific suggestion
        error_503 = AcumaticaServerError(status_code=503)
        assert error_503.suggestions[0] == "The service may be under maintenance or overloaded"

    def test_rate_limit_error_with_retry_after(self):
        """Test AcumaticaRateLimitError with retry_after."""
        error = AcumaticaRateLimitError(retry_after=60)

        assert "Rate limit exceeded. Retry after 60 seconds" in error.message
        assert error.retry_after == 60
        assert error.status_code == 429
        assert any("Wait 60 seconds" in s for s in error.suggestions)

    def test_batch_error_with_failed_operations(self):
        """Test AcumaticaBatchError with operation details."""
        failed_ops = [
            {"index": 0, "error": "Not found"},
            {"index": 2, "error": "Validation failed"}
        ]

        error = AcumaticaBatchError("", failed_operations=failed_ops)

        assert "2 operations failed" in error.message
        assert len(error.failed_operations) == 2
        assert error.error_code == ErrorCode.BATCH_EXECUTION_FAILED


class TestErrorParsing:
    """Test the parse_api_error function with various response formats."""

    def test_parse_401_unauthorized(self):
        """Test parsing 401 authentication error."""
        response_data = {"message": "Invalid credentials"}
        error = parse_api_error(response_data, 401, operation="login", entity="Auth")

        assert isinstance(error, AcumaticaAuthError)
        assert error.status_code == 401
        assert error.message == "Invalid credentials"
        assert error.operation == "login"

    def test_parse_401_session_expired(self):
        """Test parsing 401 with session expiration."""
        response_data = {"message": "Your session has expired"}
        error = parse_api_error(response_data, 401)

        assert isinstance(error, AcumaticaAuthError)
        assert error.error_code == ErrorCode.SESSION_EXPIRED

    def test_parse_404_not_found(self):
        """Test parsing 404 not found error."""
        response_data = {"message": "Record not found"}
        error = parse_api_error(
            response_data, 404,
            entity="Customer",
            entity_id="CUST999"
        )

        assert isinstance(error, AcumaticaNotFoundError)
        assert error.status_code == 404
        assert error.entity == "Customer"
        assert error.entity_id == "CUST999"

    def test_parse_412_concurrency(self):
        """Test parsing 412 concurrency conflict."""
        response_data = {"message": "Record has been modified"}
        error = parse_api_error(response_data, 412)

        assert isinstance(error, AcumaticaConcurrencyError)
        assert error.status_code == 412

    def test_parse_422_validation(self):
        """Test parsing 422 validation error with field errors."""
        response_data = {
            "message": "Validation failed",
            "fieldErrors": {
                "Email": "Invalid email format",
                "Phone": "Required field"
            }
        }
        error = parse_api_error(response_data, 422)

        assert isinstance(error, AcumaticaValidationError)
        assert error.field_errors["Email"] == "Invalid email format"
        assert error.field_errors["Phone"] == "Required field"

    def test_parse_422_business_rule(self):
        """Test parsing 422 business rule violation."""
        response_data = {"message": "Cannot delete customer with open orders"}
        error = parse_api_error(response_data, 422)

        assert isinstance(error, AcumaticaBusinessRuleError)
        assert error.status_code == 422

    def test_parse_429_rate_limit(self):
        """Test parsing 429 rate limit error."""
        response_data = {
            "message": "Too many requests",
            "retryAfter": 30
        }
        error = parse_api_error(response_data, 429)

        assert isinstance(error, AcumaticaRateLimitError)
        assert error.retry_after == 30

    def test_parse_500_server_error(self):
        """Test parsing 500 internal server error."""
        response_data = {"message": "Internal server error occurred"}
        error = parse_api_error(response_data, 500)

        assert isinstance(error, AcumaticaServerError)
        assert error.status_code == 500

    def test_parse_string_response(self):
        """Test parsing when response is a string."""
        error = parse_api_error("Something went wrong", 400)

        assert isinstance(error, AcumaticaError)
        assert error.message == "Something went wrong"

    def test_parse_various_message_formats(self):
        """Test parsing different message field formats."""
        # Test exceptionMessage
        error = parse_api_error({"exceptionMessage": "Test 1"}, 400)
        assert error.message == "Test 1"

        # Test Message (capitalized)
        error = parse_api_error({"Message": "Test 2"}, 400)
        assert error.message == "Test 2"

        # Test nested error.message
        error = parse_api_error({"error": {"message": "Test 3"}}, 400)
        assert error.message == "Test 3"

        # Test error as string
        error = parse_api_error({"error": "Test 4"}, 400)
        assert error.message == "Test 4"

    def test_parse_with_full_context(self):
        """Test parsing with complete context information."""
        response_data = {"message": "Test error"}
        error = parse_api_error(
            response_data,
            400,
            operation="put_entity",
            entity="Customer",
            entity_id="CUST001",
            request_data={"Name": "Test Customer"}
        )

        assert error.operation == "put_entity"
        assert error.entity == "Customer"
        assert error.entity_id == "CUST001"
        assert error.request_data == {"Name": "Test Customer"}


class TestExceptionEnhancement:
    """Test the enhance_exception_with_request_context function."""

    def test_enhance_acumatica_exception(self):
        """Test enhancing an existing AcumaticaError with request context."""
        original = AcumaticaError("Original error", status_code=400)
        enhanced = enhance_exception_with_request_context(
            original,
            method="POST",
            url="https://api.example.com/entity/Customer",
            headers={"Authorization": "Bearer token", "Content-Type": "application/json"},
            params={"$filter": "Status eq 'Active'"},
            json_data={"Name": "Test"}
        )

        assert enhanced is original  # Should be the same object
        assert enhanced.context["http_method"] == "POST"
        assert enhanced.context["url"] == "https://api.example.com/entity/Customer"
        assert enhanced.context["params"] == {"$filter": "Status eq 'Active'"}
        assert "authorization" not in enhanced.context["request_headers"]  # Should be redacted
        assert enhanced.request_data == {"Name": "Test"}

    def test_enhance_timeout_error(self):
        """Test converting TimeoutError to AcumaticaTimeoutError."""
        original = TimeoutError("Request timed out")
        enhanced = enhance_exception_with_request_context(
            original,
            method="GET",
            url="https://api.example.com/entity/Customer/123"
        )

        assert isinstance(enhanced, AcumaticaTimeoutError)
        assert "Request timed out" in enhanced.message
        assert enhanced.operation == "GET https://api.example.com/entity/Customer/123"

    def test_enhance_connection_error(self):
        """Test converting ConnectionError to AcumaticaConnectionError."""
        original = ConnectionError("Connection failed")
        enhanced = enhance_exception_with_request_context(
            original,
            method="PUT",
            url="https://api.example.com/entity/Customer"
        )

        assert isinstance(enhanced, AcumaticaConnectionError)
        assert "Connection failed" in enhanced.message

    def test_enhance_generic_exception(self):
        """Test converting generic exception to AcumaticaError."""
        original = ValueError("Invalid value")
        enhanced = enhance_exception_with_request_context(
            original,
            method="DELETE",
            url="https://api.example.com/entity/Customer/123"
        )

        assert isinstance(enhanced, AcumaticaError)
        assert "Invalid value" in enhanced.message
        assert enhanced.context["original_error"] == "ValueError"


class TestIntegrationScenarios:
    """Test exception handling in integration scenarios."""

    @patch('easy_acumatica.client.requests.Session.get')
    def test_connection_error(self, mock_get):
        """Test handling of connection errors."""
        mock_get.side_effect = requests.exceptions.ConnectionError("Failed to connect")

        with pytest.raises(AcumaticaError) as exc_info:
            AcumaticaClient(
                base_url="https://invalid-url.com",
                username="test",
                password="test",
                tenant="test"
            )

        # Check for either connection error or failed to fetch endpoint error
        error_str = str(exc_info.value)
        assert ("Failed to fetch endpoint" in error_str or "Connection" in error_str)

    @patch('easy_acumatica.client.requests.Session')
    def test_auth_error_on_login(self, mock_session):
        """Test handling of authentication errors during login."""
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.json.return_value = {"message": "Invalid credentials"}
        mock_response.raise_for_status.side_effect = requests.HTTPError()

        mock_sess_instance = mock_session.return_value
        mock_sess_instance.post.return_value = mock_response
        mock_sess_instance.get.return_value = mock_response  # Mock get endpoints too

        with pytest.raises(AcumaticaError) as exc_info:
            AcumaticaClient(
                base_url="https://test.com",
                username="invalid",
                password="invalid",
                tenant="test"
            )

        assert "Invalid credentials" in str(exc_info.value)

    def test_config_error_empty_password(self):
        """Test configuration error for empty password."""
        from easy_acumatica.config import AcumaticaConfig

        # AcumaticaConfig requires all parameters, test with empty password
        config = AcumaticaConfig(
            base_url="https://test.com",
            username="test",
            password="",  # Empty password should raise error
            tenant="test"
        )

        with pytest.raises(AcumaticaConfigError) as exc_info:
            config.validate()

        assert "password is required" in str(exc_info.value)

    def test_validation_error_in_utils(self):
        """Test validation errors from utility functions."""
        from easy_acumatica.utils import validate_entity_id

        with pytest.raises(AcumaticaValidationError) as exc_info:
            validate_entity_id("")

        assert "Entity ID cannot be empty" in str(exc_info.value)
        assert "entity_id" in exc_info.value.field_errors


class TestErrorCodeEnum:
    """Test the ErrorCode enum."""

    def test_error_code_values(self):
        """Test that ErrorCode enum has expected values."""
        assert ErrorCode.UNAUTHORIZED.value == "401"
        assert ErrorCode.NOT_FOUND.value == "404"
        assert ErrorCode.INTERNAL_SERVER_ERROR.value == "500"
        assert ErrorCode.VALIDATION_ERROR.value == "VALIDATION"
        assert ErrorCode.BATCH_EXECUTION_FAILED.value == "BATCH_FAILED"

    def test_error_code_in_exception(self):
        """Test using ErrorCode enum in exceptions."""
        error = AcumaticaError("Test", error_code=ErrorCode.BAD_REQUEST)
        assert error.error_code == ErrorCode.BAD_REQUEST

        # Test string representation
        detailed = error.get_detailed_message()
        assert "Error Code: 400" in detailed