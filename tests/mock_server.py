# tests/mock_server.py

from flask import Flask, Response, jsonify, request

from .mock_swagger import get_swagger_json
from .mock_xml import get_odata_metadata_xml

app = Flask(__name__)
LATEST_DEFAULT_VERSION = "24.200.001"
OLD_DEFAULT_VERSION = "23.200.001"
TEST_ENDPOINT_NAME = "Default"
# --- Authentication and Endpoint Discovery ---

@app.route('/entity/auth/login', methods=['POST'])
def login():
    """Simulates a successful login."""
    return jsonify({"message": "Logged in successfully"}), 200

@app.route('/entity/auth/logout', methods=['POST'])
def logout():
    """Simulates a successful logout."""
    return jsonify({"message": "Logged out successfully"}), 204

# --- UPDATED ENDPOINT DISCOVERY ---
@app.route('/entity', methods=['GET'])
def get_endpoints():
    """
    Provides a list of available API endpoints with multiple versions
    to test the client's auto-detection logic.
    """
    return jsonify({
        "version": {"acumaticaBuildVersion": "25.100.001"},
        "endpoints": [
            {"name": "eCommerce", "version": "23.200.001"},
            {"name": TEST_ENDPOINT_NAME, "version": OLD_DEFAULT_VERSION}, # An older version
            {"name": "MANUFACTURING", "version": "24.200.001"},
            {"name": TEST_ENDPOINT_NAME, "version": LATEST_DEFAULT_VERSION}, # The latest version
        ]
    }), 200

# --- Swagger endpoints now need to support multiple versions ---
@app.route(f'/entity/{TEST_ENDPOINT_NAME}/<version>/swagger.json', methods=['GET'])
def get_swagger(version: str):
    """
    Serves the mock swagger.json. This now accepts a version parameter
    to correctly respond to the client's request.
    """
    # In a real scenario, different swagger files might exist per version.
    # For this test, we'll serve the same one regardless of the version requested.
    print(f"Swagger requested for version: {version}")
    return jsonify(get_swagger_json()), 200

# --- NEW METADATA ENDPOINT FOR GENERIC INQUIRIES ---
@app.route('/t/<tenant>/api/odata/gi/$metadata', methods=['GET'])
def get_odata_metadata(tenant: str):
    """
    Serves the OData metadata XML for Generic Inquiries.
    This is used by the service factory to dynamically generate inquiry methods.
    """
    print(f"OData metadata requested for tenant: {tenant}")
    return Response(
        get_odata_metadata_xml(),
        mimetype='application/xml',
        headers={'Content-Type': 'application/xml; charset=utf-8'}
    )

# --- TestService Endpoints ---
BASE_ENTITY_PATH = f"/entity/{TEST_ENDPOINT_NAME}/{LATEST_DEFAULT_VERSION}/Test"
OLD_ENTITY_PATH = f"/entity/{TEST_ENDPOINT_NAME}/{OLD_DEFAULT_VERSION}/Test"
FILES_PATH = f"/entity/{TEST_ENDPOINT_NAME}/{LATEST_DEFAULT_VERSION}/files"
@app.route(BASE_ENTITY_PATH, methods=['GET'])
def get_list():
    """Handles the get_list method. Returns a list of test entities."""
    mock_entities = [
        {"id": "1", "Name": {"value": "First Item"}},
        {"id": "2", "Name": {"value": "Second Item"}},
    ]
    return jsonify(mock_entities), 200

@app.route(f'{BASE_ENTITY_PATH}/<entity_id>', methods=['GET'])
def get_by_id(entity_id: str):
    """
    Handles get_by_id and now correctly includes the mock 'files' array.
    """
    if entity_id != "123":
        return jsonify({"error": "Not Found"}), 404

    return jsonify({
        "id": "123",
        "Name": {"value": "Specific Test Item"},
        "Value": {"value": "Some Value"},
        "IsActive": {"value": True},
        "_links": {
            "files:put": f"/entity/Default/24.200.001/Test/{entity_id}/files/{{filename}}"
        },
        "files": [  # This array was missing
            {
                "id": "mock-file-guid",
                "filename": "testfile.txt",
                "href": f"{FILES_PATH}/mock-file-guid"
            }
        ]
    }), 200

@app.route(f'{OLD_ENTITY_PATH}/<entity_id>', methods=['GET'])
def get_by_id_old_api_version(entity_id: str):
    """
    Handles get_by_id and now correctly includes the mock 'files' array.
    """
    if entity_id != "223":
        return jsonify({"error": "Not Found"}), 404

    return jsonify({
        "id": "223",
        "Name": {"value": "Old Specific Test Item"},
        "Value": {"value": "Old Some Value"},
        "IsActive": {"value": True},
        "files": [  # This array was missing
            {
                "id": "mock-file-guid",
                "filename": "testfile.txt",
                "href": f"{FILES_PATH}/mock-file-guid"
            }
        ]
    }), 200

@app.route(BASE_ENTITY_PATH, methods=['PUT'])
def put_entity():
    """Handles the put_entity method. Echoes the sent data back."""
    data = request.json
    # In a real test, you could add assertions here about the incoming data
    # For now, we'll just echo it back with a new ID.
    data['id'] = "new-put-entity-id"
    return jsonify(data), 200

@app.route(f'{BASE_ENTITY_PATH}/<entity_id>', methods=['DELETE'])
def delete_by_id(entity_id: str):
    """Handles the delete_by_id method. Returns No Content on success."""
    # Here you could check if entity_id is valid
    print(f"Received DELETE for ID: {entity_id}")
    return '', 204 # HTTP 204 No Content is standard for successful DELETE

@app.route(f'{BASE_ENTITY_PATH}/TestAction', methods=['POST'])
def invoke_action():
    """Handles the invoke_action_test_action method."""
    action_data = request.json
    # Assert the structure of the action payload
    assert 'entity' in action_data
    assert 'parameters' in action_data
    assert action_data['entity']['Name']['value'] == "ActionEntity"
    assert action_data['parameters']['Param1']['value'] == "ActionParameter"

    return '', 204 # Actions often return No Content

@app.route(f'{BASE_ENTITY_PATH}/$adHocSchema', methods=['GET'])
def get_ad_hoc_schema():
    """Handles the get_ad_hoc_schema method."""
    return jsonify({
        "CustomStringField": {"type": "String", "viewName": "UsrCustomField"},
        "CustomNumberField": {"type": "Decimal", "viewName": "UsrCustomNumber"}
    }), 200

# --- NEW ENDPOINT FOR FILE UPLOADS ---
@app.route(f'{BASE_ENTITY_PATH}/<entity_id>/files/<filename>', methods=['PUT'])
def attach_file(entity_id: str, filename: str):
    """Simulates attaching a file to an entity."""
    assert request.content_type == "application/octet-stream"
    assert request.data == b"This is the content of the test file."
    assert request.headers.get("PX-CbFileComment") == "A test comment"
    print(f"File '{filename}' attached to entity '{entity_id}' successfully.")
    return '', 204

# --- NEW ENDPOINT FOR FILE DOWNLOADS ---
@app.route(f'{FILES_PATH}/<file_id>', methods=['GET'])
def get_file(file_id: str):
    """Simulates downloading a file."""
    if file_id != "mock-file-guid":
        return "File not found", 404

    return Response(
        b"This is the content of the downloaded file.",
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=downloaded.txt"}
    )

# --- NEW ENDPOINT FOR GENERIC INQUIRIES ---
@app.route('/t/<tenant>/api/odata/gi/<inquiry_name>', methods=['GET'])
def get_inquiry(tenant: str, inquiry_name: str):
    """Simulates a generic inquiry request."""
    # Return different data based on the inquiry name for better testing
    if inquiry_name == "Account Details":
        return jsonify({
            "value": [
                {"AccountID": {"value": "1000"}, "AccountName": {"value": "Cash Account"}, "Balance": {"value": 50000.00}},
                {"AccountID": {"value": "2000"}, "AccountName": {"value": "Accounts Receivable"}, "Balance": {"value": 25000.00}},
            ]
        }), 200
    elif inquiry_name == "Customer List":
        return jsonify({
            "value": [
                {"CustomerID": {"value": "C001"}, "CustomerName": {"value": "ABC Corp"}, "City": {"value": "New York"}},
                {"CustomerID": {"value": "C002"}, "CustomerName": {"value": "XYZ Ltd"}, "City": {"value": "Chicago"}},
            ]
        }), 200
    else:
        # Default response for any other inquiry
        return jsonify({
            "value": [
                {"Account": {"value": "Test Account 1"}},
                {"Account": {"value": "Test Account 2"}},
            ]
        }), 200