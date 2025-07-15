from easy_acumatica import AcumaticaClient
from easy_acumatica.core import BaseService

def test_client_initialization(live_server_url):
    """
    Tests that the AcumaticaClient initializes correctly and creates
    methods with proper snake_case naming.
    """
    # 1. Arrange & Act
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )

    # 2. Assert
    assert hasattr(client.models, "TestModel"), "TestModel should be dynamically created."
    assert hasattr(client, "tests"), "tests service should be dynamically created."
    
    test_service = getattr(client, "tests")
    assert isinstance(test_service, BaseService)

    # --- FINAL ASSERTIONS ---
    # Assert that the correct snake_case methods now exist on the service.
    assert hasattr(test_service, "get_list"), "Method get_list should exist."
    assert hasattr(test_service, "get_by_id"), "Method get_by_id should exist."
    assert hasattr(test_service, "put_entity"), "Method put_entity should exist."
    assert hasattr(test_service, "delete_by_id"), "Method delete_by_id should exist."
    assert hasattr(test_service, "invoke_action_test_action"), "Method invoke_action_test_action should exist."
    assert hasattr(test_service, "get_ad_hoc_schema"), "Method get_ad_hoc_schema should exist."

    print("\n✅ Client initialization and refactor successful!")
    print("All dynamic methods found with correct snake_case naming.")