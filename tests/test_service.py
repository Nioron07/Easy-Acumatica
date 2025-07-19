# tests/test_service.py

import pytest
from easy_acumatica import AcumaticaClient
from easy_acumatica.inquiries import GenericInquiries

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
    # Manually attach the inquiries service for testing
    client.inquiries = GenericInquiries(client)
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

def test_get_inquiry(client):
    """Tests the get method of the GenericInquiries service."""
    result = client.inquiries._get("TestInquiry")
    assert isinstance(result['value'], list)
    assert len(result['value']) == 2
    assert result['value'][0]['Account']['value'] == "Test Account 1"