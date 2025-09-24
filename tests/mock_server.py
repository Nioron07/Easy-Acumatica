# tests/mock_server.py

from flask import Flask, Response, jsonify, request
import time

try:
    from .mock_swagger import get_swagger_json, get_modified_swagger_json
    from .mock_xml import get_odata_metadata_xml, get_modified_odata_metadata_xml
except ImportError:
    # Handle case where tests are run from different directory
    from mock_swagger import get_swagger_json, get_modified_swagger_json
    from mock_xml import get_odata_metadata_xml, get_modified_odata_metadata_xml

app = Flask(__name__)
LATEST_DEFAULT_VERSION = "24.200.001"
OLD_DEFAULT_VERSION = "23.200.001"
TEST_ENDPOINT_NAME = "Default"

# Global state for simulating schema changes
_schema_version = "v1"
_xml_version = "v1"

# --- Authentication and Endpoint Discovery ---

@app.route('/entity/auth/login', methods=['POST'])
def login():
    """Simulates a successful login or various auth errors based on input."""
    data = request.get_json()
    if data and data.get('username') == 'expired_session':
        return jsonify({"message": "Your session has expired. Please log in again."}), 401
    elif data and data.get('username') == 'invalid':
        return jsonify({"message": "Invalid credentials. Please check your username and password."}), 401
    elif data and data.get('username') == 'forbidden':
        return jsonify({"message": "Access forbidden. You do not have permission to access this resource."}), 403
    return jsonify({"message": "Logged in successfully"}), 200

@app.route('/entity/auth/logout', methods=['POST'])
def logout():
    """Simulates a successful logout."""
    return jsonify({"message": "Logged out successfully"}), 204

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
            {"name": TEST_ENDPOINT_NAME, "version": OLD_DEFAULT_VERSION}, 
            {"name": "MANUFACTURING", "version": "24.200.001"},
            {"name": TEST_ENDPOINT_NAME, "version": LATEST_DEFAULT_VERSION}, 
        ]
    }), 200

# --- Schema version control endpoints for testing differential caching ---

@app.route('/test/schema/version', methods=['POST'])
def set_schema_version():
    """Test endpoint to change schema version for differential caching tests."""
    global _schema_version
    data = request.get_json()
    _schema_version = data.get('version', 'v1')
    return jsonify({"schema_version": _schema_version}), 200

@app.route('/test/xml/version', methods=['POST'])  
def set_xml_version():
    """Test endpoint to change XML version for differential caching tests."""
    global _xml_version
    data = request.get_json()
    _xml_version = data.get('version', 'v1')
    return jsonify({"xml_version": _xml_version}), 200

@app.route('/test/versions', methods=['GET'])
def get_versions():
    """Get current schema and XML versions."""
    return jsonify({
        "schema_version": _schema_version,
        "xml_version": _xml_version
    }), 200

# --- Swagger endpoints with version support ---

@app.route(f'/entity/{TEST_ENDPOINT_NAME}/<version>/swagger.json', methods=['GET'])
def get_swagger(version: str):
    """
    Serves the mock swagger.json with support for different schema versions
    to test differential caching.
    """
    print(f"Swagger requested for version: {version}, schema version: {_schema_version}")
    
    if _schema_version == "v2":
        return jsonify(get_modified_swagger_json()), 200
    else:
        return jsonify(get_swagger_json()), 200

# --- OData metadata endpoint with version support ---

@app.route('/t/<tenant>/api/odata/gi/$metadata', methods=['GET'])
def get_odata_metadata(tenant: str):
    """
    Serves the OData metadata XML for Generic Inquiries with version support
    to test differential inquiry caching.
    """
    print(f"OData metadata requested for tenant: {tenant}, XML version: {_xml_version}")
    
    if _xml_version == "v2":
        xml_content = get_modified_odata_metadata_xml()
    else:
        xml_content = get_odata_metadata_xml()
    
    return Response(
        xml_content,
        mimetype='application/xml',
        headers={'Content-Type': 'application/xml; charset=utf-8'}
    )

# --- Error Testing Endpoints ---

# Removed duplicate endpoint - auth errors handled by main login endpoint

@app.route('/test/error/<int:status_code>', methods=['GET', 'POST', 'PUT', 'DELETE'])
def trigger_error(status_code: int):
    """Test endpoint to trigger specific HTTP error codes."""
    error_responses = {
        400: {"message": "Bad request. The request was invalid or cannot be served."},
        401: {"message": "Authentication required. Please provide valid credentials."},
        403: {"message": "Access forbidden. You do not have permission to access this resource."},
        404: {"message": "Resource not found. The requested resource does not exist."},
        408: {"message": "Request timeout. The server timed out waiting for the request."},
        409: {"message": "Conflict. The request could not be completed due to a conflict."},
        412: {"message": "Precondition failed. The record has been modified by another process."},
        422: {"message": "Unprocessable entity. The request was well-formed but contains semantic errors."},
        429: {"message": "Too many requests. Rate limit exceeded.", "retryAfter": 60},
        500: {"message": "Internal server error. An unexpected error occurred."},
        502: {"message": "Bad gateway. The server received an invalid response from the upstream server."},
        503: {"message": "Service unavailable. The server is currently unable to handle the request."},
        504: {"message": "Gateway timeout. The server did not receive a timely response."}
    }

    if status_code in error_responses:
        return jsonify(error_responses[status_code]), status_code
    return jsonify({"message": f"Error with status code {status_code}"}), status_code

@app.route('/test/validation-error', methods=['POST'])
def trigger_validation_error():
    """Test endpoint to trigger validation errors with field-level details."""
    return jsonify({
        "message": "Validation failed. Please correct the errors and try again.",
        "fieldErrors": {
            "CustomerID": "Customer with ID 'CUST999' does not exist.",
            "Amount": ["Amount must be a positive number.", "Amount exceeds available credit limit."],
            "Email": "Invalid email format. Please enter a valid email address."
        }
    }), 422

@app.route('/test/business-rule-error', methods=['POST'])
def trigger_business_rule_error():
    """Test endpoint to trigger business rule violations."""
    return jsonify({
        "message": "Cannot delete customer with open orders. Please close all orders before deleting."
    }), 422

@app.route('/test/batch-error', methods=['POST'])
def trigger_batch_error():
    """Test endpoint to simulate batch operation failures."""
    return jsonify({
        "message": "Batch execution failed. 2 of 5 operations failed.",
        "failedOperations": [
            {"index": 1, "error": "Customer 'CUST001' not found."},
            {"index": 3, "error": "Validation failed for order SO-003."}
        ]
    }), 400

@app.route('/test/timeout', methods=['GET'])
def trigger_timeout():
    """Test endpoint to simulate a timeout by sleeping longer than typical timeout."""
    time.sleep(65)  # Sleep for 65 seconds to trigger client timeout
    return jsonify({"message": "This should not be reached"}), 200

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
    """Handles get_by_id with files array."""
    # Support various test entity IDs for different scenarios
    if entity_id == "999" or entity_id == "888":
        return jsonify({"message": f"Test entity with ID '{entity_id}' was not found."}), 404
    elif entity_id == "error500":
        return jsonify({"message": "Internal server error occurred while processing request."}), 500
    elif entity_id == "error412":
        return jsonify({"message": "The record has been modified by another user."}), 412
    elif entity_id == "error429":
        return jsonify({"message": "Rate limit exceeded.", "retryAfter": 30}), 429
    elif entity_id != "123":
        return jsonify({"message": f"Entity with ID '{entity_id}' not found."}), 404

    return jsonify({
        "id": "123",
        "Name": {"value": "Specific Test Item"},
        "Value": {"value": "Some Value"},
        "IsActive": {"value": True},
        "_links": {
            "files:put": f"/entity/Default/24.200.001/Test/{entity_id}/files/{{filename}}"
        },
        "files": [
            {
                "id": "mock-file-guid",
                "filename": "testfile.txt",
                "href": f"{FILES_PATH}/mock-file-guid"
            }
        ]
    }), 200

@app.route(f'{OLD_ENTITY_PATH}/<entity_id>', methods=['GET'])
def get_by_id_old_api_version(entity_id: str):
    """Handles get_by_id for old API version."""
    if entity_id != "223":
        return jsonify({"error": "Not Found"}), 404

    return jsonify({
        "id": "223",
        "Name": {"value": "Old Specific Test Item"},
        "Value": {"value": "Old Some Value"},
        "IsActive": {"value": True},
        "files": [
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

    # Check for special test cases
    if data and 'Name' in data:
        name_value = data['Name'].get('value', '') if isinstance(data['Name'], dict) else data['Name']

        if name_value == "TriggerValidationError":
            return jsonify({
                "message": "Validation failed",
                "fieldErrors": {
                    "Name": "Name cannot contain special characters.",
                    "Code": "Code is required when Name is specified."
                }
            }), 422
        elif name_value == "TriggerConflict":
            return jsonify({"message": "A record with this name already exists."}), 409
        elif name_value == "TriggerServerError":
            return jsonify({"message": "An unexpected server error occurred."}), 500

    data['id'] = "new-put-entity-id"
    return jsonify(data), 200

@app.route(f'{BASE_ENTITY_PATH}/<entity_id>', methods=['DELETE'])
def delete_by_id(entity_id: str):
    """Handles the delete_by_id method. Returns No Content on success."""
    print(f"Received DELETE for ID: {entity_id}")

    # Special test cases for error scenarios
    if entity_id == "protected":
        return jsonify({"message": "Cannot delete protected entity."}), 403
    elif entity_id == "has_references":
        return jsonify({"message": "Cannot delete entity with active references."}), 409
    elif entity_id == "not_found":
        return jsonify({"message": f"Entity with ID '{entity_id}' not found."}), 404

    return '', 204

@app.route(f'{BASE_ENTITY_PATH}/TestAction', methods=['POST'])
def invoke_action():
    """Handles the invoke_action_test_action method."""
    action_data = request.json
    assert 'entity' in action_data
    assert 'parameters' in action_data
    assert action_data['entity']['Name']['value'] == "ActionEntity"
    assert action_data['parameters']['Param1']['value'] == "ActionParameter"
    return '', 204

@app.route(f'{BASE_ENTITY_PATH}/$adHocSchema', methods=['GET'])
def get_ad_hoc_schema():
    """Handles the get_ad_hoc_schema method."""
    base_schema = {
        "CustomStringField": {"type": "String", "viewName": "UsrCustomField"},
        "CustomNumberField": {"type": "Decimal", "viewName": "UsrCustomNumber"}
    }
    
    # Add different fields based on schema version for testing
    if _schema_version == "v2":
        base_schema["CustomDateField"] = {"type": "DateTime", "viewName": "UsrCustomDate"}
        base_schema["CustomBoolField"] = {"type": "Boolean", "viewName": "UsrCustomBool"}
    
    return jsonify(base_schema), 200

@app.route(f'{BASE_ENTITY_PATH}/<entity_id>/files/<filename>', methods=['PUT'])
def attach_file(entity_id: str, filename: str):
    """Simulates attaching a file to an entity."""
    assert request.content_type == "application/octet-stream"
    assert request.data == b"This is the content of the test file."
    assert request.headers.get("PX-CbFileComment") == "A test comment"
    print(f"File '{filename}' attached to entity '{entity_id}' successfully.")
    return '', 204

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

# --- Generic Inquiry endpoints ---

@app.route('/t/<tenant>/api/odata/gi/<inquiry_name>', methods=['GET'])
def get_inquiry(tenant: str, inquiry_name: str):
    """Simulates a generic inquiry request with different data based on XML version."""
    base_data = {
        "Account Details": {
            "value": [
                {"AccountID": {"value": "1000"}, "AccountName": {"value": "Cash Account"}, "Balance": {"value": 50000.00}},
                {"AccountID": {"value": "2000"}, "AccountName": {"value": "Accounts Receivable"}, "Balance": {"value": 25000.00}},
            ]
        },
        "Customer List": {
            "value": [
                {"CustomerID": {"value": "C001"}, "CustomerName": {"value": "ABC Corp"}, "City": {"value": "New York"}},
                {"CustomerID": {"value": "C002"}, "CustomerName": {"value": "XYZ Ltd"}, "City": {"value": "Chicago"}},
            ]
        },
        "Inventory Items": {
            "value": [
                {"InventoryID": {"value": "INV001"}, "Description": {"value": "Widget A"}, "UnitPrice": {"value": 10.50}},
                {"InventoryID": {"value": "INV002"}, "Description": {"value": "Widget B"}, "UnitPrice": {"value": 15.75}},
            ]
        }
    }
    
    # Add extra data for v2 XML version
    if _xml_version == "v2":
        base_data["Vendor List"] = {
            "value": [
                {"VendorID": {"value": "V001"}, "VendorName": {"value": "Supplier A"}, "City": {"value": "Boston"}},
                {"VendorID": {"value": "V002"}, "VendorName": {"value": "Supplier B"}, "City": {"value": "Seattle"}},
            ]
        }
    
    if inquiry_name in base_data:
        return jsonify(base_data[inquiry_name]), 200
    else:
        # Default response for any other inquiry
        return jsonify({
            "value": [
                {"Account": {"value": f"Test Account 1 ({_xml_version})"}},
                {"Account": {"value": f"Test Account 2 ({_xml_version})"}},
            ]
        }), 200

# --- Performance testing endpoints ---

@app.route('/test/delay/<int:seconds>', methods=['GET'])
def add_delay(seconds: int):
    """Add artificial delay for performance testing."""
    time.sleep(min(seconds, 10))  # Cap at 10 seconds for safety
    return jsonify({"delayed": seconds}), 200

@app.route('/test/cache/reset', methods=['POST'])  
def reset_cache_test_state():
    """Reset all test state for cache testing."""
    global _schema_version, _xml_version
    _schema_version = "v1"
    _xml_version = "v1"
    return jsonify({"message": "Test state reset"}), 200