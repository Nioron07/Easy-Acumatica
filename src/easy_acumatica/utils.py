"""easy_acumatica.utils
====================

Utility functions and classes for the Easy Acumatica package.

Provides common functionality like:
- Retry decorators
- Rate limiting
- Input validation
- Logging utilities
- Performance monitoring
"""

import functools
import logging
import threading
import time
import os
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, TypeVar, Union
from weakref import WeakKeyDictionary

import requests

from .exceptions import AcumaticaError

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
            last_exception = None
            
            while attempt <= max_attempts:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
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
            
            # This should never be reached, but just in case
            if last_exception:
                raise last_exception
            raise AcumaticaError(f"Unexpected error in retry logic for {getattr(func, '__name__', repr(func))}")
        
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
        """Decorator to apply rate limiting to a function."""
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self._lock:
                current_time = time.time()
                
                # Calculate tokens accumulated since last call
                time_passed = current_time - self._last_call_time
                self._tokens = min(
                    self.burst_size,
                    self._tokens + time_passed * self.calls_per_second
                )
                
                # Check if we have tokens available
                if self._tokens < 1.0:
                    sleep_time = (1.0 - self._tokens) / self.calls_per_second
                    logger.debug(f"Rate limit reached, sleeping for {sleep_time:.3f}s")
                    time.sleep(sleep_time)
                    self._tokens = 1.0
                
                # Consume one token
                self._tokens -= 1.0
                self._last_call_time = time.time()
            
            return func(*args, **kwargs)
        
        return wrapper


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
            raise ValueError("Entity ID list cannot be empty")
        if not all(isinstance(id, str) for id in entity_id):
            raise ValueError("All entity IDs must be strings")
        # Validate each ID
        for id in entity_id:
            if not id.strip():
                raise ValueError(f"Invalid entity ID in list: '{id}'")
        return ",".join(entity_id)
    elif isinstance(entity_id, str):
        if not entity_id.strip():
            raise ValueError("Entity ID cannot be empty")
        return entity_id
    else:
        raise TypeError(f"Entity ID must be string or list of strings, not {type(entity_id).__name__}")


def sanitize_filename(filename: str) -> str:
    """
    Sanitizes a filename for safe use in file operations.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename safe for file operations
        
    Example:
        >>> sanitize_filename("my<file>name?.txt")
        'my_file_name_.txt'
    """
    import re
    # Remove or replace unsafe characters
    safe_name = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Remove control characters
    safe_name = re.sub(r'[\x00-\x1f\x7f]', '', safe_name)
    # Limit length
    max_length = 255
    if len(safe_name) > max_length:
        name, ext = os.path.splitext(safe_name)
        safe_name = name[:max_length - len(ext)] + ext
    return safe_name


class PerformanceMonitor:
    """
    Context manager for monitoring operation performance.
    
    Example:
        >>> with PerformanceMonitor("API call") as monitor:
        ...     response = make_api_call()
        >>> print(f"Operation took {monitor.elapsed:.3f} seconds")
    """
    
    def __init__(self, operation_name: str, logger: Optional[logging.Logger] = None):
        """
        Initialize performance monitor.
        
        Args:
            operation_name: Name of the operation being monitored
            logger: Optional logger for automatic logging
        """
        self.operation_name = operation_name
        self.logger = logger or logging.getLogger(__name__)
        self.start_time: Optional[float] = None
        self.end_time: Optional[float] = None
        self.elapsed: Optional[float] = None
    
    def __enter__(self):
        """Start timing."""
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop timing and log results."""
        self.end_time = time.time()
        self.elapsed = self.end_time - self.start_time
        
        if exc_type is None:
            self.logger.debug(f"{self.operation_name} completed in {self.elapsed:.3f}s")
        else:
            self.logger.warning(
                f"{self.operation_name} failed after {self.elapsed:.3f}s: {exc_type.__name__}"
            )


def chunk_list(lst: List[Any], chunk_size: int) -> List[List[Any]]:
    """
    Split a list into chunks of specified size.
    
    Args:
        lst: List to chunk
        chunk_size: Maximum size of each chunk
        
    Returns:
        List of chunks
        
    Example:
        >>> chunk_list([1, 2, 3, 4, 5], 2)
        [[1, 2], [3, 4], [5]]
    """
    if chunk_size <= 0:
        raise ValueError("Chunk size must be positive")
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def format_odata_datetime(dt: datetime) -> str:
    """
    Format datetime for OData queries.
    
    Args:
        dt: Datetime object
        
    Returns:
        OData-formatted datetime string
        
    Example:
        >>> format_odata_datetime(datetime(2024, 1, 15, 10, 30, 0))
        "datetime'2024-01-15T10:30:00'"
    """
    return f"datetime'{dt.isoformat()}'"


def parse_acumatica_datetime(date_str: str) -> Optional[datetime]:
    """
    Parse datetime string from Acumatica API.
    
    Args:
        date_str: Datetime string from API
        
    Returns:
        Parsed datetime or None if invalid
    """
    if not date_str:
        return None
    
    # Common Acumatica datetime formats
    formats = [
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M:%S.%f",
        "%Y-%m-%dT%H:%M:%SZ",
        "%Y-%m-%dT%H:%M:%S.%fZ",
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    
    logger.warning(f"Could not parse datetime: {date_str}")
    return None


class BatchProcessor:
    """
    Helper for processing items in batches with progress tracking.
    
    Example:
        >>> processor = BatchProcessor(batch_size=100)
        >>> for batch in processor.process(large_list):
        ...     api_client.bulk_update(batch)
    """
    
    def __init__(
        self,
        batch_size: int = 100,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """
        Initialize batch processor.
        
        Args:
            batch_size: Size of each batch
            progress_callback: Optional callback(current, total) for progress updates
        """
        self.batch_size = batch_size
        self.progress_callback = progress_callback
    
    def process(self, items: List[Any]) -> List[List[Any]]: # type: ignore
        """
        Process items in batches.
        
        Args:
            items: List of items to process
            
        Yields:
            Batches of items
        """
        total = len(items)
        processed = 0
        
        for batch in chunk_list(items, self.batch_size):
            yield batch
            processed += len(batch)
            
            if self.progress_callback:
                self.progress_callback(processed, total)


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None
) -> None:
    """
    Configure logging for the Easy Acumatica package.
    
    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional file path for log output
        format_string: Optional custom format string
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=format_string,
        handlers=[
            logging.StreamHandler(),
            *(logging.FileHandler(log_file) if log_file else [])
        ]
    )
    
    # Set appropriate levels for third-party libraries
    logging.getLogger("requests").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)