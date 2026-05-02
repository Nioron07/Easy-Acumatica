"""easy_acumatica.utils
====================

Utility functions and classes for the Easy Acumatica package.

Provides common functionality like:
- Retry decorators
- Rate limiting
- Input validation
"""

import functools
import logging
import threading
import time
from typing import Any, Callable, List, Optional, TypeVar, Union

import requests

from .exceptions import AcumaticaValidationError

logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_on_error(
    max_attempts: int = 3,
    delay: float = 1.0,
    backoff: float = 2.0,
    exceptions: tuple = (requests.RequestException,),
    logger: Optional[logging.Logger] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator that retries a function on specified exceptions.
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Initial delay between retries in seconds
        backoff: Multiplier for delay after each retry
        exceptions: Tuple of exception types to catch
        logger: Optional logger instance
        
    Returns:
        Decorated function that implements retry logic
        
    Example:
        >>> @retry_on_error(max_attempts=3, delay=1.0)
        ... def flaky_api_call():
        ...     # This will retry up to 3 times on RequestException
        ...     response = requests.get("https://api.example.com")
        ...     return response.json()
    """
    if logger is None:
        logger = logging.getLogger(__name__)
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 1
            current_delay = delay
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_attempts:
                        logger.error(
                            f"Max retries ({max_attempts}) exceeded for {getattr(func, '__name__', repr(func))}: {e}"
                        )
                        raise

                    logger.warning(
                        f"Attempt {attempt}/{max_attempts} failed for {getattr(func, '__name__', repr(func))}: {e}. "
                        f"Retrying in {current_delay:.1f}s..."
                    )
                    time.sleep(current_delay)
                    current_delay *= backoff
                    attempt += 1
        
        return wrapper
    return decorator


class RateLimiter:
    """
    Thread-safe rate limiter using token bucket algorithm.
    
    Attributes:
        calls_per_second: Maximum calls allowed per second
        burst_size: Maximum burst capacity (defaults to calls_per_second)
    """
    
    def __init__(self, calls_per_second: float = 10.0, burst_size: Optional[int] = None):
        """
        Initialize rate limiter.
        
        Args:
            calls_per_second: Sustained rate limit
            burst_size: Maximum burst capacity (defaults to calls_per_second)
        """
        self.calls_per_second = calls_per_second
        self.burst_size = burst_size or int(calls_per_second)
        self.min_interval = 1.0 / calls_per_second
        
        # Track state globally (not per-instance)
        self._last_call_time = 0.0
        self._tokens = float(self.burst_size)
        self._lock = threading.Lock()
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """Decorator to apply rate limiting to a function.

        Reserves a token under ``self._lock``, then sleeps **outside** the
        lock so concurrent callers can compute their own wait windows in
        parallel. Holding ``time.sleep`` inside the lock would serialize
        every limited call through the same sleep, defeating the burst
        bucket and effectively single-threading all traffic.
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            sleep_time = self._reserve_token()
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.3f}s")
                time.sleep(sleep_time)
            return func(*args, **kwargs)

        return wrapper

    def _reserve_token(self) -> float:
        """Refill, reserve one token, and return how long the caller should sleep."""
        with self._lock:
            current_time = time.time()
            time_passed = current_time - self._last_call_time
            self._tokens = min(
                self.burst_size,
                self._tokens + time_passed * self.calls_per_second,
            )

            sleep_time = 0.0
            if self._tokens < 1.0:
                sleep_time = (1.0 - self._tokens) / self.calls_per_second
                # Pretend the sleep already happened so the next caller's
                # accounting starts after our reserved slot.
                self._tokens = 1.0
                self._last_call_time = current_time + sleep_time
            else:
                self._last_call_time = current_time

            self._tokens -= 1.0
            return sleep_time


def validate_entity_id(entity_id: Union[str, List[str]]) -> str:
    """
    Validates and formats entity ID(s) for API calls.
    
    Args:
        entity_id: Single ID string or list of ID strings
        
    Returns:
        Comma-separated string of IDs
        
    Raises:
        ValueError: If entity_id is invalid
        TypeError: If entity_id is wrong type
        
    Example:
        >>> validate_entity_id("12345")
        '12345'
        >>> validate_entity_id(["123", "456", "789"])
        '123,456,789'
    """
    if isinstance(entity_id, list):
        if not entity_id:
            raise AcumaticaValidationError(
                "Entity ID list cannot be empty",
                field_errors={"entity_ids": "List cannot be empty"},
                suggestions=["Provide at least one entity ID"]
            )
        if not all(isinstance(id, str) for id in entity_id):
            raise AcumaticaValidationError(
                "All entity IDs must be strings",
                field_errors={"entity_ids": f"Non-string ID found: {[id for id in entity_id if not isinstance(id, str)]}"},
                suggestions=["Convert all IDs to strings before passing"]
            )
        # Validate each ID
        for id in entity_id:
            if not id.strip():
                raise AcumaticaValidationError(
                    f"Invalid entity ID in list: '{id}'",
                    field_errors={"entity_ids": f"Invalid ID: '{id}'"},
                    suggestions=["Entity IDs cannot be empty strings"]
                )
        return ",".join(entity_id)
    elif isinstance(entity_id, str):
        if not entity_id.strip():
            raise AcumaticaValidationError(
                "Entity ID cannot be empty",
                field_errors={"entity_id": "Empty string"},
                suggestions=["Provide a valid entity ID"]
            )
        return entity_id
    else:
        raise AcumaticaValidationError(
            f"Entity ID must be string or list of strings, not {type(entity_id).__name__}",
            field_errors={"entity_id": f"Invalid type: {type(entity_id).__name__}"},
            suggestions=["Pass a string ID or list of string IDs"]
        )


