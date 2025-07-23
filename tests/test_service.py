# tests/test_service.py

import pytest

from easy_acumatica import AcumaticaClient
from easy_acumatica.core import BaseService


@pytest.fixture(scope="module")
def client(live_server_url):
    """
    Provides a fully initialized AcumaticaClient instance for the service tests.
    """
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )
    return client

def test_get_list(client):
    """Tests the get_list method of the dynamic service."""
    response = client.tests.get_list()
    assert isinstance(response, list)
    assert len(response) == 2
    assert response[0]['Name']['value'] == "First Item"

def test_get_by_id(client):
    """Tests the get_by_id method."""
    response = client.tests.get_by_id("123")
    assert response['id'] == "123"
    assert response['Name']['value'] == "Specific Test Item"

def test_get_by_id_with_specified_api_version(client):
    """Tests the get_by_id method."""
    response = client.tests.get_by_id("223", api_version="23.200.001")
    assert response['id'] == "223"
    assert response['Name']['value'] == "Old Specific Test Item"

def test_put_entity(client):
    """Tests the put_entity method using a dynamic model instance."""
    new_entity = client.models.TestModel(Name="My New Entity", IsActive=True)
    response = client.tests.put_entity(new_entity)
    assert response['id'] == "new-put-entity-id"
    assert response['Name']['value'] == "My New Entity"

def test_delete_by_id(client):
    """Tests the delete_by_id method."""
    response = client.tests.delete_by_id("456")
    assert response is None

def test_invoke_action(client):
    """Tests an invoke_action_* method."""
    action_invocation = client.models.TestAction(
        entity=client.models.TestModel(Name="ActionEntity"),
        parameters={"Param1": "ActionParameter"}
    )
    response = client.tests.invoke_action_test_action(action_invocation)
    assert response is None # 204 No Content

def test_get_ad_hoc_schema(client):
    """Tests the get_ad_hoc_schema method."""
    response = client.tests.get_ad_hoc_schema()
    assert "CustomStringField" in response
    assert response["CustomStringField"]["type"] == "String"

def test_get_entity_with_file_link(client):
    """Tests that get_by_id returns an entity with a files array."""
    response = client.tests.get_by_id("123")
    assert "files" in response
    assert isinstance(response['files'], list)
    assert response['files'][0]['filename'] == "testfile.txt"

def test_put_file(client):
    """Tests attaching a file to a record."""
    file_content = b"This is the content of the test file."
    response = client.tests.put_file(
        entity_id="123",
        filename="upload.txt",
        data=file_content,
        comment="A test comment"
    )
    assert response is None

def test_get_files(client):
    """Tests the get_files method to retrieve a list of attached files."""
    files = client.tests.get_files(entity_id="123")
    assert isinstance(files, list)
    assert len(files) == 1
    assert files[0]['filename'] == 'testfile.txt'

def test_get_file_content(client):
    """Tests downloading the actual content of a file."""
    entity = client.tests.get_by_id("123")
    file_href = entity['files'][0]['href']
    file_url = f"{client.base_url}{file_href}"
    response = client.session.get(file_url)
    response.raise_for_status()
    assert response.content == b"This is the content of the downloaded file."

# --- NEW TESTS FOR INQUIRIES SERVICE ---

def test_inquiries_service_exists(client):
    """Tests that the inquiries service was created and is accessible."""
    assert hasattr(client, "inquiries"), "The 'inquiries' service should be created."
    inquiries_service = client.inquiries
    assert isinstance(inquiries_service, BaseService)
    assert inquiries_service.entity_name == "Inquirie"

def test_inquiry_methods_created(client):
    """Tests that inquiry methods were dynamically created from the XML metadata."""
    inquiries_service = client.inquiries
    
    # Check that methods were created for each EntitySet in the mock XML
    assert hasattr(inquiries_service, "Account_Details"), "Account_Details method should exist"
    assert hasattr(inquiries_service, "Customer_List"), "Customer_List method should exist"
    assert hasattr(inquiries_service, "Inventory_Items"), "Inventory_Items method should exist"
    assert hasattr(inquiries_service, "GL_Trial_Balance"), "gl_trial_balance method should exist"
    assert hasattr(inquiries_service, "AR_Customer_Balance_Summary"), "AR_Customer_Balance_Summary method should exist"
    assert hasattr(inquiries_service, "IN_Inventory_Summary"), "IN_Inventory_Summary method should exist"

def test_inquiry_method_call(client):
    """Tests that inquiry methods actually work and return data."""
    # Test the account_details method
    result = client.inquiries.Account_Details()
    assert isinstance(result, dict)
    assert 'value' in result
    assert isinstance(result['value'], list)
    assert len(result['value']) == 2
    assert result['value'][0]['AccountID']['value'] == "1000"
    assert result['value'][0]['AccountName']['value'] == "Cash Account"
    assert result['value'][0]['Balance']['value'] == 50000.00

def test_inquiry_method_with_options(client):
    """Tests that inquiry methods work with QueryOptions."""
    from easy_acumatica.odata import QueryOptions, F
    
    # Test with query options (the mock server doesn't actually filter, but we test the call)
    options = QueryOptions(
        filter=F.AccountID == "1000",
        top=10
    )
    
    result = client.inquiries.Customer_List(options=options)
    assert isinstance(result, dict)
    assert 'value' in result
    assert isinstance(result['value'], list)
    assert len(result['value']) == 2
    assert result['value'][0]['CustomerID']['value'] == "C001"
    assert result['value'][0]['CustomerName']['value'] == "ABC Corp"

def test_inquiry_method_docstrings(client):
    """Tests that inquiry methods have proper docstrings generated."""
    # Check that the dynamically created methods have docstrings
    account_details_method = getattr(client.inquiries, "Account_Details")
    assert account_details_method.__doc__ is not None
    assert "Generic Inquiry for the 'Account Details' endpoint" in account_details_method.__doc__
    assert "AccountID" in account_details_method.__doc__
    assert "AccountName" in account_details_method.__doc__
    assert "Balance" in account_details_method.__doc__

def test_inquiry_method_name_formatting(client):
    """Tests that inquiry method names are properly formatted from EntitySet names."""
    inquiries_service = client.inquiries
    
    # Test that names with spaces and hyphens are converted to snake_case
    assert hasattr(inquiries_service, "Account_Details")
    assert hasattr(inquiries_service, "Customer_List")
    assert hasattr(inquiries_service, "GL_Trial_Balance")
    assert hasattr(inquiries_service, "AR_Customer_Balance_Summary")
    assert hasattr(inquiries_service, "IN_Inventory_Summary")

def test_different_inquiry_responses(client):
    """Tests that different inquiries return different data structures."""
    # Test Account Details inquiry
    account_result = client.inquiries.Account_Details()
    assert 'AccountID' in account_result['value'][0]
    assert 'Balance' in account_result['value'][0]
    
    # Test Customer List inquiry  
    customer_result = client.inquiries.Customer_List()
    assert 'CustomerID' in customer_result['value'][0]
    assert 'CustomerName' in customer_result['value'][0]
    assert 'City' in customer_result['value'][0]
    
    # Test that they return different data
    assert account_result != customer_result

def test_xml_metadata_parsing(client):
    """Tests that the XML metadata was correctly parsed to create inquiry methods."""
    inquiries_service = client.inquiries
    
    # Verify that all expected EntitySets from the mock XML were processed
    expected_methods = [
        "Account_Details",
        "Customer_List", 
        "Inventory_Items",
        "GL_Trial_Balance",
        "AR_Customer_Balance_Summary",
        "IN_Inventory_Summary"
    ]
    
    for method_name in expected_methods:
        assert hasattr(inquiries_service, method_name), f"Method {method_name} should exist"
        method = getattr(inquiries_service, method_name)
        assert callable(method), f"Method {method_name} should be callable"
        assert method.__doc__ is not None, f"Method {method_name} should have a docstring"

print("✅ All inquiry service tests should now pass!")