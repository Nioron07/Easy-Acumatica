"""Pooled-session batch execution.

For N calls and ``max_concurrent=K``, the batch spawns
``min(K, N)`` worker threads. Each worker authenticates **one** HTTP
session and reuses it for every call it pulls off a shared queue. So 10
calls with ``max_concurrent=5`` produce exactly 5 logins (not 10), each
session running ~2 calls back-to-back. Service calls execute under the
worker's session via the client's thread-local session override; lambdas
and other non-service callables run without a session.
"""

import concurrent.futures
import logging
import queue
import threading
import time
from dataclasses import dataclass
from typing import Any, Callable, List, Optional, Tuple, Union

import requests
from requests.adapters import HTTPAdapter

from .exceptions import AcumaticaBatchError

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
        self.method_name = getattr(
            func, "__name__", "unknown"
        )  # Add method_name attribute

    def execute(self) -> Any:
        """Execute the wrapped function call synchronously."""
        return self.func(*self.args, **self.kwargs)


class BatchCall:
    """Execute multiple API calls concurrently using a pool of authenticated sessions.

    For N calls and ``max_concurrent=K``, the batch spawns ``min(K, N)``
    worker threads. Each worker authenticates one ``requests.Session`` and
    reuses it for every call it processes off a shared queue, so the
    server sees roughly N/K calls per session and only ``min(K, N)``
    /auth/login posts in total. Workers run in parallel; results come
    back ordered by submission index.
    """

    def __init__(
        self,
        *calls: Union[CallableWrapper, Callable],
        max_concurrent: Optional[int] = None,
        timeout: Optional[float] = None,
        fail_fast: bool = False,
        return_exceptions: bool = True,
        progress_callback: Optional[Callable[[int, int], None]] = None,
    ):
        """Initialize a batch call with separate HTTP sessions execution."""
        self.calls: List[CallableWrapper] = []
        self.max_concurrent = max_concurrent or 5
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
                raise TypeError(
                    f"Invalid call type: {type(call)}. Must be callable or CallableWrapper."
                )

        # State tracking
        self.results: List[BatchCallResult] = []
        self.stats: BatchCallStats = BatchCallStats()
        self.executed: bool = False

        logger.debug(
            f"Created BatchCall with {len(self.calls)} calls (pooled sessions)"
        )

    def execute(self) -> Tuple[Any, ...]:
        """Execute the batch using a pool of authenticated worker sessions.

        ``min(max_concurrent, len(calls))`` workers run in parallel; each
        owns one session, pulls calls off a shared queue, and runs them
        sequentially under that session. Results are stored ordered by
        the original submission index.
        """
        if self.executed:
            logger.warning("BatchCall already executed, returning cached results")
            return self.get_results_tuple()

        if not self.calls:
            self.stats = BatchCallStats(concurrency_level=0)
            self.executed = True
            return tuple()

        start_time = time.time()
        self.results = [
            BatchCallResult(success=False, call_index=i) for i in range(len(self.calls))
        ]

        worker_count = min(self.max_concurrent, len(self.calls))
        work_queue: "queue.Queue[Tuple[int, CallableWrapper]]" = queue.Queue()
        for i, call in enumerate(self.calls):
            work_queue.put((i, call))

        stop_event = threading.Event()
        progress_lock = threading.Lock()
        progress_state = {
            "completed": 0,
            "first_error": None,
            "first_error_index": None,
        }

        logger.info(
            f"Starting pooled-session batch: {len(self.calls)} calls, "
            f"{worker_count} worker session(s)"
        )

        timed_out = False
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=worker_count
        ) as executor:
            worker_futures = [
                executor.submit(
                    self._worker, work_queue, stop_event, progress_lock, progress_state
                )
                for _ in range(worker_count)
            ]
            try:
                for fut in concurrent.futures.as_completed(
                    worker_futures, timeout=self.timeout
                ):
                    fut.result()  # surface any unexpected worker exception
            except concurrent.futures.TimeoutError:
                timed_out = True
                stop_event.set()
                logger.error(f"Batch execution timed out after {self.timeout} seconds")

        if timed_out and not self.return_exceptions:
            raise concurrent.futures.TimeoutError(
                f"Batch execution timed out after {self.timeout} seconds"
            )

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
            concurrency_level=worker_count,
        )

        self.executed = True

        logger.info(
            f"Pooled-session batch completed in {total_time:.2f}s: "
            f"{successful}/{len(self.calls)} successful"
        )

        first_error = progress_state["first_error"]
        if self.fail_fast and first_error is not None:
            failed_operations = [
                {
                    "index": r.call_index,
                    "error": str(r.error),
                    "operation": getattr(
                        self.calls[r.call_index], "method_name", "unknown"
                    ),
                }
                for r in self.results
                if not r.success and r.error is not None
            ]
            raise AcumaticaBatchError(
                f"Batch execution failed (fail_fast=True) at call "
                f"{progress_state['first_error_index']}: {first_error}",
                failed_operations=failed_operations,
            )

        return self.get_results_tuple()

    def _worker(
        self,
        work_queue: "queue.Queue",
        stop_event: threading.Event,
        progress_lock: threading.Lock,
        progress_state: dict,
    ) -> None:
        """One pooled worker: lazily authenticates a single session on its
        first service-bound call and reuses it for every subsequent call
        it pulls off the shared queue. Logs out and closes when the queue
        empties or ``stop_event`` is set.
        """
        own_client: Any = None
        own_session: Optional[requests.Session] = None
        try:
            while not stop_event.is_set():
                try:
                    index, call = work_queue.get_nowait()
                except queue.Empty:
                    return

                call_start = time.time()
                client_from_call = self._get_original_client_from_call(call)

                try:
                    if client_from_call is None:
                        # Lambda / non-service callable - no session needed.
                        result = call.execute()
                    else:
                        if own_session is None:
                            own_client = client_from_call
                            own_session = self._create_separate_http_session(own_client)
                            self._authenticate_session(own_session, own_client, index)
                        elif own_client is not client_from_call:
                            # Rare: a call from a different client mid-batch.
                            # Tear down the current session and re-auth so
                            # the override matches the call's client.
                            try:
                                self._logout_session(own_session, own_client)
                            finally:
                                try:
                                    own_session.close()
                                except Exception:
                                    pass
                            own_client = client_from_call
                            own_session = self._create_separate_http_session(own_client)
                            self._authenticate_session(own_session, own_client, index)
                        result = self._execute_call_with_session(
                            call, own_session, own_client
                        )

                    self.results[index] = BatchCallResult(
                        success=True,
                        result=result,
                        execution_time=time.time() - call_start,
                        call_index=index,
                    )
                except Exception as e:
                    self.results[index] = BatchCallResult(
                        success=False,
                        error=e,
                        execution_time=time.time() - call_start,
                        call_index=index,
                    )
                    if self.fail_fast:
                        with progress_lock:
                            if progress_state["first_error"] is None:
                                progress_state["first_error"] = e
                                progress_state["first_error_index"] = index
                        stop_event.set()

                with progress_lock:
                    progress_state["completed"] += 1
                    completed = progress_state["completed"]
                if self.progress_callback:
                    try:
                        self.progress_callback(completed, len(self.calls))
                    except Exception as cb_err:
                        logger.warning(f"Progress callback failed: {cb_err}")
        finally:
            if own_session is not None:
                try:
                    self._logout_session(own_session, own_client)
                except Exception as e:
                    logger.debug(f"Worker logout failed: {e}")
                try:
                    own_session.close()
                except Exception as e:
                    logger.debug(f"Worker session close failed: {e}")

    def _authenticate_session(
        self, session: "requests.Session", original_client: Any, index: int
    ) -> None:
        """Authenticate a session independently without touching the main client.

        Concurrent logins are naturally bounded by the worker pool size
        (``min(max_concurrent, len(calls))``); no separate semaphore is
        needed because each worker logs in at most once.
        """
        url = f"{original_client.base_url}/entity/auth/login"
        for login_attempt in range(2):
            try:
                response = session.post(
                    url,
                    json=original_client._login_payload,
                    verify=original_client.verify_ssl,
                    timeout=original_client.timeout,
                )
                if response.status_code == 401:
                    raise Exception("Invalid credentials")
                response.raise_for_status()
                logger.debug(
                    f"Worker session authentication successful (first call {index})"
                )
                return
            except Exception as login_error:
                logger.warning(
                    f"Login attempt {login_attempt + 1} failed (worker first call {index}): {login_error}"
                )
                if login_attempt < 1:
                    time.sleep(0.5)
                else:
                    raise

    def _logout_session(
        self, session: "requests.Session", original_client: Any
    ) -> None:
        """Logout a session independently."""
        try:
            url = f"{original_client.base_url}/entity/auth/logout"
            response = session.post(
                url, verify=original_client.verify_ssl, timeout=original_client.timeout
            )
            session.cookies.clear()
        except Exception as e:
            logger.debug(f"Non-critical logout error: {e}")

    def _execute_call_with_session(
        self, call: CallableWrapper, session: "requests.Session", original_client: Any
    ) -> Any:
        """Execute a call using a specific session without mutating shared client state.

        The previous implementation swapped ``original_client.session`` and
        ``_logged_in`` directly, which raced across worker threads (and any
        foreground caller using the same client mid-batch). We now route
        the override through a thread-local context manager exposed on the
        client, so each worker sees its own session while the shared
        attributes stay untouched.
        """
        with original_client._use_thread_session(session, logged_in=True):
            return call.execute()

    def _get_original_client_from_call(self, call: CallableWrapper) -> Any:
        """
        Extract the original AcumaticaClient from the callable wrapper.

        Args:
            call: The CallableWrapper to extract client from

        Returns:
            Original AcumaticaClient instance or None
        """
        # Try to get the client from the function's __self__ attribute (bound method)
        if hasattr(call.func, "__self__"):
            service_instance = call.func.__self__
            if hasattr(service_instance, "_client"):
                return service_instance._client

        return None

    def _create_separate_http_session(self, original_client: Any) -> "requests.Session":
        """
        Create a separate HTTP session with the same configuration as the original.
        """
        new_session = requests.Session()

        # No automatic HTTP retry - surface the server's actual error to the
        # caller instead of wrapping it in a "too many 5xx" RetryError.
        adapter = HTTPAdapter(
            pool_connections=original_client._pool_connections,
            pool_maxsize=original_client._pool_maxsize,
            max_retries=0,
            pool_block=False,
        )
        new_session.mount("http://", adapter)
        new_session.mount("https://", adapter)

        # Copy headers from original session but ensure fresh cookies. Note
        # that ``requests.Session`` has no ``timeout`` attribute - per-call
        # timeouts are set by ``_request`` in core.py, so we don't try to
        # set one here.
        new_session.headers.update(original_client.session.headers)
        new_session.cookies.clear()
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
                        failed_operations=[
                            {
                                "index": i,
                                "error": str(batch_result.error),
                                "operation": getattr(
                                    self.calls[i], "method_name", "unknown"
                                ),
                            }
                        ],
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
            for r in self.results
            if not r.success
        ]

    def retry_failed_calls(self, max_concurrent: Optional[int] = None) -> "BatchCall":
        """Create a new BatchCall with only the failed calls from this batch."""
        if not self.executed:
            raise RuntimeError("Batch must be executed before retrying failed calls")

        failed_calls = [
            self.calls[i] for i, r in enumerate(self.results) if not r.success
        ]

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
            progress_callback=self.progress_callback,
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
        print(
            f"Success Rate: {(self.stats.successful_calls / self.stats.total_calls * 100):.1f}%"
        )
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
            return (
                f"BatchCall({len(self.calls)} calls, "
                f"{self.stats.successful_calls} successful, executed with separate HTTP sessions)"
            )
        else:
            return f"BatchCall({len(self.calls)} calls, separate HTTP sessions, not executed)"


# Keep the same helper functions
def batch_call(*calls, **kwargs) -> BatchCall:
    """Convenience function to create and execute a BatchCall."""
    batch = BatchCall(*calls, **kwargs)
    return batch


def create_batch_from_ids(
    service, entity_ids: List[str], method_name: str = "get_by_id", **method_kwargs
) -> BatchCall:
    """Helper function to create a batch call for fetching multiple entities by ID."""
    method = getattr(service, method_name)
    calls = [
        CallableWrapper(method, entity_id, **method_kwargs) for entity_id in entity_ids
    ]
    return BatchCall(*calls)


def create_batch_from_filters(
    service, filters: List[Any], method_name: str = "get_list", **method_kwargs
) -> BatchCall:
    """Helper function to create a batch call for multiple filtered queries."""
    method = getattr(service, method_name)
    calls = [
        CallableWrapper(method, options=filter_obj, **method_kwargs)
        for filter_obj in filters
    ]
    return BatchCall(*calls)
