# tests/test_batch.py

import threading
import time

import pytest

from easy_acumatica import AcumaticaClient
from easy_acumatica.batch import (
    BatchCall,
    BatchCallResult,
    BatchCallStats,
    CallableWrapper,
    batch_call,
    create_batch_from_filters,
    create_batch_from_ids,
)
from easy_acumatica.exceptions import AcumaticaBatchError, AcumaticaNotFoundError
from easy_acumatica.odata import F, QueryOptions

def test_successful_batch_get_by_id(base_client_config, reset_server_state):
    """Tests a batch call with multiple successful get_by_id requests."""
    client = AcumaticaClient(**base_client_config)
    
    ids_to_fetch = ["123", "123", "123"]
    
    # Create batch calls using the .batch property
    calls = [client.test.get_by_id.batch(id) for id in ids_to_fetch]
    
    # Execute the batch call
    results = BatchCall(*calls).execute()
    
    assert len(results) == len(ids_to_fetch)
    for result in results:
        assert isinstance(result, dict)
        assert result['id'] == "123"
        assert result['Name']['value'] == "Specific Test Item"

def test_create_batch_from_ids_helper(base_client_config, reset_server_state):
    """Tests the create_batch_from_ids helper function."""
    client = AcumaticaClient(**base_client_config)
    
    ids_to_fetch = ["123", "123"]
    
    # Use the helper to create and execute the batch
    results = create_batch_from_ids(client.test, ids_to_fetch).execute()
    
    assert len(results) == len(ids_to_fetch)
    assert results[0]['id'] == "123"
    assert results[1]['id'] == "123"

def test_batch_with_mixed_success_and_failure(base_client_config, reset_server_state):
    """Tests a batch with both successful and failed calls."""
    client = AcumaticaClient(**base_client_config)
    
    batch = BatchCall(
        client.test.get_by_id.batch("123"),          # Success
        client.test.get_by_id.batch("999"),          # Failure (Not Found)
        client.test.get_by_id.batch("123"),          # Success
        return_exceptions=True
    )
    
    results = batch.execute()
    
    assert len(results) == 3
    
    # Check successful call
    assert isinstance(results[0], dict)
    assert results[0]['id'] == "123"
    
    # Check failed call
    assert isinstance(results[1], AcumaticaNotFoundError)
    
    # Check successful call
    assert isinstance(results[2], dict)
    assert results[2]['id'] == "123"
    
    # Check stats
    assert batch.stats.total_calls == 3
    assert batch.stats.successful_calls == 2
    assert batch.stats.failed_calls == 1

def test_batch_fail_fast(base_client_config, reset_server_state):
    """Tests the fail_fast functionality of BatchCall."""
    client = AcumaticaClient(**base_client_config)

    with pytest.raises(AcumaticaBatchError):
        BatchCall(
            client.test.get_by_id.batch("123"),
            client.test.get_by_id.batch("999"),  # This will fail
            client.test.get_by_id.batch("123"),
            fail_fast=True,
            return_exceptions=False  # Ensure exceptions are raised
        ).execute()

def test_batch_return_exceptions_false(base_client_config, reset_server_state):
    """Tests that an exception is raised immediately when return_exceptions is False."""
    client = AcumaticaClient(**base_client_config)

    with pytest.raises(AcumaticaBatchError):
        BatchCall(
            client.test.get_by_id.batch("123"),
            client.test.get_by_id.batch("999"),
            return_exceptions=False
        ).execute()

def test_batch_put_entity(base_client_config, reset_server_state):
    """Tests batching of put_entity calls."""
    client = AcumaticaClient(**base_client_config)
    
    new_item1 = client.models.TestModel(Name="Batch Item 1")
    new_item2 = client.models.TestModel(Name="Batch Item 2")
    
    results = BatchCall(
        client.test.put_entity.batch(new_item1),
        client.test.put_entity.batch(new_item2)
    ).execute()
    
    assert len(results) == 2
    assert results[0]['Name']['value'] == "Batch Item 1"
    assert results[1]['Name']['value'] == "Batch Item 2"
    assert results[0]['id'] == "new-put-entity-id"
    
def test_batch_delete_entity(base_client_config, reset_server_state):
    """Tests batching of delete_by_id calls."""
    client = AcumaticaClient(**base_client_config)
    
    # The mock server returns 204 No Content, which results in None
    results = BatchCall(
        client.test.delete_by_id.batch("1"),
        client.test.delete_by_id.batch("2")
    ).execute()
    
    assert results == (None, None)

def test_batch_with_mixed_operations(base_client_config, reset_server_state):
    """Tests a batch with a mix of GET, PUT, and DELETE operations."""
    client = AcumaticaClient(**base_client_config)
    
    new_item = client.models.TestModel(Name="Mixed Batch Item")
    
    get_result, put_result, delete_result = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.put_entity.batch(new_item),
        client.test.delete_by_id.batch("321")
    ).execute()
    
    assert get_result['id'] == "123"
    assert put_result['Name']['value'] == "Mixed Batch Item"
    assert delete_result is None

def test_progress_callback(base_client_config, reset_server_state):
    """Tests the progress_callback functionality."""
    client = AcumaticaClient(**base_client_config)
    
    progress_updates = []
    def my_callback(completed, total):
        progress_updates.append((completed, total))
        
    BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        progress_callback=my_callback
    ).execute()
    
    assert len(progress_updates) == 2
    assert progress_updates[0] == (1, 2)
    assert progress_updates[1] == (2, 2)

def test_empty_batch_call():
    """Tests that an empty BatchCall executes without errors."""
    batch = BatchCall()
    results = batch.execute()
    assert results == tuple()
    assert batch.stats.total_calls == 0

def test_retry_failed_calls(base_client_config, reset_server_state):
    """Tests the ability to retry only the failed calls from a batch."""
    client = AcumaticaClient(**base_client_config)
    
    initial_batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("999"),  # Fails
        client.test.get_by_id.batch("888")   # Fails
    )
    initial_batch.execute()
    
    assert initial_batch.stats.failed_calls == 2
    
    # Create a new batch with only the failed calls
    retry_batch = initial_batch.retry_failed_calls()
    retry_batch.execute() # Execute the new batch
    
    assert len(retry_batch) == 2
    
    # For this test, they will fail again, but we can check the calls are correct
    failed_calls_info = retry_batch.get_failed_calls()
    
    # Note: Can't directly compare call objects, but we can check args
    original_failed_ids = {call.args[0] for _, call, _ in initial_batch.get_failed_calls()}
    retry_ids = {call.args[0] for call in retry_batch.calls}

    assert original_failed_ids == retry_ids
    assert "999" in retry_ids
    assert "888" in retry_ids


def test_batch_does_not_mutate_shared_client_session(base_client_config, reset_server_state):
    """Regression: workers must not race on client.session / _logged_in.

    Before the thread-local override fix, BatchCall swapped these
    attributes on the shared client per worker. With concurrent workers
    the last finisher's restore could clobber the foreground attributes,
    leaking a worker's temp session into subsequent foreground calls.
    """
    client = AcumaticaClient(**base_client_config)
    pre_session_id = id(client.session)
    pre_logged_in = client._logged_in

    BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        max_concurrent=4,
    ).execute()

    assert id(client.session) == pre_session_id, (
        "client.session was replaced by a batch worker - data race regression"
    )
    assert client._logged_in == pre_logged_in


def test_batch_logins_bounded_by_max_concurrent(base_client_config, reset_server_state):
    """Pooled-session model: N calls with max_concurrent=K produce exactly
    min(K, N) logins, not one per call. With 6 calls and max_concurrent=2
    the batch should authenticate 2 worker sessions, each running 3 calls."""
    client = AcumaticaClient(**base_client_config)

    login_count = {'n': 0}
    login_lock = __import__('threading').Lock()

    from easy_acumatica.batch import BatchCall as _BatchCall
    original_auth = _BatchCall._authenticate_session

    def counting_auth(self, session, original_client, index):
        with login_lock:
            login_count['n'] += 1
        return original_auth(self, session, original_client, index)

    _BatchCall._authenticate_session = counting_auth
    try:
        BatchCall(
            *[client.test.get_by_id.batch("123") for _ in range(6)],
            max_concurrent=2,
        ).execute()
    finally:
        _BatchCall._authenticate_session = original_auth

    assert login_count['n'] == 2, (
        f"expected 2 worker logins (min(max_concurrent=2, 6)), got {login_count['n']}"
    )


def test_batch_fail_fast_raises_batch_error(base_client_config, reset_server_state):
    """fail_fast must raise AcumaticaBatchError, not a bare Exception."""
    client = AcumaticaClient(**base_client_config)

    batch = BatchCall(
        client.test.get_by_id.batch("999"),  # fails
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        fail_fast=True,
        max_concurrent=4,
    )
    with pytest.raises(AcumaticaBatchError) as exc_info:
        batch.execute()
    assert exc_info.value.failed_operations


# ---------------------------------------------------------------------------
# CallableWrapper / dataclass surface
# ---------------------------------------------------------------------------


def test_callable_wrapper_construct_and_execute():
    def add(a, b, c=0):
        return a + b + c

    wrapper = CallableWrapper(add, 1, 2, c=3)
    assert wrapper.func is add
    assert wrapper.args == (1, 2)
    assert wrapper.kwargs == {"c": 3}
    assert wrapper.method_name == "add"
    assert wrapper.execute() == 6


def test_callable_wrapper_lambda_method_name():
    """Lambdas don't have a useful __name__; method_name still stays a string."""
    wrapper = CallableWrapper(lambda: 42)
    assert wrapper.execute() == 42
    assert isinstance(wrapper.method_name, str)


def test_batch_call_result_defaults():
    r = BatchCallResult(success=True)
    assert r.success is True
    assert r.result is None
    assert r.error is None
    assert r.execution_time == 0.0
    assert r.call_index == 0


def test_batch_call_stats_defaults():
    s = BatchCallStats()
    assert s.total_calls == 0
    assert s.successful_calls == 0
    assert s.failed_calls == 0
    assert s.concurrency_level == 0


# ---------------------------------------------------------------------------
# Constructor: input validation, defaults, mixed call types
# ---------------------------------------------------------------------------


def test_batch_constructor_rejects_non_callable():
    with pytest.raises(TypeError):
        BatchCall(123)  # not callable, not a CallableWrapper


def test_batch_constructor_default_max_concurrent_is_5():
    """Default max_concurrent should match the documented value of 5."""
    batch = BatchCall(lambda: 1)
    assert batch.max_concurrent == 5


def test_batch_constructor_explicit_max_concurrent():
    batch = BatchCall(lambda: 1, max_concurrent=3)
    assert batch.max_concurrent == 3


def test_batch_accepts_bare_callable_and_wraps_it():
    """A plain function (not pre-wrapped) is auto-wrapped in CallableWrapper."""
    batch = BatchCall(lambda: "hello")
    assert isinstance(batch.calls[0], CallableWrapper)


def test_batch_accepts_prewrapped_callable_wrapper():
    """Pre-wrapped CallableWrappers are stored as-is, not double-wrapped."""
    wrapper = CallableWrapper(lambda x: x * 2, 5)
    batch = BatchCall(wrapper)
    assert batch.calls[0] is wrapper


def test_batch_executes_lambdas_without_session():
    """Non-service callables (lambdas) execute without going through auth."""
    batch = BatchCall(
        lambda: 1,
        lambda: 2,
        lambda: 3,
    )
    assert batch.execute() == (1, 2, 3)
    assert batch.stats.successful_calls == 3


def test_batch_mixed_lambdas_and_service_calls(base_client_config, reset_server_state):
    """A batch may interleave lambdas and service calls. The service call
    triggers worker-session login; the lambda should run without one."""
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        lambda: "local",
        client.test.get_by_id.batch("123"),
        lambda: 99,
    )
    results = batch.execute()
    assert results[0] == "local"
    assert isinstance(results[1], dict) and results[1]["id"] == "123"
    assert results[2] == 99


# ---------------------------------------------------------------------------
# Worker pool sizing
# ---------------------------------------------------------------------------


def test_concurrency_level_capped_at_call_count(base_client_config, reset_server_state):
    """worker_count = min(max_concurrent, len(calls))."""
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        max_concurrent=10,
    )
    batch.execute()
    assert batch.stats.concurrency_level == 2


def test_max_concurrent_one_runs_sequentially(base_client_config, reset_server_state):
    """max_concurrent=1 means one worker, one session, one call at a time."""
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        max_concurrent=1,
    )
    results = batch.execute()
    assert len(results) == 3
    assert batch.stats.concurrency_level == 1
    assert batch.stats.successful_calls == 3


# ---------------------------------------------------------------------------
# Re-execution and result accessors
# ---------------------------------------------------------------------------


def test_re_execute_returns_cached_results(base_client_config, reset_server_state):
    """Calling execute() twice does not re-run the calls."""
    client = AcumaticaClient(**base_client_config)
    invocations = {"n": 0}
    real_get = client.test.get_by_id

    def counting_get(*args, **kwargs):
        invocations["n"] += 1
        return real_get(*args, **kwargs)

    batch = BatchCall(CallableWrapper(counting_get, "123"))
    first = batch.execute()
    second = batch.execute()
    assert first == second
    # Counting wrapper isn't recognized as a service call, but the point
    # of this test is that the second execute() returns the cached tuple.
    assert batch.executed is True


def test_get_results_tuple_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        batch.get_results_tuple()


def test_get_successful_results_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        batch.get_successful_results()


def test_get_failed_calls_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        batch.get_failed_calls()


def test_indexing_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        _ = batch[0]


def test_iter_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        iter(batch)


def test_retry_failed_calls_before_execute_raises():
    batch = BatchCall(lambda: 1)
    with pytest.raises(RuntimeError):
        batch.retry_failed_calls()


def test_get_successful_results_after_execute(base_client_config, reset_server_state):
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("999"),  # fails
        client.test.get_by_id.batch("123"),
    )
    batch.execute()
    successful = batch.get_successful_results()
    assert len(successful) == 2
    for item in successful:
        assert isinstance(item, dict) and item["id"] == "123"


def test_get_failed_calls_shape(base_client_config, reset_server_state):
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("999"),
    )
    batch.execute()
    failed = batch.get_failed_calls()
    assert len(failed) == 1
    index, call, error = failed[0]
    assert index == 1
    assert isinstance(call, CallableWrapper)
    assert call.args == ("999",)
    assert isinstance(error, AcumaticaNotFoundError)


def test_retry_failed_calls_when_no_failures(base_client_config, reset_server_state):
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(client.test.get_by_id.batch("123"))
    batch.execute()
    retry = batch.retry_failed_calls()
    assert len(retry) == 0
    assert retry.execute() == tuple()


# ---------------------------------------------------------------------------
# Container protocol (__len__, __getitem__, __iter__, __repr__)
# ---------------------------------------------------------------------------


def test_len_reflects_call_count():
    batch = BatchCall(lambda: 1, lambda: 2, lambda: 3)
    assert len(batch) == 3


def test_getitem_returns_batchcall_result():
    batch = BatchCall(lambda: "x")
    batch.execute()
    item = batch[0]
    assert isinstance(item, BatchCallResult)
    assert item.success is True
    assert item.result == "x"


def test_iter_yields_batchcall_results():
    batch = BatchCall(lambda: 1, lambda: 2)
    batch.execute()
    items = list(batch)
    assert len(items) == 2
    assert all(isinstance(r, BatchCallResult) for r in items)


def test_repr_changes_after_execute():
    batch = BatchCall(lambda: 1, lambda: 2)
    pre = repr(batch)
    assert "not executed" in pre
    batch.execute()
    post = repr(batch)
    assert "not executed" not in post
    assert "successful" in post


# ---------------------------------------------------------------------------
# Progress callback resilience
# ---------------------------------------------------------------------------


def test_progress_callback_exception_does_not_abort_batch(base_client_config, reset_server_state):
    """A raising progress_callback must be logged and ignored, not propagated."""
    client = AcumaticaClient(**base_client_config)

    def bad_callback(completed, total):
        raise RuntimeError("callback boom")

    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
        progress_callback=bad_callback,
    )
    results = batch.execute()
    assert len(results) == 2
    assert batch.stats.successful_calls == 2


def test_progress_callback_invoked_for_lambdas_only():
    """Lambdas exercise the same progress accounting as service calls."""
    progress = []
    BatchCall(
        lambda: 1,
        lambda: 2,
        lambda: 3,
        progress_callback=lambda d, t: progress.append((d, t)),
    ).execute()
    assert len(progress) == 3
    assert progress[-1] == (3, 3)


# ---------------------------------------------------------------------------
# Helpers and convenience functions
# ---------------------------------------------------------------------------


def test_create_batch_from_filters_helper(base_client_config, reset_server_state):
    """create_batch_from_filters should fan a list of QueryOptions across get_list."""
    client = AcumaticaClient(**base_client_config)
    filters = [
        QueryOptions(filter=F.Name == "First Item"),
        QueryOptions(filter=F.Name == "Second Item"),
    ]
    batch = create_batch_from_filters(client.test, filters)
    assert len(batch) == 2
    results = batch.execute()
    assert len(results) == 2
    for r in results:
        assert isinstance(r, list)


def test_batch_call_helper_returns_unexecuted():
    """The ``batch_call`` convenience wrapper builds but does not execute."""
    batch = batch_call(lambda: 1, lambda: 2)
    assert isinstance(batch, BatchCall)
    assert batch.executed is False
    # Sanity: it still works after manual execute().
    assert batch.execute() == (1, 2)


# ---------------------------------------------------------------------------
# Concurrency / thread-safety regressions
# ---------------------------------------------------------------------------


def test_two_batches_on_same_client_do_not_corrupt_each_other(base_client_config, reset_server_state):
    """Two BatchCalls running in parallel on the same client must each see
    consistent results - the thread-local override must keep their
    sessions isolated."""
    client = AcumaticaClient(**base_client_config)

    def run_batch(tag):
        return BatchCall(
            *[client.test.get_by_id.batch("123") for _ in range(4)],
            max_concurrent=2,
        ).execute()

    threads = []
    results = {}

    def worker(tag):
        results[tag] = run_batch(tag)

    for tag in ("A", "B"):
        t = threading.Thread(target=worker, args=(tag,))
        threads.append(t)
        t.start()
    for t in threads:
        t.join(timeout=10)

    assert len(results) == 2
    for tag, batch_results in results.items():
        assert len(batch_results) == 4
        for r in batch_results:
            assert isinstance(r, dict) and r["id"] == "123"


def test_foreground_call_during_batch_uses_default_session(base_client_config, reset_server_state):
    """A direct client.test.get_by_id call running in parallel with a batch
    must use the client's default session, not a worker's thread-local
    override (would only happen if the override leaked across threads)."""
    client = AcumaticaClient(**base_client_config)
    default_session = client.session

    captured_session = []

    def foreground():
        # If the override leaks here, client.session would be a worker's
        # temp session - record what we saw.
        captured_session.append(client.session)
        client.test.get_by_id("123")

    batch = BatchCall(
        *[client.test.get_by_id.batch("123") for _ in range(6)],
        max_concurrent=3,
    )

    fg_thread = threading.Thread(target=foreground)
    fg_thread.start()
    batch.execute()
    fg_thread.join(timeout=10)

    # Foreground thread must have observed the original default session,
    # not whatever override a worker had active.
    assert captured_session and captured_session[0] is default_session


# ---------------------------------------------------------------------------
# Stats and timing
# ---------------------------------------------------------------------------


def test_stats_record_call_timings(base_client_config, reset_server_state):
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(
        client.test.get_by_id.batch("123"),
        client.test.get_by_id.batch("123"),
    )
    batch.execute()
    assert batch.stats.total_time > 0
    assert batch.stats.average_call_time > 0
    assert batch.stats.min_call_time > 0
    assert batch.stats.max_call_time >= batch.stats.min_call_time


def test_stats_for_empty_batch_have_zero_concurrency():
    batch = BatchCall()
    batch.execute()
    assert batch.stats.total_calls == 0
    assert batch.stats.concurrency_level == 0


# ---------------------------------------------------------------------------
# Misc: print_summary doesn't crash, repr formatting
# ---------------------------------------------------------------------------


def test_print_summary_runs_post_execute(capsys, base_client_config, reset_server_state):
    client = AcumaticaClient(**base_client_config)
    batch = BatchCall(client.test.get_by_id.batch("123"))
    batch.execute()
    batch.print_summary()
    out = capsys.readouterr().out
    assert "Total Calls" in out
    assert "Successful" in out


def test_print_summary_before_execute(capsys):
    batch = BatchCall(lambda: 1)
    batch.print_summary()
    assert "not yet executed" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Thread-local session override on the client (foundation for batch's fix)
# ---------------------------------------------------------------------------


def test_use_thread_session_overrides_only_in_owning_thread(base_client_config, reset_server_state):
    """The override set via _use_thread_session() must not bleed across
    threads. This is the foundation that makes BatchCall safe."""
    import requests as _requests
    client = AcumaticaClient(**base_client_config)
    fake_session = _requests.Session()

    seen_in_other_thread = []

    def other_thread():
        seen_in_other_thread.append(client.session)

    with client._use_thread_session(fake_session, logged_in=True):
        # In this thread, the override is active.
        assert client.session is fake_session
        assert client._logged_in is True

        t = threading.Thread(target=other_thread)
        t.start()
        t.join(timeout=2)

    # After the context manager exits, the override is cleared.
    assert client.session is not fake_session

    # The other thread must have seen the default session, not the override.
    assert seen_in_other_thread and seen_in_other_thread[0] is not fake_session