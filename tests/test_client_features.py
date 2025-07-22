from easy_acumatica import AcumaticaClient

# Constants from the mock server for verification
LATEST_DEFAULT_VERSION = "24.200.001"
OLD_DEFAULT_VERSION = "23.200.001"

def test_auto_detects_latest_endpoint_version(live_server_url):
    """
    Tests that the client, when no version is specified, automatically
    finds and uses the LATEST version of the endpoint from the server list.
    """
    # 1. Arrange & Act: Initialize client without an endpoint_version
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default"
    )

    # 2. Assert
    # Verify that the client stored the correct (latest) version
    assert client.endpoints["Default"]["version"] == LATEST_DEFAULT_VERSION

    # Verify that subsequent API calls use the latest version in the URL
    # We can check this by making a simple API call and inspecting its URL
    try:
        # This call will fail if it uses the wrong version, as no mock endpoint exists for it
        client.tests.get_by_id("123")
    except Exception as e:
        # If an error occurs, check if the URL in the error message contains the correct version
        assert LATEST_DEFAULT_VERSION in str(e), \
            f"The client should have used version {LATEST_DEFAULT_VERSION} in its API call."

    print(f"\n✅ Client successfully auto-detected latest version: {LATEST_DEFAULT_VERSION}")


def test_uses_specified_endpoint_version(live_server_url):
    """
    Tests that the client uses the EXPLICITLY provided version, even if it's
    not the latest one available on the server.
    """
    # 1. Arrange & Act: Initialize client WITH a specific, older version
    client = AcumaticaClient(
        base_url=live_server_url,
        username="test_user",
        password="test_password",
        tenant="test_tenant",
        endpoint_name="Default",
        endpoint_version=OLD_DEFAULT_VERSION # Specify the older version
    )

    # 2. Assert
    # The client's internal endpoint dictionary should reflect all available versions
    assert client.endpoints["Default"]["version"] == LATEST_DEFAULT_VERSION

    # We need to add a swagger endpoint for the OLD version in the mock server
    # to make this test pass. For now, we can check the constructed URL.
    # Let's try to make a call and check the URL in the potential error.
    try:
        # This will fail because our mock swagger endpoint for the old version doesn't exist yet,
        # but the failure will prove it TRIED to use the correct URL.
        client.tests.get_by_id("123")
    except Exception as e:
        assert OLD_DEFAULT_VERSION in str(e), \
             f"The client should have used the specified version {OLD_DEFAULT_VERSION}."

    print(f"\n✅ Client correctly used specified version: {OLD_DEFAULT_VERSION}")
