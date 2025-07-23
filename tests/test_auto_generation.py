from typing import Optional

from easy_acumatica import AcumaticaClient
from easy_acumatica.core import BaseDataClassModel, BaseService


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
    test_service = client.tests
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


def test_inquiries_service_generation(live_server_url):
    """
    Tests that the inquiries service is properly generated from XML metadata.
    """
    # 1. Arrange & Act
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )

    # 2. Assert Inquiries Service Creation
    assert hasattr(client, "inquiries"), "The 'inquiries' service should be created."
    inquiries_service = client.inquiries
    assert isinstance(inquiries_service, BaseService)
    assert inquiries_service.entity_name == "Inquirie"

    # 3. Assert Inquiry Methods Creation from XML Metadata
    expected_inquiry_methods = [
        "Account_Details",
        "Customer_List", 
        "Inventory_Items",
        "GL_Trial_Balance",
        "AR_Customer_Balance_Summary",
        "IN_Inventory_Summary"
    ]

    for method_name in expected_inquiry_methods:
        assert hasattr(inquiries_service, method_name), f"Method {method_name} should exist on inquiries service"
        method = getattr(inquiries_service, method_name)
        assert callable(method), f"Method {method_name} should be callable"

    # 4. Assert Method Names Are Properly Formatted
    # Test that EntitySet names with spaces/hyphens are converted to snake_case
    original_names = [
        "Account Details",
        "Customer List", 
        "Inventory Items",
        "GL-Trial Balance",
        "AR-Customer Balance Summary",
        "IN-Inventory Summary"
    ]
    
    # Verify the transformation logic worked
    for original_name, expected_method in zip(original_names, expected_inquiry_methods):
        assert hasattr(inquiries_service, expected_method), \
            f"EntitySet '{original_name}' should create method '{expected_method}'"

    print("\n✅ Inquiries service created successfully!")
    print(f"✅ Generated {len(expected_inquiry_methods)} inquiry methods from XML metadata.")
    print("✅ Method names properly formatted from EntitySet names.")


def test_inquiry_methods_have_docstrings(live_server_url):
    """
    Tests that dynamically generated inquiry methods have proper docstrings.
    """
    # 1. Arrange & Act
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user", 
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )

    # 2. Assert Docstrings Are Generated
    inquiries_service = client.inquiries
    
    # Test a specific method's docstring
    account_details_method = getattr(inquiries_service, "Account_Details")
    docstring = account_details_method.__doc__
    
    assert docstring is not None, "Inquiry method should have a docstring"
    assert "Generic Inquiry for the 'Account Details' endpoint" in docstring
    assert "Args:" in docstring
    assert "QueryOptions" in docstring
    assert "Returns:" in docstring
    
    # Check that docstring contains field information from XML EntityType
    assert "AccountID" in docstring
    assert "AccountName" in docstring  
    assert "Balance" in docstring
    assert "IsActive" in docstring
    assert "CreatedDate" in docstring

    # Test another method to ensure consistent generation
    customer_list_method = getattr(inquiries_service, "Customer_List")
    customer_docstring = customer_list_method.__doc__
    
    assert customer_docstring is not None
    assert "Generic Inquiry for the 'Customer List' endpoint" in customer_docstring
    assert "CustomerID" in customer_docstring
    assert "CustomerName" in customer_docstring
    assert "City" in customer_docstring
    assert "Phone" in customer_docstring
    assert "Email" in customer_docstring

    print("\n✅ Inquiry methods have proper docstrings!")
    print("✅ Docstrings include field information from XML metadata.")
    print("✅ Docstrings follow consistent format with Args and Returns sections.")


def test_xml_metadata_endpoint_access(live_server_url):
    """
    Tests that the XML metadata endpoint is accessible and returns valid XML.
    """
    import requests
    import xml.etree.ElementTree as ET
    
    # Test the metadata endpoint directly
    metadata_url = f"{live_server_url}/t/test_tenant/api/odata/gi/$metadata"
    
    response = requests.get(metadata_url)
    assert response.status_code == 200
    assert response.headers.get('content-type', '').startswith('application/xml')
    
    # Parse the XML to verify it's valid
    root = ET.fromstring(response.content)
    
    # Verify it's valid OData metadata XML
    assert root.tag.endswith('Edmx'), "Root element should be Edmx"
    
    # Find EntityContainer
    namespaces = {'edmx': 'http://docs.oasis-open.org/odata/ns/edmx', 'edm': 'http://docs.oasis-open.org/odata/ns/edm'}
    container = root.find('.//edm:EntityContainer[@Name="Default"]', namespaces)
    assert container is not None, "Should find EntityContainer named 'Default'"
    
    # Verify EntitySets exist
    entity_sets = container.findall('edm:EntitySet', namespaces)
    assert len(entity_sets) >= 3, "Should have at least 3 EntitySets"
    
    # Verify specific EntitySets from our mock data
    entity_set_names = [es.get('Name') for es in entity_sets]
    assert "Account Details" in entity_set_names
    assert "Customer List" in entity_set_names
    assert "Inventory Items" in entity_set_names

    print("\n✅ XML metadata endpoint is accessible and returns valid OData XML!")
    print(f"✅ Found {len(entity_sets)} EntitySets in metadata.")