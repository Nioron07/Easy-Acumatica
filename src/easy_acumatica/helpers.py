"""easy_acumatica.helpers
=====================

Helper functions for the Easy Acumatica package.

Provides utilities for:
- Response error handling
- Data transformation
- API-specific formatting
"""

import json
import logging
from typing import Any, Dict, Optional, Union

import requests

from .exceptions import AcumaticaConnectionError, AcumaticaError, AcumaticaTimeoutError, parse_api_error

logger = logging.getLogger(__name__)


def _raise_with_detail(resp: requests.Response) -> None:
    """
    Raise AcumaticaError with a readable explanation when the HTTP
    status is not 2xx.
    
    Args:
        resp: Response object from requests
        
    Raises:
        AcumaticaError: Appropriate subclass based on error type
    """
    # Success - no error to raise
    if 200 <= resp.status_code < 300:
        return

    # Try to parse error details from response
    try:
        data = resp.json()
        if isinstance(data, dict):
            # Use the enhanced error parser
            raise parse_api_error(data, resp.status_code)
        else:
            # Response is JSON but not a dict (maybe a list or string)
            detail = str(data)
    except (ValueError, json.JSONDecodeError):
        # Response is not JSON
        detail = resp.text or f"HTTP {resp.status_code}"
    except requests.exceptions.RequestException as e:
        # Network or connection error
        if isinstance(e, requests.exceptions.Timeout):
            raise AcumaticaTimeoutError(f"Request timed out: {e}")
        elif isinstance(e, requests.exceptions.ConnectionError):
            raise AcumaticaConnectionError(f"Connection error: {e}")
        else:
            raise AcumaticaConnectionError(f"Request failed: {e}")

    # If we get here, we couldn't parse a specific error
    msg = f"Acumatica API error {resp.status_code}: {detail}"
    raise AcumaticaError(msg, status_code=resp.status_code)


def format_api_value(value: Any) -> Dict[str, Any]:
    """
    Format a Python value for the Acumatica API.
    
    The Acumatica API expects values in a specific format:
    - Simple values: {"value": <value>}
    - Lists: [{"value": <item1>}, {"value": <item2>}, ...]
    - Nested objects: Recursively formatted
    
    Args:
        value: Python value to format
        
    Returns:
        Formatted value for API
        
    Example:
        >>> format_api_value("Hello")
        {'value': 'Hello'}
        >>> format_api_value([1, 2, 3])
        [{'value': 1}, {'value': 2}, {'value': 3}]
    """
    if value is None:
        return {"value": None}
    elif isinstance(value, (str, int, float, bool)):
        return {"value": value}
    elif isinstance(value, list):
        return [format_api_value(item) for item in value]
    elif isinstance(value, dict):
        # If it already has the API format, return as-is
        if "value" in value and len(value) == 1:
            return value
        # Otherwise, format each key-value pair
        return {k: format_api_value(v) for k, v in value.items()}
    else:
        # For other types, convert to string
        return {"value": str(value)}


def extract_api_value(data: Union[Dict[str, Any], list, Any]) -> Any:
    """
    Extract Python value from Acumatica API format.
    
    Reverses the format_api_value transformation.
    
    Args:
        data: API-formatted data
        
    Returns:
        Extracted Python value
        
    Example:
        >>> extract_api_value({'value': 'Hello'})
        'Hello'
        >>> extract_api_value([{'value': 1}, {'value': 2}])
        [1, 2]
    """
    if isinstance(data, dict):
        if "value" in data and len(data) == 1:
            # Simple value format
            return data["value"]
        elif "_links" in data or "id" in data:
            # This is likely an entity, keep as dict but extract values
            result = {}
            for key, value in data.items():
                if key not in ["_links", "note", "error", "rowNumber"]:
                    result[key] = extract_api_value(value)
            return result
        else:
            # Nested object, recursively extract
            return {k: extract_api_value(v) for k, v in data.items()}
    elif isinstance(data, list):
        # Extract each item in the list
        return [extract_api_value(item) for item in data]
    else:
        # Already a simple value
        return data


def clean_entity_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean entity data for API submission.
    
    Removes system fields and empty values that shouldn't be sent
    to the API when creating or updating entities.
    
    Args:
        data: Entity data dictionary
        
    Returns:
        Cleaned data suitable for API submission
    """
    # Fields to always exclude
    system_fields = {
        "_links", "note", "error", "rowNumber", "id",
        "CreatedDateTime", "LastModifiedDateTime",
        "tstamp", "NoteID", "RefNbr"
    }

    # Clean the data
    cleaned = {}
    for key, value in data.items():
        # Skip system fields
        if key in system_fields:
            continue

        # Skip None values
        if value is None:
            continue

        # Skip empty collections
        if isinstance(value, (list, dict)) and not value:
            continue

        # Skip empty strings for non-required fields
        if isinstance(value, str) and not value.strip():
            continue

        # Recursively clean nested objects
        if isinstance(value, dict) and "value" not in value:
            cleaned_nested = clean_entity_data(value)
            if cleaned_nested:  # Only include if not empty after cleaning
                cleaned[key] = cleaned_nested
        else:
            cleaned[key] = value

    return cleaned


def parse_odata_error(error_response: Dict[str, Any]) -> str:
    """
    Parse OData error response into readable message.
    
    Args:
        error_response: Error response from OData endpoint
        
    Returns:
        Human-readable error message
    """
    if "error" in error_response:
        error = error_response["error"]
        if isinstance(error, dict):
            message = error.get("message", "Unknown OData error")
            if isinstance(message, dict):
                return message.get("value", str(message))
            return str(message)
        return str(error)

    # Fallback to general message
    return json.dumps(error_response)


def merge_entity_data(
    original: Dict[str, Any],
    updates: Dict[str, Any],
    merge_lists: bool = False
) -> Dict[str, Any]:
    """
    Merge update data into original entity data.
    
    Args:
        original: Original entity data
        updates: Updates to apply
        merge_lists: If True, append to lists instead of replacing
        
    Returns:
        Merged entity data
    """
    result = original.copy()

    for key, value in updates.items():
        if value is None:
            # Explicit None means remove the field
            result.pop(key, None)
        elif key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested objects
            result[key] = merge_entity_data(result[key], value, merge_lists)
        elif key in result and merge_lists and isinstance(result[key], list) and isinstance(value, list):
            # Append to existing list
            result[key] = result[key] + value
        else:
            # Replace value
            result[key] = value

    return result


def validate_response_data(
    data: Any,
    expected_type: Optional[type] = None,
    required_fields: Optional[list] = None
) -> None:
    """
    Validate response data meets expected criteria.
    
    Args:
        data: Response data to validate
        expected_type: Expected data type
        required_fields: List of required field names
        
    Raises:
        AcumaticaError: If validation fails
    """
    if expected_type and not isinstance(data, expected_type):
        raise AcumaticaError(
            f"Invalid response type. Expected {expected_type.__name__}, "
            f"got {type(data).__name__}"
        )

    if required_fields and isinstance(data, dict):
        missing = [field for field in required_fields if field not in data]
        if missing:
            raise AcumaticaError(
                f"Missing required fields in response: {', '.join(missing)}"
            )


def format_error_details(
    error: Exception,
    include_traceback: bool = False
) -> Dict[str, Any]:
    """
    Format exception details for logging or API response.
    
    Args:
        error: Exception to format
        include_traceback: Whether to include full traceback
        
    Returns:
        Dictionary with error details
    """
    import traceback

    details = {
        "error_type": type(error).__name__,
        "message": str(error),
    }

    # Add Acumatica-specific details if available
    if isinstance(error, AcumaticaError):
        if hasattr(error, "status_code") and error.status_code:
            details["status_code"] = error.status_code
        if hasattr(error, "response_data") and error.response_data:
            details["response_data"] = error.response_data
        if hasattr(error, "error_code") and error.error_code:
            details["error_code"] = error.error_code
        if hasattr(error, "field_errors") and error.field_errors:
            details["field_errors"] = error.field_errors

    if include_traceback:
        details["traceback"] = traceback.format_exc()

    return details


def safe_get_nested(
    data: Dict[str, Any],
    path: str,
    default: Any = None,
    separator: str = "."
) -> Any:
    """
    Safely get nested value from dictionary.
    
    Args:
        data: Dictionary to search
        path: Dot-separated path to value
        default: Default value if not found
        separator: Path separator (default: ".")
        
    Returns:
        Value at path or default
        
    Example:
        >>> data = {"Contact": {"Email": {"value": "test@example.com"}}}
        >>> safe_get_nested(data, "Contact.Email.value")
        'test@example.com'
    """
    keys = path.split(separator)
    current = data

    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default

    return current


def build_entity_url(
    base_url: str,
    endpoint: str,
    version: str,
    entity: str,
    entity_id: Optional[str] = None,
    action: Optional[str] = None
) -> str:
    """
    Build a properly formatted entity URL.
    
    Args:
        base_url: Base URL of Acumatica instance
        endpoint: API endpoint name
        version: API version
        entity: Entity type name
        entity_id: Optional entity ID
        action: Optional action name
        
    Returns:
        Formatted URL
        
    Example:
        >>> build_entity_url("https://example.com", "Default", "20.200.001", 
        ...                  "Contact", "123", "Activate")
        'https://example.com/entity/Default/20.200.001/Contact/123/Activate'
    """
    parts = [base_url.rstrip("/"), "entity", endpoint, version, entity]

    if entity_id:
        parts.append(entity_id)

    if action:
        parts.append(action)

    return "/".join(parts)


class ResponseLogger:
    """
    Context manager for logging API responses.
    
    Example:
        >>> with ResponseLogger("GetContact") as logger:
        ...     response = make_api_call()
        ...     logger.log_response(response)
    """

    def __init__(
        self,
        operation: str,
        log_level: int = logging.DEBUG,
        max_body_length: int = 1000
    ):
        """
        Initialize response logger.
        
        Args:
            operation: Name of the operation
            log_level: Logging level
            max_body_length: Maximum response body length to log
        """
        self.operation = operation
        self.log_level = log_level
        self.max_body_length = max_body_length
        self.logger = logging.getLogger(__name__)

    def __enter__(self):
        """Enter context."""
        self.logger.log(self.log_level, f"Starting {self.operation}")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context."""
        if exc_type:
            self.logger.error(f"{self.operation} failed: {exc_val}")
        else:
            self.logger.log(self.log_level, f"{self.operation} completed")

    def log_response(self, response: requests.Response) -> None:
        """Log response details."""
        self.logger.log(
            self.log_level,
            f"{self.operation} response: {response.status_code} - "
            f"{len(response.content)} bytes"
        )

        if response.text and self.logger.isEnabledFor(self.log_level):
            body = response.text
            if len(body) > self.max_body_length:
                body = body[:self.max_body_length] + "..."
            self.logger.log(self.log_level, f"Response body: {body}")
