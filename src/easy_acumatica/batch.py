"""Improved batch calling implementation that addresses the event loop issues
and provides better performance for synchronous HTTP requests."""

import asyncio
import threading
import time
import concurrent.futures
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
import logging

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
        self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        """Generate a human-readable description of this call."""
        func_name = getattr(self.func, '__name__', str(self.func))
        
        if hasattr(self.func, '__self__'):
            service_name = getattr(self.func.__self__, 'entity_name', 'Unknown')
            return f"{service_name}.{func_name}"
        
        return func_name
    
    def execute(self) -> Any:
        """Execute the wrapped function call synchronously."""
        return self.func(*self.args, **self.kwargs)
    
    def __repr__(self) -> str:
        return f"CallableWrapper({self.description})"

class BatchCall:
    """
    Execute multiple API calls concurrently using threading (better for sync HTTP).
    
    This implementation uses ThreadPoolExecutor instead of asyncio since the underlying
    requests are synchronous, which provides better performance and avoids event loop issues.
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
        """Initialize a batch call with threading-based execution."""
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
        
        logger.debug(f"Created BatchCall with {len(self.calls)} calls")
    
    def execute(self) -> Tuple[Any, ...]:
        """
        Execute all calls concurrently using ThreadPoolExecutor and return results as a tuple.
        
        This method uses threading instead of asyncio since the underlying HTTP requests
        are synchronous, providing better performance and avoiding event loop issues.
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
        
        logger.info(f"Starting threaded batch execution with {len(self.calls)} calls, max concurrent: {self.max_concurrent}")
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                # Submit all tasks
                future_to_index = {
                    executor.submit(self._execute_single_call, call, i): i
                    for i, call in enumerate(self.calls)
                }
                
                # Wait for completion with optional timeout
                completed_futures = concurrent.futures.as_completed(
                    future_to_index.keys(), 
                    timeout=self.timeout
                )
                
                completed_count = 0
                first_error = None
                
                for future in completed_futures:
                    index = future_to_index[future]
                    result = future.result()  # This will re-raise any exception
                    
                    self.results[index] = result
                    completed_count += 1
                    
                    # Progress callback
                    if self.progress_callback:
                        try:
                            self.progress_callback(completed_count, len(self.calls))
                        except Exception as e:
                            logger.warning(f"Progress callback failed: {e}")
                    
                    # Handle fail_fast
                    if self.fail_fast and not result.success and first_error is None:
                        first_error = result.error
                        # Cancel remaining futures
                        for remaining_future in future_to_index.keys():
                            remaining_future.cancel()
                        break
                
        except concurrent.futures.TimeoutError:
            logger.error(f"Batch execution timed out after {self.timeout} seconds")
            raise
        except Exception as e:
            logger.error(f"Batch execution failed: {e}")
            raise
        
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
            f"Threaded batch execution completed in {total_time:.2f}s: "
            f"{successful}/{len(self.calls)} successful"
        )
        
        # Handle fail_fast
        if self.fail_fast and first_error:
            from .exceptions import AcumaticaError
            raise AcumaticaError(f"Batch execution failed (fail_fast=True): {first_error}")
        
        return self.get_results_tuple()
    
    def _execute_single_call(self, call: CallableWrapper, index: int) -> BatchCallResult:
        """
        Execute a single call in a thread and return its result.
        
        Args:
            call: The call to execute
            index: Index of this call in the batch
            
        Returns:
            BatchCallResult with execution details
        """
        start_time = time.time()
        
        try:
            logger.debug(f"Executing call {index}: {call.description}")
            result = call.execute()
            execution_time = time.time() - start_time
            
            logger.debug(f"Call {index} completed successfully in {execution_time:.3f}s")
            return BatchCallResult(
                success=True,
                result=result,
                execution_time=execution_time,
                call_index=index
            )
        
        except Exception as e:
            execution_time = time.time() - start_time
            
            logger.debug(f"Call {index} failed after {execution_time:.3f}s: {e}")
            return BatchCallResult(
                success=False,
                error=e,
                execution_time=execution_time,
                call_index=index
            )
    
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
                    from .exceptions import AcumaticaError
                    raise AcumaticaError(
                        f"Call {i} ({self.calls[i].description}) failed: {batch_result.error}"
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
        
        print(f"\nThreaded Batch Execution Summary")
        print(f"=" * 50)
        print(f"Total Calls: {self.stats.total_calls}")
        print(f"Successful: {self.stats.successful_calls}")
        print(f"Failed: {self.stats.failed_calls}")
        print(f"Success Rate: {(self.stats.successful_calls / self.stats.total_calls * 100):.1f}%")
        print(f"Total Time: {self.stats.total_time:.2f}s")
        print(f"Average Call Time: {self.stats.average_call_time:.3f}s")
        print(f"Fastest Call: {self.stats.min_call_time:.3f}s")
        print(f"Slowest Call: {self.stats.max_call_time:.3f}s")
        print(f"Max Concurrent: {self.stats.concurrency_level}")
        
        # Show failed calls
        failed_calls = self.get_failed_calls()
        if failed_calls:
            print(f"\nFailed Calls:")
            for index, call, error in failed_calls:
                print(f"  {index}: {call.description} - {type(error).__name__}: {error}")
    
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
                   f"{self.stats.successful_calls} successful, executed)")
        else:
            return f"BatchCall({len(self.calls)} calls, not executed)"

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