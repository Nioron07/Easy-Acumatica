# src/easy_acumatica/__init__.py
"""Top-level package for Acumatica API wrapper."""
from .client import AcumaticaClient
from .batch import BatchCall, CallableWrapper, batch_call, create_batch_from_ids, create_batch_from_filters
from .exceptions import (
    AcumaticaError,
    AcumaticaAuthError,
    AcumaticaNotFoundError,
    AcumaticaValidationError,
    AcumaticaBusinessRuleError,
    AcumaticaConcurrencyError,
    AcumaticaServerError,
    AcumaticaConnectionError,
    AcumaticaTimeoutError,
    AcumaticaRateLimitError,
    AcumaticaConfigError,
    AcumaticaSchemaError,
    AcumaticaBatchError,
    AcumaticaRetryExhaustedError,
    ErrorCode
)

__all__ = [
    "AcumaticaClient",
    "BatchCall",
    "CallableWrapper",
    "batch_call",
    "create_batch_from_ids",
    "create_batch_from_filters",
    # Exceptions
    "AcumaticaError",
    "AcumaticaAuthError",
    "AcumaticaNotFoundError",
    "AcumaticaValidationError",
    "AcumaticaBusinessRuleError",
    "AcumaticaConcurrencyError",
    "AcumaticaServerError",
    "AcumaticaConnectionError",
    "AcumaticaTimeoutError",
    "AcumaticaRateLimitError",
    "AcumaticaConfigError",
    "AcumaticaSchemaError",
    "AcumaticaBatchError",
    "AcumaticaRetryExhaustedError",
    "ErrorCode"
]