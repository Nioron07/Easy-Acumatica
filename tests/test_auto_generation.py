import pytest
from typing import Optional
from easy_acumatica import AcumaticaClient
from easy_acumatica.core import BaseService, BaseDataClassModel

def test_client_and_model_structure(live_server_url):
    """
    Tests client initialization and validates the structure of the
    dynamically created data model.
    """
    # 1. Arrange & Act
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )

    # 2. Assert Service and Method Creation
    assert hasattr(client, "tests"), "The 'tests' service should be created."
    test_service = getattr(client, "tests")
    assert isinstance(test_service, BaseService)
    assert hasattr(test_service, "get_list"), "Method get_list should exist."
    assert hasattr(test_service, "put_entity"), "Method put_entity should exist."

    # 3. Assert Model Structure
    assert hasattr(client.models, "TestModel"), "TestModel should be created."
    assert hasattr(client.models, "FileLink"), "FileLink model should be created."
    
    TestModel = client.models.TestModel
    assert issubclass(TestModel, BaseDataClassModel)
    annotations = TestModel.__annotations__
    
    # Verify the existence and correct type of each field
    assert "Name" in annotations
    assert annotations['Name'] == Optional[str]
    
    assert "Value" in annotations
    assert annotations['Value'] == Optional[str]
    
    assert "IsActive" in annotations
    assert annotations['IsActive'] == Optional[bool]
    
    assert "files" in annotations
    # The type will be a List of the ForwardRef to FileLink initially
    assert 'List' in str(annotations['files'])
    assert 'FileLink' in str(annotations['files'])

    print("\n✅ Client initialization successful!")
    print("✅ Dynamic service and all methods created correctly.")
    print("✅ Dynamic model 'TestModel' created with correct field structure and types.")