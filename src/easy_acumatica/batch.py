"""Improved batch calling implementation that uses separate sessions for each call
to achieve optimal performance by avoiding serialization bottlenecks."""

import concurrent.futures
import logging
import time
import requests
from dataclasses import dataclass
from .exceptions import (
    AcumaticaError,
    AcumaticaBatchError,
    AcumaticaAuthError,
    ErrorCode
)
from typing import Any, Callable, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)

@dataclass
class BatchCallResult:
    """Result of a single call within a batch."""
    success: bool
    result: Any = None
    error: Optional[Exception] = None
    execution_time: float = 0.0
    call_index: int = 0

@dataclass
class BatchCallStats:
    """Statistics for a batch execution."""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    total_time: float = 0.0
    average_call_time: float = 0.0
    max_call_time: float = 0.0
    min_call_time: float = 0.0
    concurrency_level: int = 0

class CallableWrapper:
    """Wrapper for API calls that allows deferred execution."""
    
    def __init__(self, func: Callable, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.method_name = getattr(func, '__name__', 'unknown')  # Add method_name attribute
    
    def execute(self) -> Any:
        """Execute the wrapped function call synchronously."""
        return self.func(*self.args, **self.kwargs)

class BatchCall:
    """
    Execute multiple API calls concurrently using separate HTTP sessions for optimal performance.
    
    This implementation creates separate HTTP sessions under the same AcumaticaClient to avoid
    serialization bottlenecks while reusing the already-built schema and service infrastructure.
    Each session is authenticated independently and cleaned up after use.
    """
    
    def __init__(
        self,
        *calls: Union[CallableWrapper, Callable],
        max_concurrent: Optional[int] = None,
        timeout: Optional[float] = None,
        fail_fast: bool = False,
        return_exceptions: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None
    ):
        """Initialize a batch call with separate HTTP sessions execution."""
        self.calls: List[CallableWrapper] = []
        self.max_concurrent = max_concurrent or 10
        self.timeout = timeout
        self.fail_fast = fail_fast
        self.return_exceptions = return_exceptions
        self.progress_callback = progress_callback
        
        # Process input calls
        for call in calls:
            if isinstance(call, CallableWrapper):
                self.calls.append(call)
            elif callable(call):
                self.calls.append(CallableWrapper(call))
            else:
                raise TypeError(f"Invalid call type: {type(call)}. Must be callable or CallableWrapper.")
        
        # State tracking
        self.results: List[BatchCallResult] = []
        self.stats: BatchCallStats = BatchCallStats()
        self.executed: bool = False
        
        logger.debug(f"Created BatchCall with {len(self.calls)} calls using separate HTTP sessions")
    
    def execute(self) -> Tuple[Any, ...]:
        """
        Execute all calls concurrently using separate HTTP sessions for optimal performance.
        
        Each call gets its own HTTP session to avoid serialization bottlenecks while
        reusing the existing client schema and services. Sessions are automatically
        authenticated and cleaned up.
        """
        if self.executed:
            logger.warning("BatchCall already executed, returning cached results")
            return self.get_results_tuple()
        
        if not self.calls:
            self.stats = BatchCallStats(
                total_calls=0,
                successful_calls=0,
                failed_calls=0,
                total_time=0.0,
                concurrency_level=0
            )
            self.executed = True
            return tuple()
        
        start_time = time.time()
        self.results = [BatchCallResult(success=False, call_index=i) for i in range(len(self.calls))]
        
        logger.info(f"Starting separate HTTP session batch execution with {len(self.calls)} calls, max concurrent: {self.max_concurrent}")
        
        first_error = None
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                # Submit all tasks with separate session execution
                future_to_index = {
                    executor.submit(self._execute_call_with_separate_session, call, i): i
                    for i, call in enumerate(self.calls)
                }
                
                # Wait for completion with optional timeout
                try:
                    completed_futures = concurrent.futures.as_completed(
                        future_to_index.keys(), 
                        timeout=self.timeout
                    )
                except concurrent.futures.TimeoutError:
                    logger.error(f"Batch execution timed out after {self.timeout} seconds")
                    raise
                
                completed_count = 0
                
                for future in completed_futures:
                    index = future_to_index[future]
                    try:
                        result = future.result()  # This will re-raise any exception from the thread
                        self.results[index] = result
                    except Exception as e:
                        # Create an error result
                        self.results[index] = BatchCallResult(
                            success=False,
                            error=e,
                            execution_time=0.0,
                            call_index=index
                        )
                        if self.fail_fast and first_error is None:
                            first_error = e
                    
                    completed_count += 1
                    
                    # Progress callback
                    if self.progress_callback:
                        try:
                            self.progress_callback(completed_count, len(self.calls))
                        except Exception as e:
                            logger.warning(f"Progress callback failed: {e}")
                    
                    # Handle fail_fast
                    if self.fail_fast and first_error:
                        raise AcumaticaBatchError(
                            f"Batch execution failed (fail_fast=True): {first_error}",
                            failed_operations=[{"index": index, "error": str(first_error)}]
                        )

                
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            if not self.return_exceptions:
                raise
            # If return_exceptions is True, we continue to process results
        
        # Calculate statistics
        total_time = time.time() - start_time
        call_times = [r.execution_time for r in self.results if r.execution_time > 0]
        successful = sum(1 for r in self.results if r.success)
        failed = len(self.results) - successful
        
        self.stats = BatchCallStats(
            total_calls=len(self.calls),
            successful_calls=successful,
            failed_calls=failed,
            total_time=total_time,
            average_call_time=sum(call_times) / len(call_times) if call_times else 0,
            max_call_time=max(call_times) if call_times else 0,
            min_call_time=min(call_times) if call_times else 0,
            concurrency_level=min(self.max_concurrent, len(self.calls))
        )
        
        self.executed = True
        
        logger.info(
            f"Separate HTTP session batch execution completed in {total_time:.2f}s: "
            f"{successful}/{len(self.calls)} successful"
        )
        
        # Handle fail_fast
        if self.fail_fast and first_error:
            raise Exception(f"Batch execution failed (fail_fast=True): {first_error}")
        
        return self.get_results_tuple()
    
    def _execute_call_with_separate_session(self, call: CallableWrapper, index: int) -> BatchCallResult:
        """
        Execute a single call using a completely separate authenticated HTTP session.
        
        Args:
            call: The call to execute
            index: Index of this call in the batch
            
        Returns:
            BatchCallResult with execution details
        """
        start_time = time.time()
        temp_session = None
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            try:
                # Get the original client from the call
                original_client = self._get_original_client_from_call(call)
                if not original_client:
                    # If we can't get the client, just execute the call directly
                    # This handles lambda functions and other non-service calls
                    result = call.execute()
                    execution_time = time.time() - start_time
                    return BatchCallResult(
                        success=True,
                        result=result,
                        execution_time=execution_time,
                        call_index=index
                    )
                
                logger.debug(f"Creating separate session for call {index} (attempt {attempt + 1})")
                
                # Create a completely separate HTTP session 
                if temp_session:
                    temp_session.close()  # Close previous attempt if it exists
                temp_session = self._create_separate_http_session(original_client)
                
                # Add a small delay between concurrent logins to avoid server overload
                if attempt == 0 and index > 0:
                    time.sleep(index * 0.1)  # Stagger login attempts
                
                # Authenticate the temporary session directly
                self._authenticate_session(temp_session, original_client, index)
                
                # Execute the call using the authenticated temp session
                result = self._execute_call_with_session(call, temp_session, original_client)
                
                # Logout the temporary session 
                self._logout_session(temp_session, original_client)
                
                execution_time = time.time() - start_time
                
                logger.debug(f"Call {index} completed successfully in {execution_time:.3f}s with separate session")
                return BatchCallResult(
                    success=True,
                    result=result,
                    execution_time=execution_time,
                    call_index=index
                )
                
            except Exception as e:
                execution_time = time.time() - start_time
                
                # Check if this is a retryable error
                is_retryable = (
                    "401" in str(e) or 
                    "authentication" in str(e).lower() or
                    "login" in str(e).lower() or
                    "unauthorized" in str(e).lower()
                )
                
                if is_retryable and attempt < max_retries - 1:
                    logger.warning(f"Call {index} attempt {attempt + 1} failed with retryable error: {e}. Retrying in {retry_delay}s...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                    continue
                
                logger.debug(f"Call {index} failed after {execution_time:.3f}s with separate session (attempt {attempt + 1}): {e}")
                raise e

        
        # Final cleanup after all attempts
        try:
            if temp_session:
                temp_session.close()
                
            logger.debug(f"Cleaned up separate session for call {index}")
        except Exception as e:
            logger.warning(f"Error in final cleanup for call {index}: {e}")
        
        # This should never be reached due to the return statements in the try block
        return BatchCallResult(
            success=False,
            error=RuntimeError(f"Unexpected end of retry loop for call {index}"),
            execution_time=time.time() - start_time,
            call_index=index
        )

    def _authenticate_session(self, session: 'requests.Session', original_client: Any, index: int) -> None:
        """Authenticate a session independently without touching the main client."""
        url = f"{original_client.base_url}/entity/auth/login"
        
        for login_attempt in range(2):
            try:
                response = session.post(
                    url, 
                    json=original_client._login_payload, 
                    verify=original_client.verify_ssl,
                    timeout=original_client.timeout
                )
                
                if response.status_code == 401:
                    raise Exception("Invalid credentials")
                
                response.raise_for_status()
                logger.debug(f"Session authentication successful for call {index}")
                return
                
            except Exception as login_error:
                logger.warning(f"Login attempt {login_attempt + 1} failed for call {index}: {login_error}")
                if login_attempt < 1:  # Only wait if not the last attempt
                    time.sleep(0.5)
                else:
                    raise login_error

    def _logout_session(self, session: 'requests.Session', original_client: Any) -> None:
        """Logout a session independently."""
        try:
            url = f"{original_client.base_url}/entity/auth/logout"
            response = session.post(url, verify=original_client.verify_ssl, timeout=original_client.timeout)
            session.cookies.clear()
        except Exception as e:
            logger.debug(f"Non-critical logout error: {e}")

    def _execute_call_with_session(self, call: CallableWrapper, session: 'requests.Session', original_client: Any) -> Any:
        """Execute a call using a specific session without modifying the main client."""
        # We need to temporarily replace the session for the duration of the call only
        original_session = original_client.session
        original_logged_in = original_client._logged_in
        
        try:
            # Temporarily use the authenticated session
            original_client.session = session
            original_client._logged_in = True  # We know this session is authenticated
            
            # Execute the call
            result = call.execute()
            return result
            
        finally:
            # Immediately restore original state
            original_client.session = original_session
            original_client._logged_in = original_logged_in
    
    def _get_original_client_from_call(self, call: CallableWrapper) -> Any:
        """
        Extract the original AcumaticaClient from the callable wrapper.
        
        Args:
            call: The CallableWrapper to extract client from
            
        Returns:
            Original AcumaticaClient instance or None
        """
        # Try to get the client from the function's __self__ attribute (bound method)
        if hasattr(call.func, '__self__'):
            service_instance = call.func.__self__
            if hasattr(service_instance, '_client'):
                return service_instance._client
        
        return None
    
    def _create_separate_http_session(self, original_client: Any) -> 'requests.Session':
        """
        Create a separate HTTP session with the same configuration as the original.
        
        Args:
            original_client: The original client to copy session configuration from
            
        Returns:
            New requests.Session configured like the original
        """
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        # Create new session
        new_session = requests.Session()
        
        # Copy configuration from original client's session creation logic with more aggressive settings
        retry_strategy = Retry(
            total=original_client._max_retries,
            backoff_factor=original_client._backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"],
            raise_on_status=False  # Don't raise exceptions, let our code handle them
        )
        
        adapter = HTTPAdapter(
            pool_connections=original_client._pool_connections,
            pool_maxsize=original_client._pool_maxsize,
            max_retries=retry_strategy,
            pool_block=False  # Don't block if pool is full
        )
        
        new_session.mount("http://", adapter)
        new_session.mount("https://", adapter)
        
        # Copy headers from original session but ensure fresh cookies
        new_session.headers.update(original_client.session.headers)
        new_session.cookies.clear()  # Start with fresh cookies
        
        # Set more aggressive timeouts for batch operations
        new_session.timeout = (10, 30)  # (connect_timeout, read_timeout)
        
        return new_session
    
    def get_results_tuple(self) -> Tuple[Any, ...]:
        """Get results as a tuple for unpacking assignment."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before accessing results")
        
        results = []
        for i, batch_result in enumerate(self.results):
            if batch_result.success:
                results.append(batch_result.result)
            else:
                if self.return_exceptions:
                    results.append(batch_result.error)
                else:
                    raise AcumaticaBatchError(
                        f"Call {i} failed: {batch_result.error}",
                        failed_operations=[{
                            "index": i,
                            "error": str(batch_result.error),
                            "operation": getattr(self.calls[i], 'method_name', 'unknown')
                        }]
                    )
        
        return tuple(results)
    
    def get_successful_results(self) -> List[Any]:
        """Get only the results from successful calls."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before accessing results")
        
        return [r.result for r in self.results if r.success]
    
    def get_failed_calls(self) -> List[Tuple[int, CallableWrapper, Exception]]:
        """Get information about failed calls."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before accessing results")
        
        return [
            (r.call_index, self.calls[r.call_index], r.error)
            for r in self.results if not r.success
        ]
    
    def retry_failed_calls(self, max_concurrent: Optional[int] = None) -> 'BatchCall':
        """Create a new BatchCall with only the failed calls from this batch."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before retrying failed calls")
        
        failed_calls = [self.calls[i] for i, r in enumerate(self.results) if not r.success]
        
        if not failed_calls:
            logger.info("No failed calls to retry")
            return BatchCall()  # Empty batch
        
        logger.info(f"Creating retry batch with {len(failed_calls)} failed calls")
        return BatchCall(
            *failed_calls,
            max_concurrent=max_concurrent or self.max_concurrent,
            timeout=self.timeout,
            fail_fast=self.fail_fast,
            return_exceptions=self.return_exceptions,
            progress_callback=self.progress_callback
        )
    
    def print_summary(self) -> None:
        """Print a summary of batch execution results."""
        if not self.executed:
            print("BatchCall not yet executed")
            return
        
        print(f"\nSeparate HTTP Session Batch Execution Summary")
        print(f"=" * 50)
        print(f"Total Calls: {self.stats.total_calls}")
        print(f"Successful: {self.stats.successful_calls}")
        print(f"Failed: {self.stats.failed_calls}")
        print(f"Success Rate: {(self.stats.successful_calls / self.stats.total_calls * 100):.1f}%")
        print(f"Total Time: {self.stats.total_time:.2f}s")
        print(f"Average Call Time: {self.stats.average_call_time:.3f}s")
        print(f"Fastest Call: {self.stats.min_call_time:.3f}s")
        print(f"Slowest Call: {self.stats.max_call_time:.3f}s")
        print(f"Max Concurrent HTTP Sessions: {self.stats.concurrency_level}")
        
        # Show failed calls
        failed_calls = self.get_failed_calls()
        if failed_calls:
            print(f"\nFailed Calls:")
            for index, call, error in failed_calls:
                print(f"  {index}: - {type(error).__name__}: {error}")
    
    def __len__(self) -> int:
        """Return the number of calls in this batch."""
        return len(self.calls)
    
    def __getitem__(self, index: int) -> BatchCallResult:
        """Get a specific result by index."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before accessing results")
        return self.results[index]
    
    def __iter__(self):
        """Iterate over results."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before iterating results")
        return iter(self.results)
    
    def __repr__(self) -> str:
        if self.executed:
            return (f"BatchCall({len(self.calls)} calls, "
                   f"{self.stats.successful_calls} successful, executed with separate HTTP sessions)")
        else:
            return f"BatchCall({len(self.calls)} calls, separate HTTP sessions, not executed)"


# Keep the same helper functions
def batch_call(*calls, **kwargs) -> BatchCall:
    """Convenience function to create and execute a BatchCall."""
    batch = BatchCall(*calls, **kwargs)
    return batch

def create_batch_from_ids(service, entity_ids: List[str], method_name: str = 'get_by_id', **method_kwargs) -> BatchCall:
    """Helper function to create a batch call for fetching multiple entities by ID."""
    method = getattr(service, method_name)
    calls = [CallableWrapper(method, entity_id, **method_kwargs) for entity_id in entity_ids]
    return BatchCall(*calls)

def create_batch_from_filters(service, filters: List[Any], method_name: str = 'get_list', **method_kwargs) -> BatchCall:
    """Helper function to create a batch call for multiple filtered queries."""
    method = getattr(service, method_name)
    calls = [CallableWrapper(method, options=filter_obj, **method_kwargs) for filter_obj in filters]
    return BatchCall(*calls)