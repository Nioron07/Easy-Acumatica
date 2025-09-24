# tests/test_batch.py

import pytest
from easy_acumatica import AcumaticaClient
from easy_acumatica.batch import BatchCall, create_batch_from_ids, create_batch_from_filters
from easy_acumatica.exceptions import AcumaticaNotFoundError, AcumaticaBatchError
from easy_acumatica.odata import QueryOptions

def test_successful_batch_get_by_id(base_client_config, reset_server_state):
    """Tests a batch call with multiple successful get_by_id requests."""
    client = AcumaticaClient(**base_client_config)
    
    ids_to_fetch = ["123", "123", "123"]
    
    # Create batch calls using the .batch property
    calls = [client.tests.get_by_id.batch(id) for id in ids_to_fetch]
    
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
    results = create_batch_from_ids(client.tests, ids_to_fetch).execute()
    
    assert len(results) == len(ids_to_fetch)
    assert results[0]['id'] == "123"
    assert results[1]['id'] == "123"

def test_batch_with_mixed_success_and_failure(base_client_config, reset_server_state):
    """Tests a batch with both successful and failed calls."""
    client = AcumaticaClient(**base_client_config)
    
    batch = BatchCall(
        client.tests.get_by_id.batch("123"),          # Success
        client.tests.get_by_id.batch("999"),          # Failure (Not Found)
        client.tests.get_by_id.batch("123"),          # Success
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
            client.tests.get_by_id.batch("123"),
            client.tests.get_by_id.batch("999"),  # This will fail
            client.tests.get_by_id.batch("123"),
            fail_fast=True,
            return_exceptions=False  # Ensure exceptions are raised
        ).execute()

def test_batch_return_exceptions_false(base_client_config, reset_server_state):
    """Tests that an exception is raised immediately when return_exceptions is False."""
    client = AcumaticaClient(**base_client_config)

    with pytest.raises(AcumaticaBatchError):
        BatchCall(
            client.tests.get_by_id.batch("123"),
            client.tests.get_by_id.batch("999"),
            return_exceptions=False
        ).execute()

def test_batch_put_entity(base_client_config, reset_server_state):
    """Tests batching of put_entity calls."""
    client = AcumaticaClient(**base_client_config)
    
    new_item1 = client.models.TestModel(Name="Batch Item 1")
    new_item2 = client.models.TestModel(Name="Batch Item 2")
    
    results = BatchCall(
        client.tests.put_entity.batch(new_item1),
        client.tests.put_entity.batch(new_item2)
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
        client.tests.delete_by_id.batch("1"),
        client.tests.delete_by_id.batch("2")
    ).execute()
    
    assert results == (None, None)

def test_batch_with_mixed_operations(base_client_config, reset_server_state):
    """Tests a batch with a mix of GET, PUT, and DELETE operations."""
    client = AcumaticaClient(**base_client_config)
    
    new_item = client.models.TestModel(Name="Mixed Batch Item")
    
    get_result, put_result, delete_result = BatchCall(
        client.tests.get_by_id.batch("123"),
        client.tests.put_entity.batch(new_item),
        client.tests.delete_by_id.batch("321")
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
        client.tests.get_by_id.batch("123"),
        client.tests.get_by_id.batch("123"),
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
        client.tests.get_by_id.batch("123"),
        client.tests.get_by_id.batch("999"),  # Fails
        client.tests.get_by_id.batch("888")   # Fails
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