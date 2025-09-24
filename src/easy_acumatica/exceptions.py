# easy_acumatica.exceptions
"""
Comprehensive exception system for Easy-Acumatica.

This module provides detailed, actionable exceptions with rich context
to help developers quickly identify and fix issues.
"""

import json
import logging
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standard error codes based on Acumatica API responses."""
    # Authentication & Authorization
    UNAUTHORIZED = "401"
    FORBIDDEN = "403"
    SESSION_EXPIRED = "401_SESSION"
    INVALID_CREDENTIALS = "401_CREDENTIALS"

    # Client Errors
    BAD_REQUEST = "400"
    NOT_FOUND = "404"
    PRECONDITION_FAILED = "412"
    UNPROCESSABLE_ENTITY = "422"
    RATE_LIMIT_EXCEEDED = "429"

    # Server Errors
    INTERNAL_SERVER_ERROR = "500"
    BAD_GATEWAY = "502"
    SERVICE_UNAVAILABLE = "503"
    GATEWAY_TIMEOUT = "504"

    # Business Logic Errors
    VALIDATION_ERROR = "VALIDATION"
    BUSINESS_RULE_VIOLATION = "BUSINESS_RULE"
    CONCURRENCY_CONFLICT = "CONCURRENCY"
    DUPLICATE_RECORD = "DUPLICATE"

    # Connection Errors
    CONNECTION_ERROR = "CONNECTION"
    TIMEOUT = "TIMEOUT"
    DNS_ERROR = "DNS"
    SSL_ERROR = "SSL"

    # Configuration Errors
    CONFIG_MISSING = "CONFIG_MISSING"
    CONFIG_INVALID = "CONFIG_INVALID"
    ENDPOINT_NOT_FOUND = "ENDPOINT_NOT_FOUND"
    SCHEMA_ERROR = "SCHEMA_ERROR"

    # Operation Errors
    OPERATION_NOT_SUPPORTED = "OPERATION_NOT_SUPPORTED"
    BATCH_EXECUTION_FAILED = "BATCH_FAILED"
    RETRY_EXHAUSTED = "RETRY_EXHAUSTED"


class AcumaticaError(Exception):
    """
    Enhanced base exception for all Acumatica-related errors.

    Provides rich context including:
    - Error code and HTTP status
    - Detailed message with suggestions
    - Request/response data
    - Timestamp and operation context
    """

    def __init__(
        self,
        message: str,
        error_code: Optional[Union[ErrorCode, str]] = None,
        status_code: Optional[int] = None,
        operation: Optional[str] = None,
        entity: Optional[str] = None,
        entity_id: Optional[str] = None,
        request_data: Optional[Dict[str, Any]] = None,
        response_data: Optional[Dict[str, Any]] = None,
        suggestions: Optional[List[str]] = None,
        **kwargs
    ):
        """
        Initialize AcumaticaError with rich context.

        Args:
            message: Primary error message
            error_code: ErrorCode enum or string code
            status_code: HTTP status code
            operation: Operation being performed (e.g., "get_by_id", "put_entity")
            entity: Entity type involved (e.g., "Customer", "SalesOrder")
            entity_id: Specific entity ID if applicable
            request_data: Data sent in request
            response_data: Raw response from API
            suggestions: List of suggestions for fixing the error
            **kwargs: Additional context data
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code if isinstance(error_code, ErrorCode) else ErrorCode(error_code) if error_code else None
        self.status_code = status_code
        self.operation = operation
        self.entity = entity
        self.entity_id = entity_id
        self.request_data = request_data
        self.response_data = response_data
        self.suggestions = suggestions or []
        self.timestamp = datetime.now(timezone.utc)
        self.context = kwargs

        # Log the error with context
        logger.error(self.get_detailed_message())

    def get_detailed_message(self) -> str:
        """Get a detailed, formatted error message."""
        parts = [f"[{self.timestamp.isoformat()}Z] {self.message}"]

        if self.error_code:
            parts.append(f"Error Code: {self.error_code.value if isinstance(self.error_code, ErrorCode) else self.error_code}")

        if self.status_code:
            parts.append(f"HTTP Status: {self.status_code}")

        if self.operation:
            parts.append(f"Operation: {self.operation}")

        if self.entity:
            entity_info = f"Entity: {self.entity}"
            if self.entity_id:
                entity_info += f" (ID: {self.entity_id})"
            parts.append(entity_info)

        if self.suggestions:
            parts.append("\nSuggestions:")
            for i, suggestion in enumerate(self.suggestions, 1):
                parts.append(f"  {i}. {suggestion}")

        if self.response_data:
            # Extract meaningful error details from response
            api_message = self._extract_api_message(self.response_data)
            if api_message and api_message != self.message:
                parts.append(f"\nAPI Response: {api_message}")

        if self.context:
            parts.append(f"\nAdditional Context: {self.context}")

        return "\n".join(parts)

    def _extract_api_message(self, response_data: Dict[str, Any]) -> Optional[str]:
        """Extract meaningful message from API response."""
        # Try common error message locations
        for path in [
            "exceptionMessage",
            "message",
            "error.message",
            "error",
            "Message",
            "ExceptionMessage",
            "innererror.message"
        ]:
            msg = self._get_nested_value(response_data, path)
            if msg:
                return str(msg)
        return None

    def _get_nested_value(self, data: Dict, path: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        keys = path.split('.')
        current = data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current

    def __str__(self) -> str:
        """String representation with key details."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        elif self.error_code:
            code_val = self.error_code.value if isinstance(self.error_code, ErrorCode) else self.error_code
            return f"[{code_val}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        """Developer-friendly representation."""
        return f"AcumaticaError(message={self.message!r}, error_code={self.error_code}, status_code={self.status_code})"


class AcumaticaAuthError(AcumaticaError):
    """Authentication and authorization errors (401, 403)."""

    def __init__(self, message: str, **kwargs):
        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Verify your username and password are correct",
            "Check if your session has expired and try logging in again",
            "Ensure your user has the necessary permissions",
            "Verify the tenant name is correct"
        ])
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaNotFoundError(AcumaticaError):
    """Resource not found errors (404)."""

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        self.resource_type = resource_type or kwargs.get('entity')
        self.resource_id = resource_id or kwargs.get('entity_id')

        if not message and self.resource_type and self.resource_id:
            message = f"{self.resource_type} with ID '{self.resource_id}' was not found"
        elif not message and self.resource_type:
            message = f"{self.resource_type} not found"

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            f"Verify the {self.resource_type or 'resource'} ID is correct",
            "Check if the record exists in Acumatica",
            "Ensure you're using the correct endpoint version",
            "Verify the entity name is spelled correctly"
        ])

        kwargs['status_code'] = 404
        kwargs['error_code'] = ErrorCode.NOT_FOUND
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaValidationError(AcumaticaError):
    """Data validation errors (400, 422)."""

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, Union[str, List[str]]]] = None,
        **kwargs
    ):
        self.field_errors = field_errors or {}

        # Build detailed message from field errors
        if self.field_errors and not message:
            error_parts = []
            for field, errors in self.field_errors.items():
                if isinstance(errors, list):
                    for error in errors:
                        error_parts.append(f"{field}: {error}")
                else:
                    error_parts.append(f"{field}: {errors}")
            message = "Validation failed:\n" + "\n".join(error_parts)

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Check that all required fields are provided",
            "Verify field values match expected formats",
            "Ensure numeric fields contain valid numbers",
            "Check date formats (should be ISO 8601)",
            "Verify reference fields point to existing records"
        ])

        if self.field_errors:
            for field in self.field_errors:
                suggestions.append(f"Review the value for field: {field}")

        kwargs['error_code'] = ErrorCode.VALIDATION_ERROR
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaBusinessRuleError(AcumaticaError):
    """Business rule violations (422)."""

    def __init__(self, message: str, rule: Optional[str] = None, **kwargs):
        self.rule = rule

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Review the business rules for this operation",
            "Check if the operation is allowed in the current document state",
            "Verify all prerequisites are met",
            "Ensure the operation sequence is correct"
        ])

        kwargs['status_code'] = 422
        kwargs['error_code'] = ErrorCode.BUSINESS_RULE_VIOLATION
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaConcurrencyError(AcumaticaError):
    """Concurrency conflicts (412)."""

    def __init__(self, message: str = None, **kwargs):
        if not message:
            message = "The record was modified by another user. Please refresh and try again."

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Refresh the record to get the latest version",
            "Merge your changes with the current version",
            "Use optimistic concurrency control tokens",
            "Implement retry logic with exponential backoff"
        ])

        kwargs['status_code'] = 412
        kwargs['error_code'] = ErrorCode.CONCURRENCY_CONFLICT
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaServerError(AcumaticaError):
    """Server-side errors (5xx)."""

    def __init__(self, message: str = None, **kwargs):
        if not message:
            status = kwargs.get('status_code', 500)
            message = f"Server error ({status}). The server encountered an error processing your request."

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "This is likely a temporary issue - try again in a few moments",
            "If the problem persists, contact your Acumatica administrator",
            "Check the Acumatica server logs for more details",
            "Verify the Acumatica instance is running and accessible",
            "Consider implementing retry logic with exponential backoff"
        ])

        if kwargs.get('status_code') == 503:
            suggestions.insert(0, "The service may be under maintenance or overloaded")

        kwargs['error_code'] = ErrorCode.INTERNAL_SERVER_ERROR
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaConnectionError(AcumaticaError):
    """Network and connection errors."""

    def __init__(self, message: str, **kwargs):
        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Check your network connection",
            "Verify the Acumatica URL is correct",
            "Ensure the server is accessible from your network",
            "Check if a firewall is blocking the connection",
            "Verify SSL/TLS certificates if using HTTPS"
        ])

        kwargs['error_code'] = ErrorCode.CONNECTION_ERROR
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaTimeoutError(AcumaticaConnectionError):
    """Request timeout errors."""

    def __init__(self, message: str = None, timeout_seconds: Optional[float] = None, **kwargs):
        self.timeout_seconds = timeout_seconds

        if not message:
            if timeout_seconds:
                message = f"Request timed out after {timeout_seconds} seconds"
            else:
                message = "Request timed out"

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Increase the timeout value for long-running operations",
            "Break large operations into smaller batches",
            "Check if the server is under heavy load",
            "Optimize your query with filters and field selection"
        ])

        kwargs['error_code'] = ErrorCode.TIMEOUT
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaRateLimitError(AcumaticaError):
    """Rate limiting errors (429)."""

    def __init__(
        self,
        message: str = None,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        self.retry_after = retry_after

        if not message:
            if retry_after:
                message = f"Rate limit exceeded. Retry after {retry_after} seconds."
            else:
                message = "Rate limit exceeded"

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            f"Wait {retry_after or 'a few'} seconds before retrying",
            "Implement exponential backoff in your retry logic",
            "Reduce the frequency of API calls",
            "Consider batching multiple operations",
            "Cache frequently accessed data locally"
        ])

        kwargs['status_code'] = 429
        kwargs['error_code'] = ErrorCode.RATE_LIMIT_EXCEEDED
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaConfigError(AcumaticaError):
    """Configuration-related errors."""

    def __init__(self, message: str, missing_field: Optional[str] = None, **kwargs):
        self.missing_field = missing_field

        suggestions = kwargs.pop('suggestions', [])

        if missing_field:
            suggestions.append(f"Provide the missing configuration field: {missing_field}")

        suggestions.extend([
            "Check your .env file or environment variables",
            "Verify all required configuration fields are set",
            "Ensure configuration values are in the correct format",
            "Review the configuration documentation"
        ])

        kwargs['error_code'] = ErrorCode.CONFIG_INVALID
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaSchemaError(AcumaticaError):
    """Schema and endpoint errors."""

    def __init__(self, message: str, endpoint: Optional[str] = None, **kwargs):
        self.endpoint = endpoint

        suggestions = kwargs.pop('suggestions', [])

        if endpoint:
            suggestions.append(f"Verify the endpoint '{endpoint}' exists")

        suggestions.extend([
            "Check if the endpoint version is correct",
            "Ensure the Acumatica instance has the required customizations",
            "Verify the API endpoint is properly configured",
            "Try refreshing the schema cache"
        ])

        kwargs['error_code'] = ErrorCode.SCHEMA_ERROR
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaBatchError(AcumaticaError):
    """Batch execution errors."""

    def __init__(
        self,
        message: str,
        failed_operations: Optional[List[Dict[str, Any]]] = None,
        **kwargs
    ):
        self.failed_operations = failed_operations or []

        if self.failed_operations and not message:
            message = f"Batch execution failed. {len(self.failed_operations)} operations failed."

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Review the failed operations for specific errors",
            "Consider using fail_fast=False to continue on errors",
            "Implement retry logic for failed operations",
            "Break large batches into smaller chunks"
        ])

        kwargs['error_code'] = ErrorCode.BATCH_EXECUTION_FAILED
        super().__init__(message, suggestions=suggestions, **kwargs)


class AcumaticaRetryExhaustedError(AcumaticaError):
    """Retry limit exceeded errors."""

    def __init__(
        self,
        message: str = None,
        attempts: Optional[int] = None,
        last_error: Optional[Exception] = None,
        **kwargs
    ):
        self.attempts = attempts
        self.last_error = last_error

        if not message:
            message = f"Operation failed after {attempts or 'multiple'} attempts"
            if last_error:
                message += f". Last error: {last_error}"

        suggestions = kwargs.pop('suggestions', [])
        suggestions.extend([
            "Check if the issue is persistent or transient",
            "Review the last error for specific problems",
            "Increase retry limits for critical operations",
            "Implement circuit breaker pattern for failing services"
        ])

        kwargs['error_code'] = ErrorCode.RETRY_EXHAUSTED
        super().__init__(message, suggestions=suggestions, **kwargs)


def parse_api_error(
    response_data: Union[Dict[str, Any], str, None],
    status_code: int,
    operation: Optional[str] = None,
    entity: Optional[str] = None,
    entity_id: Optional[str] = None,
    request_data: Optional[Dict[str, Any]] = None
) -> AcumaticaError:
    """
    Parse API response and return appropriate exception with rich context.

    Args:
        response_data: Response from API (dict, string, or None)
        status_code: HTTP status code
        operation: Operation being performed
        entity: Entity type involved
        entity_id: Specific entity ID
        request_data: Original request data

    Returns:
        Appropriate AcumaticaError subclass with full context
    """
    # Parse response data if it's a string
    if isinstance(response_data, str):
        try:
            response_data = json.loads(response_data)
        except (json.JSONDecodeError, ValueError):
            # Keep as string if not valid JSON
            response_data = {"message": response_data}

    # Extract error details from response
    message = None
    error_code = None
    field_errors = {}

    if isinstance(response_data, dict):
        # Try various common error message locations
        message = (
            response_data.get("exceptionMessage") or
            response_data.get("message") or
            response_data.get("Message")
        )

        # Check nested error object
        if not message and isinstance(response_data.get("error"), dict):
            message = response_data["error"].get("message")
        elif not message and isinstance(response_data.get("error"), str):
            message = response_data["error"]

        if not message:
            message = response_data.get("ExceptionMessage")

        # Extract error code
        error_code = (
            response_data.get("errorCode") or
            response_data.get("code") or
            response_data.get("ErrorCode")
        )

        # Extract field-level errors
        field_errors = response_data.get("fieldErrors", {}) or response_data.get("errors", {})
    elif isinstance(response_data, str):
        message = response_data

    # Default message if none found
    if not message:
        message = f"API request failed with status code {status_code}"

    # Common context for all errors
    common_kwargs = {
        "status_code": status_code,
        "operation": operation,
        "entity": entity,
        "entity_id": entity_id,
        "request_data": request_data,
        "response_data": response_data,
        "error_code": error_code
    }

    # Map status codes to specific exceptions
    if status_code == 401:
        if "session" in message.lower() or "expired" in message.lower():
            common_kwargs["error_code"] = ErrorCode.SESSION_EXPIRED
        else:
            common_kwargs["error_code"] = ErrorCode.UNAUTHORIZED
        return AcumaticaAuthError(message, **common_kwargs)

    elif status_code == 403:
        common_kwargs["error_code"] = ErrorCode.FORBIDDEN
        return AcumaticaAuthError(f"Insufficient permissions: {message}", **common_kwargs)

    elif status_code == 404:
        return AcumaticaNotFoundError(message, **common_kwargs)

    elif status_code == 412:
        return AcumaticaConcurrencyError(message, **common_kwargs)

    elif status_code == 422:
        # Check if it's validation or business rule
        if field_errors or "validation" in message.lower():
            return AcumaticaValidationError(message, field_errors=field_errors, **common_kwargs)
        else:
            return AcumaticaBusinessRuleError(message, **common_kwargs)

    elif status_code == 429:
        retry_after = None
        if isinstance(response_data, dict):
            retry_after = (
                response_data.get("retryAfter") or
                response_data.get("Retry-After") or
                response_data.get("retry-after")
            )
        return AcumaticaRateLimitError(message, retry_after=retry_after, **common_kwargs)

    elif status_code == 400:
        # Could be validation or general bad request
        if field_errors:
            return AcumaticaValidationError(message, field_errors=field_errors, **common_kwargs)
        common_kwargs["error_code"] = ErrorCode.BAD_REQUEST
        return AcumaticaError(message, **common_kwargs)

    elif 500 <= status_code < 600:
        return AcumaticaServerError(message, **common_kwargs)

    else:
        # Generic error for unexpected status codes
        return AcumaticaError(message, **common_kwargs)


def enhance_exception_with_request_context(
    exception: Exception,
    method: str,
    url: str,
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None
) -> AcumaticaError:
    """
    Enhance any exception with HTTP request context.

    Args:
        exception: Original exception
        method: HTTP method used
        url: Request URL
        headers: Request headers
        params: Query parameters
        json_data: JSON body data

    Returns:
        Enhanced AcumaticaError with full context
    """
    if isinstance(exception, AcumaticaError):
        # Already an AcumaticaError, just add request context
        exception.context.update({
            "http_method": method.upper(),
            "url": url,
            "params": params,
            "request_headers": {k: v for k, v in (headers or {}).items()
                               if k.lower() not in ['authorization', 'cookie']}  # Redact sensitive headers
        })
        if json_data:
            exception.request_data = json_data
        return exception

    # Convert other exceptions to AcumaticaError
    if isinstance(exception, TimeoutError):
        return AcumaticaTimeoutError(
            str(exception),
            operation=f"{method.upper()} {url}",
            request_data=json_data
        )

    if isinstance(exception, ConnectionError):
        return AcumaticaConnectionError(
            str(exception),
            operation=f"{method.upper()} {url}",
            request_data=json_data
        )

    # Generic exception
    error = AcumaticaError(
        f"Unexpected error during {method.upper()} {url}: {exception}",
        operation=f"{method.upper()} {url}",
        request_data=json_data
    )
    error.context["original_error"] = str(type(exception).__name__)
    return error