# tests/test_batch.py
"""Tests for batch calling functionality."""

import pytest
import time
from unittest.mock import Mock, patch
from concurrent.futures import ThreadPoolExecutor

from easy_acumatica import AcumaticaClient
from easy_acumatica.batch import (
    BatchCall, CallableWrapper, batch_call, 
    create_batch_from_ids, create_batch_from_filters,
    BatchCallResult, BatchCallStats
)
from easy_acumatica.exceptions import AcumaticaError
from easy_acumatica.odata import QueryOptions, F


class TestCallableWrapper:
    """Test CallableWrapper functionality."""
    
    def test_callable_wrapper_creation(self):
        """Test creating CallableWrapper."""
        def test_func(a, b, c=3):
            return a + b + c
        
        wrapper = CallableWrapper(test_func, 1, 2, c=4)
        
        assert wrapper.func == test_func
        assert wrapper.args == (1, 2)
        assert wrapper.kwargs == {"c": 4}
        assert wrapper.description == "test_func"
    
    def test_callable_wrapper_execution(self):
        """Test CallableWrapper execution."""
        def test_func(x, y=10):
            return x * y
        
        wrapper = CallableWrapper(test_func, 5, y=20)
        result = wrapper.execute()
        
        assert result == 100
    
    def test_callable_wrapper_with_service_method(self, live_server_url):
        """Test CallableWrapper with actual service method."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant"
        )
        
        wrapper = CallableWrapper(client.tests.get_by_id, "123")
        result = wrapper.execute()
        
        assert result["id"] == "123"
        client.close()


class TestBatchCall:
    """Test BatchCall functionality."""
    
    @pytest.fixture
    def client(self, live_server_url):
        """Provide a client for testing."""
        return AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant"
        )
    
    def test_batch_call_creation(self, client):
        """Test creating BatchCall with various call types."""
        # Test with CallableWrapper
        wrapper = CallableWrapper(client.tests.get_by_id, "123")
        
        # Test with direct callable (should be auto-wrapped)
        def simple_call():
            return "test"
        
        batch = BatchCall(wrapper, simple_call, max_concurrent=2)
        
        assert len(batch.calls) == 2
        assert isinstance(batch.calls[0], CallableWrapper)
        assert isinstance(batch.calls[1], CallableWrapper)
        assert batch.max_concurrent == 2
    
    def test_batch_call_execution(self, client):
        """Test basic batch execution."""
        # Create batch with multiple API calls
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            max_concurrent=2,
            timeout=30
        )
        
        # Execute and get results
        results = batch.execute()
        
        assert len(results) == 2
        assert results[0]["id"] == "123"  # get_by_id result
        assert isinstance(results[1], list)  # get_list result
        assert len(results[1]) == 2
        
        # Check batch stats
        assert batch.stats.total_calls == 2
        assert batch.stats.successful_calls == 2
        assert batch.stats.failed_calls == 0
        assert batch.stats.total_time > 0
    
    def test_batch_call_unpacking(self, client):
        """Test tuple unpacking from batch results."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        # Test unpacking
        entity, entity_list = batch.execute()
        
        assert entity["id"] == "123"
        assert isinstance(entity_list, list)
        assert len(entity_list) == 2
    
    def test_batch_call_async_execution(self, client):
        """Test async execution without blocking."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        # Execute async
        batch.execute_async()
        
        # Results should be available
        assert batch.executed is True
        assert len(batch.results) == 2
        assert batch.results[0].success is True
        assert batch.results[1].success is True
    
    def test_batch_call_error_handling(self, client):
        """Test error handling in batch calls."""
        def failing_call():
            raise ValueError("Test error")
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),  # Should succeed
            CallableWrapper(failing_call),  # Should fail
            return_exceptions=True
        )
        
        results = batch.execute()
        
        assert len(results) == 2
        assert results[0]["id"] == "123"  # Successful result
        assert isinstance(results[1], ValueError)  # Exception as result
        
        assert batch.stats.successful_calls == 1
        assert batch.stats.failed_calls == 1
    
    def test_batch_call_fail_fast(self, client):
        """Test fail_fast behavior."""
        def failing_call():
            raise ValueError("Test error")
        
        batch = BatchCall(
            CallableWrapper(failing_call),
            CallableWrapper(client.tests.get_by_id, "123"),
            fail_fast=True,
            return_exceptions=False
        )
        
        with pytest.raises(AcumaticaError, match="fail_fast"):
            batch.execute()
    
    def test_batch_call_timeout(self, client):
        """Test batch timeout behavior."""
        def slow_call():
            time.sleep(2)
            return "slow"
        
        batch = BatchCall(
            CallableWrapper(slow_call),
            CallableWrapper(slow_call),
            timeout=1.0  # 1 second timeout
        )
        
        with pytest.raises(TimeoutError):
            batch.execute()
    
    def test_batch_call_progress_callback(self, client):
        """Test progress callback functionality."""
        progress_calls = []
        
        def progress_callback(completed, total):
            progress_calls.append((completed, total))
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list),
            progress_callback=progress_callback
        )
        
        batch.execute()
        
        # Should have progress updates
        assert len(progress_calls) >= 1
        assert progress_calls[-1] == (2, 2)  # Final update should be (2, 2)
    
    def test_batch_call_retry_failed(self, client):
        """Test retrying failed calls."""
        call_count = 0
        
        def sometimes_failing_call():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ValueError("First call fails")
            return "success"
        
        # Initial batch with one failure
        batch1 = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(sometimes_failing_call)
        )
        
        batch1.execute()
        assert batch1.stats.failed_calls == 1
        
        # Retry failed calls
        retry_batch = batch1.retry_failed_calls()
        retry_results = retry_batch.execute()
        
        assert len(retry_results) == 1
        assert retry_results[0] == "success"
        assert retry_batch.stats.successful_calls == 1
    
    def test_batch_call_helper_methods(self, client):
        """Test helper methods for accessing results."""
        def failing_call():
            raise ValueError("Test error")
        
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(failing_call),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        
        # Test successful results
        successful = batch.get_successful_results()
        assert len(successful) == 2
        assert successful[0]["id"] == "123"
        assert isinstance(successful[1], list)
        
        # Test failed calls
        failed = batch.get_failed_calls()
        assert len(failed) == 1
        assert failed[0][0] == 1  # Index 1 failed
        assert isinstance(failed[0][2], ValueError)  # Error is ValueError
    
    def test_batch_call_indexing_and_iteration(self, client):
        """Test indexing and iteration over batch results."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        
        # Test indexing
        assert isinstance(batch[0], BatchCallResult)
        assert batch[0].success is True
        assert batch[1].success is True
        
        # Test length
        assert len(batch) == 2
        
        # Test iteration
        results = list(batch)
        assert len(results) == 2
        assert all(isinstance(r, BatchCallResult) for r in results)
    
    def test_batch_call_summary(self, client, capsys):
        """Test print_summary functionality."""
        batch = BatchCall(
            CallableWrapper(client.tests.get_by_id, "123"),
            CallableWrapper(client.tests.get_list)
        )
        
        batch.execute()
        batch.print_summary()
        
        captured = capsys.readouterr()
        assert "Batch Execution Summary" in captured.out
        assert "Total Calls: 2" in captured.out
        assert "Successful: 2" in captured.out
        assert "Success Rate: 100.0%" in captured.out


class TestBatchCallIntegration:
    """Test batch calling integration with service methods."""
    
    @pytest.fixture
    def client(self, live_server_url):
        """Provide a client for testing."""
        return AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant"
        )
    
    def test_service_method_batch_property(self, client):
        """Test that service methods have .batch property."""
        # Check that batch property exists
        assert hasattr(client.tests.get_by_id, 'batch')
        assert callable(client.tests.get_by_id.batch)
        
        # Create batch call using .batch property
        wrapper = client.tests.get_by_id.batch("123")
        assert isinstance(wrapper, CallableWrapper)
        
        result = wrapper.execute()
        assert result["id"] == "123"
    
    def test_batch_with_service_methods(self, client):
        """Test creating batch with service method .batch properties."""
        batch = BatchCall(
            client.tests.get_by_id.batch("123"),
            client.tests.get_list.batch(),
            client.tests.get_ad_hoc_schema.batch()
        )
        
        entity, entity_list, schema = batch.execute()
        
        assert entity["id"] == "123"
        assert isinstance(entity_list, list)
        assert isinstance(schema, dict)
    
    def test_batch_with_different_services(self, client):
        """Test batch calls across different services."""
        # Note: In our test setup, we only have 'tests' service
        # In real usage, this would work with multiple services
        batch = BatchCall(
            client.tests.get_by_id.batch("123"),
            client.tests.get_list.batch()
        )
        
        results = batch.execute()
        assert len(results) == 2


class TestBatchConvenienceFunctions:
    """Test convenience functions for batch calling."""
    
    @pytest.fixture
    def client(self, live_server_url):
        """Provide a client for testing."""
        return AcumaticaClient(
            base_url=live_server_url,
            username="test_user", 
            password="test_password",
            tenant="test_tenant"
        )
    
    def test_batch_call_function(self, client):
        """Test batch_call convenience function."""
        batch = batch_call(
            client.tests.get_by_id.batch("123"),
            client.tests.get_list.batch(),
            max_concurrent=2
        )
        
        # Should return executed BatchCall
        assert isinstance(batch, BatchCall)
        assert not batch.executed  # batch_call returns unexecuted batch
        
        results = batch.execute()
        assert len(results) == 2
    
    def test_create_batch_from_ids(self, client):
        """Test create_batch_from_ids helper."""
        entity_ids = ["123"]  # Only "123" exists in our mock
        
        batch = create_batch_from_ids(client.tests, entity_ids)
        results = batch.execute()
        
        assert len(results) == 1
        assert results[0]["id"] == "123"
    
    def test_create_batch_from_filters(self, client):
        """Test create_batch_from_filters helper."""
        filters = [
            QueryOptions(top=5),
            QueryOptions(top=10),
        ]
        
        batch = create_batch_from_filters(client.tests, filters, method_name='get_list')
        results = batch.execute()
        
        assert len(results) == 2
        # Both should return the same list (our mock doesn't actually filter)
        assert all(isinstance(result, list) for result in results)


class TestBatchCallPerformance:
    """Test batch calling performance characteristics."""
    
    @pytest.fixture
    def client(self, live_server_url):
        """Provide a client for testing."""
        return AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password", 
            tenant="test_tenant"
        )
    
    def test_batch_vs_sequential_performance(self, client):
        """Test that batch calls are faster than sequential calls."""
        def slow_call(delay=0.1):
            time.sleep(delay)
            return client.tests.get_by_id("123")
        
        num_calls = 3
        delay_per_call = 0.1
        
        # Sequential execution
        start_time = time.time()
        for _ in range(num_calls):
            slow_call(delay_per_call)
        sequential_time = time.time() - start_time
        
        # Batch execution
        batch = BatchCall(*[CallableWrapper(slow_call, delay_per_call) for _ in range(num_calls)])
        
        start_time = time.time()
        batch.execute()
        batch_time = time.time() - start_time
        
        # Batch should be significantly faster
        # Sequential: ~3 * 0.1 = 0.3s, Batch: ~0.1s (concurrent)
        assert batch_time < sequential_time * 0.8  # At least 20% faster
        assert batch.stats.total_calls == num_calls
        assert batch.stats.successful_calls == num_calls
    
    def test_batch_concurrency_levels(self, client):
        """Test different concurrency levels."""
        def simple_call():
            return client.tests.get_by_id("123")
        
        num_calls = 5
        
        # Test with different max_concurrent settings
        for max_concurrent in [1, 3, 5]:
            batch = BatchCall(
                *[CallableWrapper(simple_call) for _ in range(num_calls)],
                max_concurrent=max_concurrent
            )
            
            start_time = time.time()
            results = batch.execute()
            execution_time = time.time() - start_time
            
            assert len(results) == num_calls
            assert batch.stats.concurrency_level == min(max_concurrent, num_calls)
            assert all(r["id"] == "123" for r in results)


class TestBatchCallEdgeCases:
    """Test edge cases and error scenarios."""
    
    def test_empty_batch_call(self):
        """Test creating and executing empty batch."""
        batch = BatchCall()
        
        results = batch.execute()
        assert results == ()
        assert batch.stats.total_calls == 0
    
    def test_batch_call_invalid_callable(self):
        """Test batch with invalid callable."""
        with pytest.raises(TypeError, match="Invalid call type"):
            BatchCall("not_callable")
    
    def test_batch_call_re_execution(self, live_server_url):
        """Test that re-executing batch is handled gracefully."""
        client = AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant"
        )
        
        batch = BatchCall(CallableWrapper(client.tests.get_by_id, "123"))
        
        # First execution
        results1 = batch.execute()
        
        # Second execution should not re-run
        results2 = batch.execute()
        
        assert results1 == results2
        client.close()
    
    def test_accessing_results_before_execution(self):
        """Test that accessing results before execution raises error."""
        batch = BatchCall(CallableWrapper(lambda: "test"))
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch.get_results_tuple()
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch.get_successful_results()
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            list(batch)  # Iteration
        
        with pytest.raises(RuntimeError, match="Batch must be executed"):
            batch[0]  # Indexing


class TestBatchCallWithRealScenarios:
    """Test batch calling with realistic Acumatica scenarios."""
    
    @pytest.fixture
    def client(self, live_server_url):
        """Provide a client for testing."""
        return AcumaticaClient(
            base_url=live_server_url,
            username="test_user",
            password="test_password",
            tenant="test_tenant"
        )
    
    def test_batch_crud_operations(self, client):
        """Test batch with mixed CRUD operations."""
        # Create model for PUT operation
        test_model = client.models.TestModel(
            Name="Batch Test Entity",
            Value="Test Value",
            IsActive=True
        )
        
        batch = BatchCall(
            client.tests.get_list.batch(),
            client.tests.get_by_id.batch("123"),
            client.tests.put_entity.batch(test_model),
            client.tests.get_ad_hoc_schema.batch()
        )
        
        entity_list, entity, created_entity, schema = batch.execute()
        
        # Verify results
        assert isinstance(entity_list, list)
        assert entity["id"] == "123"
        assert created_entity["id"] == "new-put-entity-id"
        assert isinstance(schema, dict)
        
        # Verify batch stats
        assert batch.stats.successful_calls == 4
        assert batch.stats.failed_calls == 0
    
    def test_batch_with_query_options(self, client):
        """Test batch calls with QueryOptions."""
        options1 = QueryOptions(top=5)
        options2 = QueryOptions(expand=["files"], select=["id", "Name", "files"])
        
        batch = BatchCall(
            client.tests.get_list.batch(options=options1),
            client.tests.get_by_id.batch("123", options=options2)
        )
        
        list_result, entity_result = batch.execute()
        
        assert isinstance(list_result, list)
        assert entity_result["id"] == "123"
        assert "files" in entity_result  # Should be expanded
    
    def test_batch_error_recovery(self, client):
        """Test error recovery patterns with batch calls."""
        # Create a batch where some calls might fail
        batch = BatchCall(
            client.tests.get_by_id.batch("123"),    # Should succeed
            client.tests.get_by_id.batch("999"),    # Should fail (not found)
            client.tests.get_list.batch(),          # Should succeed
            return_exceptions=True
        )
        
        results = batch.execute()
        
        # Check that we got results for all calls
        assert len(results) == 3
        
        # First and third should succeed
        assert results[0]["id"] == "123"
        assert isinstance(results[2], list)
        
        # Second should be an exception
        # Note: Our mock server returns 404 for unknown IDs, 
        # which should be wrapped in an AcumaticaError
        assert isinstance(results[1], Exception)
        
        # Get only successful results
        successful_results = batch.get_successful_results()
        assert len(successful_results) == 2
        
        # Get failed calls info
        failed_calls = batch.get_failed_calls()
        assert len(failed_calls) == 1
        assert failed_calls[0][0] == 1  # Index 1 failed