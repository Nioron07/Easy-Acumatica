# src/easy_acumatica/__init__.py
"""Top-level package for Acumatica API wrapper."""

try:
    from importlib.metadata import PackageNotFoundError, version as _pkg_version

    try:
        __version__ = _pkg_version("easy_acumatica")
    except PackageNotFoundError:  # editable install / source tree without metadata
        __version__ = "0.0.0+unknown"
except ImportError:  # pragma: no cover - importlib.metadata is in stdlib >=3.8
    __version__ = "0.0.0+unknown"

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