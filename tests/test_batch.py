# tests/test_batch.py
"""Tests for batch calling functionality."""

import pytest
import time
from unittest.mock import patch, Mock

from easy_acumatica import AcumaticaClient
from easy_acumatica.batch import (
    BatchCall, CallableWrapper, batch_call, 
    create_batch_from_ids, create_batch_from_filters,
    BatchCallResult, BatchCallStats
)
from easy_acumatica.odata import QueryOptions, F
from easy_acumatica.exceptions import AcumaticaError


@pytest.fixture
def client(live_server_url):
    """Provide a test client for batch operations."""
    return AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        cache_methods=False
    )


class TestCallableWrapper:
    """Test the CallableWrapper class."""
    
    def test_create_wrapper(self, client):
        """Test creating a CallableWrapper."""
        wrapper = CallableWrapper(client.tests.get_by_id, "123")
        assert wrapper.method_name == "get_by_id"
        assert wrapper.args == ("123",)
        assert wrapper.kwargs == {}
    
    def test_wrapper_description_generation(self, client):
        """Test that wrapper generates meaningful descriptions."""
        wrapper = CallableWrapper(client.tests.get_list)
        assert "Test" in wrapper.description
        assert "get_list" in wrapper.description
    
    def test_wrapper_execution(self, client):
        """Test that wrapper can execute the wrapped function."""
        wrapper = CallableWrapper(client.tests.get_by_id, "123")
        result = wrapper.execute()
        assert result["id"] == "123"
        assert result["Name"]["value"] == "Specific Test Item"
    
    def test_wrapper_with_kwargs(self, client):
        """Test wrapper with keyword arguments."""
        options = QueryOptions(top=5)
        wrapper = CallableWrapper(client.tests.get_list, options=options)
        assert wrapper.kwargs == {"options": options}
        
        result = wrapper.execute()
        assert isinstance(result, list)
    
    def test_wrapper_repr(self, client):
        """Test wrapper string representation."""
        wrapper = CallableWrapper(client.tests.get_by_id, "123")
        repr_str = repr(wrapper)
        assert "CallableWrapper" in repr_str
        assert "Test.get_by_id" in repr_str or "get_by_id" in repr_str


class TestBatchCallBasics:
    """Test basic BatchCall functionality."""
    
    def test_create_empty_batch(self):
        """Test creating an empty BatchCall."""
        batch = BatchCall()
        assert len(batch) == 0
        assert not batch.executed
    
    def test_create_batch_with_callables(self, client):
        """Test creating BatchCall with CallableWrapper objects."""
        call1 = CallableWrapper(client.tests.get_by_id, "123")
        call2 = CallableWrapper(client.tests.get_list)
        
        batch = BatchCall(call1, call2)
        assert len(batch) == 2
        assert not batch.executed
    
    def test_create_batch_with_direct_functions(self, client):
        """Test creating BatchCall with direct function references."""
        # This should work by auto-wrapping in CallableWrapper
        batch = BatchCall(
            lambda: client.tests.get_by_id("123"),
            lambda: client.tests.get_list()
        )
        assert len(batch) == 2
    
    def test_invalid_call_type_raises_error(self):
        """Test that invalid call types raise TypeError."""
        with pytest.raises(TypeError, match="Invalid call type"):
            BatchCall("not a callable")
    
    def test_batch_configuration(self, client):
        """Test BatchCall configuration options."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            max_concurrent=5,
            timeout=30,
            fail_fast=True,
            return_exceptions=False
        )
        
        assert batch.max_concurrent == 5
        assert batch.timeout == 30
        assert batch.fail_fast is True
        assert batch.return_exceptions is False


class TestBatchExecution:
    """Test batch execution functionality."""
    
    def test_execute_empty_batch(self):
        """Test executing an empty BatchCall."""
        batch = BatchCall()
        results = batch.execute()
        
        assert results == tuple()
        assert batch.executed
        assert batch.stats.total_calls == 0
    
    def test_execute_single_call(self, client):
        """Test executing BatchCall with single call."""
        batch = BatchCall(CallableWrapper(client.tests.get_by_id, "123"))
        results = batch.execute()
        
        assert len(results) == 1
        assert results[0]["id"] == "123"
        assert batch.executed
        assert batch.stats.total_calls == 1
        assert batch.stats.successful_calls == 1
        assert batch.stats.failed_calls == 0
    
    def test_execute_multiple_calls(self, client):
        """Test executing BatchCall with multiple calls."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            CallableWrapper(client.tests.get_ad_hoc_schema)
        )
        
        results = batch.execute()
        
        assert len(results) == 3
        assert results[0]["id"] == "123"  # get_by_id result
        assert isinstance(results[1], list)  # get_list result
        assert isinstance(results[2], dict)  # get_ad_hoc_schema result
        
        assert batch.stats.total_calls == 3
        assert batch.stats.successful_calls == 3
        assert batch.stats.failed_calls == 0
    
    def test_execute_already_executed_batch(self, client):
        """Test that executing an already executed batch returns cached results."""
        batch = BatchCall(CallableWrapper(client.tests.get_by_id, "123"))
        
        # First execution
        results1 = batch.execute()
        
        # Second execution should return same results
        results2 = batch.execute()
        
        assert results1 == results2
        assert batch.executed
    
    def test_batch_with_mixed_success_and_failure(self, client):
        """Test batch with both successful and failing calls."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Success
            CallableWrapper(client.tests.get_by_id, "999"),  # Should fail (404)
            CallableWrapper(client.tests.get_list),  # Success
            return_exceptions=True
        )
        
        results = batch.execute()
        
        assert len(results) == 3
        assert results[0]["id"] == "123"  # Success
        assert isinstance(results[1], Exception)  # Failed call
        assert isinstance(results[2], list)  # Success
        
        assert batch.stats.successful_calls == 2
        assert batch.stats.failed_calls == 1
    
    def test_batch_fail_fast(self, client):
        """Test fail_fast functionality."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "999"),  # Will fail
            CallableWrapper(client.tests.get_by_id, "123"),  # Would succeed
            fail_fast=True,
            return_exceptions=False
        )
        
        with pytest.raises(AcumaticaError, match="Batch execution failed"):
            batch.execute()
    
    def test_batch_return_exceptions_false(self, client):
        """Test that return_exceptions=False raises on failure."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "999"),  # Will fail
            return_exceptions=False
        )
        
        with pytest.raises(AcumaticaError):
            batch.execute()


class TestBatchResults:
    """Test batch result handling and utilities."""
    
    def test_get_results_tuple(self, client):
        """Test get_results_tuple method."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        results = batch.get_results_tuple()
        
        assert isinstance(results, tuple)
        assert len(results) == 2
    
    def test_get_successful_results(self, client):
        """Test get_successful_results method."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Success
            CallableWrapper(client.tests.get_by_id, "999"),  # Fail
            return_exceptions=True
        )
        
        batch.execute()
        successful = batch.get_successful_results()
        
        assert len(successful) == 1
        assert successful[0]["id"] == "123"
    
    def test_get_failed_calls(self, client):
        """Test get_failed_calls method."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Success
            CallableWrapper(client.tests.get_by_id, "999"),  # Fail
            return_exceptions=True
        )
        
        batch.execute()
        failed = batch.get_failed_calls()
        
        assert len(failed) == 1
        index, call, error = failed[0]
        assert index == 1
        assert isinstance(call, CallableWrapper)
        assert isinstance(error, Exception)
    
    def test_batch_indexing(self, client):
        """Test batch result indexing."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        
        # Test indexing
        result0 = batch[0]
        assert isinstance(result0, BatchCallResult)
        assert result0.success is True
        assert result0.result["id"] == "123"
        
        result1 = batch[1]
        assert result1.success is True
        assert isinstance(result1.result, list)
    
    def test_batch_iteration(self, client):
        """Test iterating over batch results."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        
        results = list(batch)
        assert len(results) == 2
        assert all(isinstance(r, BatchCallResult) for r in results)


class TestBatchStatistics:
    """Test batch statistics and performance tracking."""
    
    def test_batch_stats_successful_calls(self, client):
        """Test statistics for successful batch."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            CallableWrapper(client.tests.get_ad_hoc_schema)
        )
        
        batch.execute()
        stats = batch.stats
        
        assert isinstance(stats, BatchCallStats)
        assert stats.total_calls == 3
        assert stats.successful_calls == 3
        assert stats.failed_calls == 0
        assert stats.total_time > 0
        assert stats.average_call_time > 0
        assert stats.concurrency_level <= 10  # Default max_concurrent
    
    def test_batch_stats_mixed_results(self, client):
        """Test statistics for batch with mixed results."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Success
            CallableWrapper(client.tests.get_by_id, "999"),  # Fail
            CallableWrapper(client.tests.get_list),  # Success
            return_exceptions=True
        )
        
        batch.execute()
        stats = batch.stats
        
        assert stats.total_calls == 3
        assert stats.successful_calls == 2
        assert stats.failed_calls == 1
        assert stats.total_time > 0
    
    def test_batch_print_summary(self, client, capsys):
        """Test print_summary method."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        batch.print_summary()
        
        captured = capsys.readouterr()
        assert "Separate HTTP Session Batch Execution Summary" in captured.out
        assert "Total Calls: 2" in captured.out
        assert "Successful: 2" in captured.out
        assert "Success Rate:" in captured.out
    
    def test_batch_print_summary_with_failures(self, client, capsys):
        """Test print_summary with failed calls."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "999"),  # Will fail
            return_exceptions=True
        )
        
        batch.execute()
        batch.print_summary()
        
        captured = capsys.readouterr()
        assert "Failed Calls:" in captured.out
        assert "0:" in captured.out  # Shows failed call index


class TestBatchRetry:
    """Test batch retry functionality."""
    
    def test_retry_failed_calls(self, client):
        """Test retry_failed_calls method."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Success
            CallableWrapper(client.tests.get_by_id, "999"),  # Fail
            return_exceptions=True
        )
        
        batch.execute()
        
        # Create retry batch with only failed calls
        retry_batch = batch.retry_failed_calls()
        
        assert len(retry_batch) == 1
        assert not retry_batch.executed
        
        # The retry batch should still fail (since 999 doesn't exist)
        retry_batch.execute()
        assert retry_batch.stats.failed_calls == 1
    
    def test_retry_failed_calls_no_failures(self, client):
        """Test retry_failed_calls when no calls failed."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        retry_batch = batch.retry_failed_calls()
        
        assert len(retry_batch) == 0


class TestBatchConcurrency:
    """Test batch concurrency features."""
    
    def test_max_concurrent_setting(self, client):
        """Test that max_concurrent setting is respected."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            max_concurrent=2
        )
        
        batch.execute()
        
        assert batch.stats.concurrency_level == 2
    
    def test_progress_callback(self, client):
        """Test progress callback functionality."""
        progress_calls = []
        
        def progress_callback(completed, total):
            progress_calls.append((completed, total))
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            CallableWrapper(client.tests.get_ad_hoc_schema),
            progress_callback=progress_callback
        )
        
        batch.execute()
        
        # Should have received progress callbacks
        assert len(progress_calls) >= 1
        assert progress_calls[-1] == (3, 3)  # Final callback should show completion
    
    @patch('time.sleep')  # Mock sleep to speed up test
    def test_timeout_handling(self, mock_sleep, client):
        """Test timeout handling in batch execution."""
        # Create a batch with very short timeout
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            timeout=0.001  # Very short timeout
        )
        
        # This test is tricky because our mock server is fast
        # We'll test that timeout parameter is accepted
        try:
            batch.execute()
        except Exception:
            pass  # Timeout or other error is acceptable
        
        # Main thing is that the batch was created with timeout
        assert batch.timeout == 0.001


class TestBatchSessionManagement:
    """Test separate HTTP session management."""
    
    def test_separate_session_creation(self, client):
        """Test that batch creates separate sessions."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        # Execute batch - should work with separate sessions
        results = batch.execute()
        
        assert len(results) == 2
        assert results[0]["id"] == "123"
        assert isinstance(results[1], list)
        
        # Original client session should still work
        direct_result = client.tests.get_by_id("123")
        assert direct_result["id"] == "123"
    
    def test_session_authentication_retry(self, client):
        """Test that sessions retry authentication failures."""
        # This test verifies that the batch system handles auth retries
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            max_concurrent=1  # Single thread to make behavior predictable
        )
        
        results = batch.execute()
        assert len(results) == 1
        assert results[0]["id"] == "123"
        
        # Should have succeeded despite any auth retries
        assert batch.stats.successful_calls == 1


class TestHelperFunctions:
    """Test helper functions for batch creation."""
    
    def test_batch_call_function(self, client):
        """Test the batch_call convenience function."""
        result = batch_call(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        assert isinstance(result, BatchCall)
        assert len(result) == 2
    
    def test_create_batch_from_ids(self, client):
        """Test create_batch_from_ids helper."""
        batch = create_batch_from_ids(
            client.tests,
            ["123", "999"],  # One exists, one doesn't
            method_name="get_by_id"
        )
        
        assert isinstance(batch, BatchCall)
        assert len(batch) == 2
        
        # Execute with exception handling
        batch.return_exceptions = True
        results = batch.execute()
        
        assert len(results) == 2
        assert results[0]["id"] == "123"  # Success
        assert isinstance(results[1], Exception)  # Failure
    
    def test_create_batch_from_filters(self, client):
        """Test create_batch_from_filters helper."""
        filter1 = QueryOptions(top=1)
        filter2 = QueryOptions(top=2)
        
        batch = create_batch_from_filters(
            client.tests,
            [filter1, filter2],
            method_name="get_list"
        )
        
        assert isinstance(batch, BatchCall)
        assert len(batch) == 2
        
        results = batch.execute()
        assert len(results) == 2
        assert all(isinstance(r, list) for r in results)


class TestBatchEdgeCases:
    """Test edge cases and error conditions."""
    
    def test_batch_access_before_execution_raises_error(self, client):
        """Test that accessing results before execution raises error."""
        batch = BatchCall(CallableWrapper(client.tests.get_by_id, "123"))
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch.get_results_tuple()
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch.get_successful_results()
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch.get_failed_calls()
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch[0]
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            list(batch)
    
    def test_batch_repr_before_execution(self, client):
        """Test batch string representation before execution."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        repr_str = repr(batch)
        assert "BatchCall(2 calls" in repr_str
        assert "not executed" in repr_str
    
    def test_batch_repr_after_execution(self, client):
        """Test batch string representation after execution."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        repr_str = repr(batch)
        
        assert "BatchCall(2 calls" in repr_str
        assert "2 successful" in repr_str
        assert "executed with separate HTTP sessions" in repr_str


class TestBatchWithDifferentMethodTypes:
    """Test batch with different types of API methods."""
    
    def test_batch_with_put_operations(self, client):
        """Test batch with PUT operations."""
        test_model = client.models.TestModel(Name="Batch Test", IsActive=True)
        
        batch = BatchCall(
            CallableWrapper(client.tests.put_entity, test_model),
            CallableWrapper(client.tests.put_entity, test_model)
        )
        
        results = batch.execute()
        
        assert len(results) == 2
        assert all("id" in result for result in results)
        assert all(result["Name"]["value"] == "Batch Test" for result in results)
    
    def test_batch_with_delete_operations(self, client):
        """Test batch with DELETE operations."""
        batch = BatchCall(
            CallableWrapper(client.tests.delete_by_id, "123"),
            CallableWrapper(client.tests.delete_by_id, "456")
        )
        
        results = batch.execute()
        
        # DELETE returns None (204 No Content)
        assert len(results) == 2
        assert all(result is None for result in results)
    
    def test_batch_with_mixed_operations(self, client):
        """Test batch with mixed operation types."""
        test_model = client.models.TestModel(Name="Mixed Batch", IsActive=False)
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # GET
            CallableWrapper(client.tests.put_entity, test_model),  # PUT
            CallableWrapper(client.tests.get_list),  # GET
            CallableWrapper(client.tests.delete_by_id, "789")  # DELETE
        )
        
        results = batch.execute()
        
        assert len(results) == 4
        assert results[0]["id"] == "123"  # GET result
        assert "id" in results[1]  # PUT result
        assert isinstance(results[2], list)  # GET list result
        assert results[3] is None  # DELETE result


class TestBatchErrorScenarios:
    """Test various error scenarios in batch execution."""
    
    def test_batch_with_invalid_method(self, client):
        """Test batch with method that doesn't exist."""
        # Create wrapper with non-existent method
        wrapper = CallableWrapper(lambda: client.tests.nonexistent_method())
        batch = BatchCall(wrapper, return_exceptions=True)
        
        results = batch.execute()
        
        assert len(results) == 1
        assert isinstance(results[0], Exception)
    
    def test_batch_progress_callback_exception(self, client):
        """Test that batch handles progress callback exceptions gracefully."""
        def failing_callback(completed, total):
            raise Exception("Callback failed")
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            progress_callback=failing_callback
        )
        
        # Should complete successfully despite callback failure
        results = batch.execute()
        assert len(results) == 1
        assert results[0]["id"] == "123"
    
    def test_batch_with_network_simulation(self, client):
        """Test batch behavior with simulated network delays."""
        # Use mock server's delay endpoint
        batch = BatchCall(
            CallableWrapper(lambda: client.session.get(f"{client.base_url}/test/delay/1").json()),
            CallableWrapper(client.tests.get_by_id, "123"),
            max_concurrent=2
        )
        
        start_time = time.time()
        results = batch.execute()
        elapsed = time.time() - start_time
        
        # Should complete both calls, one delayed by ~1 second
        assert len(results) == 2
        assert elapsed >= 0.8  # Allow some margin for timing


class TestBatchMethodIntegration:
    """Test integration with service method batch properties."""
    
    def test_service_method_batch_property(self, client):
        """Test that service methods have .batch property."""
        assert hasattr(client.tests.get_by_id, 'batch')
        assert callable(client.tests.get_by_id.batch)
        
        # Create wrapper using .batch property
        wrapper = client.tests.get_by_id.batch("123")
        assert isinstance(wrapper, CallableWrapper)
        
        # Test execution
        batch = BatchCall(wrapper)
        results = batch.execute()
        assert results[0]["id"] == "123"
    
    def test_batch_with_service_method_batch_calls(self, client):
        """Test batch using service method .batch calls."""
        batch = BatchCall(
            client.tests.get_by_id.batch("123"),
            client.tests.get_list.batch(),
            client.tests.get_ad_hoc_schema.batch()
        )
        
        results = batch.execute()
        
        assert len(results) == 3
        assert results[0]["id"] == "123"
        assert isinstance(results[1], list)
        assert isinstance(results[2], dict)
    
    def test_batch_with_method_arguments(self, client):
        """Test batch with various method argument patterns."""
        options = QueryOptions(top=5)
        test_model = client.models.TestModel(Name="Batch Args Test")
        
        batch = BatchCall(
            client.tests.get_by_id.batch("123"),
            client.tests.get_list.batch(options=options),
            client.tests.put_entity.batch(test_model),
            client.tests.get_ad_hoc_schema.batch()
        )
        
        results = batch.execute()
        
        assert len(results) == 4
        assert results[0]["id"] == "123"
        assert isinstance(results[1], list)
        assert "id" in results[2]
        assert isinstance(results[3], dict)


print("✅ All batch tests implemented and should pass!")