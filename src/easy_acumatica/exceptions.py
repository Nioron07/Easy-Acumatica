"""easy_acumatica.exceptions
========================

Custom exception classes for Easy Acumatica.

Provides a hierarchy of exceptions for different error scenarios,
making it easier to handle specific error cases in client code.
"""

from typing import Any, Dict, Optional


class AcumaticaError(Exception):
    """
    Base exception class for all errors related to the Acumatica API.
    
    Attributes:
        message: Error message
        status_code: HTTP status code (if applicable)
        response_data: Raw response data from API (if available)
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AcumaticaError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response data from API
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response_data = response_data

    def __str__(self) -> str:
        """String representation of the error."""
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message


class AcumaticaAuthError(AcumaticaError):
    """
    Raised for authentication-related errors.
    
    This includes:
    - Invalid credentials (401)
    - Insufficient permissions (403)
    - Session timeout
    - Login failures
    """
    pass


class AcumaticaConnectionError(AcumaticaError):
    """
    Raised for connection-related errors.
    
    This includes:
    - Network connectivity issues
    - DNS resolution failures
    - Connection timeouts
    - SSL/TLS errors
    """
    pass


class AcumaticaTimeoutError(AcumaticaConnectionError):
    """
    Raised when a request times out.
    
    This is a specific type of connection error that occurs
    when the server doesn't respond within the timeout period.
    """
    pass


class AcumaticaAPIError(AcumaticaError):
    """
    Raised for API-specific errors.
    
    This includes:
    - Invalid endpoint
    - Malformed requests
    - Business logic errors
    - Validation errors
    """

    def __init__(
        self,
        message: str,
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ):
        """
        Initialize AcumaticaAPIError.
        
        Args:
            message: Error message
            status_code: HTTP status code
            response_data: Response data from API
            error_code: Specific API error code
        """
        super().__init__(message, status_code, response_data)
        self.error_code = error_code


class AcumaticaValidationError(AcumaticaAPIError):
    """
    Raised when data validation fails.
    
    This includes:
    - Missing required fields
    - Invalid field values
    - Business rule violations
    """

    def __init__(
        self,
        message: str,
        field_errors: Optional[Dict[str, str]] = None,
        **kwargs
    ):
        """
        Initialize AcumaticaValidationError.
        
        Args:
            message: Error message
            field_errors: Dictionary of field-specific errors
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, **kwargs)
        self.field_errors = field_errors or {}


class AcumaticaRateLimitError(AcumaticaAPIError):
    """
    Raised when API rate limits are exceeded.
    
    Attributes:
        retry_after: Seconds to wait before retrying (if provided by API)
    """

    def __init__(
        self,
        message: str,
        retry_after: Optional[int] = None,
        **kwargs
    ):
        """
        Initialize AcumaticaRateLimitError.
        
        Args:
            message: Error message
            retry_after: Seconds to wait before retrying
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, status_code=429, **kwargs)
        self.retry_after = retry_after


class AcumaticaSchemaError(AcumaticaError):
    """
    Raised when there are issues with the API schema.
    
    This includes:
    - Unable to fetch schema
    - Invalid schema format
    - Incompatible schema version
    """
    pass


class AcumaticaConfigError(AcumaticaError):
    """
    Raised for configuration-related errors.
    
    This includes:
    - Missing required configuration
    - Invalid configuration values
    - Configuration file errors
    """
    pass


class AcumaticaNotFoundError(AcumaticaAPIError):
    """
    Raised when a requested resource is not found (404).
    
    Attributes:
        resource_type: Type of resource (e.g., "Contact", "Invoice")
        resource_id: ID of the missing resource
    """

    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize AcumaticaNotFoundError.
        
        Args:
            message: Error message
            resource_type: Type of missing resource
            resource_id: ID of missing resource
            **kwargs: Additional arguments for parent class
        """
        super().__init__(message, status_code=404, **kwargs)
        self.resource_type = resource_type
        self.resource_id = resource_id


class AcumaticaServerError(AcumaticaAPIError):
    """
    Raised for server-side errors (5xx).
    
    This includes:
    - Internal server errors (500)
    - Service unavailable (503)
    - Gateway timeout (504)
    """
    pass


def parse_api_error(response_data: Dict[str, Any], status_code: int) -> AcumaticaError:
    """
    Parse API response and return appropriate exception.
    
    Args:
        response_data: Response data from API
        status_code: HTTP status code
        
    Returns:
        Appropriate AcumaticaError subclass instance
    """
    # Extract error details from response
    message = (
        response_data.get("exceptionMessage") or
        response_data.get("message") or
        response_data.get("error") or
        f"API error with status code {status_code}"
    )

    error_code = response_data.get("errorCode") or response_data.get("code")

    # Map status codes to specific exceptions
    if status_code == 401:
        return AcumaticaAuthError(message, status_code, response_data)
    elif status_code == 403:
        return AcumaticaAuthError(f"Insufficient permissions: {message}", status_code, response_data)
    elif status_code == 404:
        return AcumaticaNotFoundError(message, status_code=status_code, response_data=response_data)
    elif status_code == 429:
        retry_after = response_data.get("retryAfter")
        return AcumaticaRateLimitError(message, retry_after=retry_after, response_data=response_data)
    elif 400 <= status_code < 500:
        # Check for validation errors
        if "validation" in message.lower() or "field" in response_data:
            field_errors = response_data.get("fieldErrors", {})
            return AcumaticaValidationError(
                message,
                field_errors=field_errors,
                status_code=status_code,
                response_data=response_data
            )
        return AcumaticaAPIError(message, status_code, response_data, error_code)
    elif 500 <= status_code < 600:
        return AcumaticaServerError(message, status_code, response_data, error_code)
    else:
        return AcumaticaError(message, status_code, response_data)
