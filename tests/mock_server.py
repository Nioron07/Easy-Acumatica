from flask import Flask, jsonify, request
from .mock_swagger import get_swagger_json

app = Flask(__name__)

# The endpoint version the client will request
TEST_ENDPOINT_VERSION = "24.200.001"
TEST_ENDPOINT_NAME = "Default"

@app.route('/entity/auth/login', methods=['POST'])
def login():
    """Simulates a successful login."""
    return jsonify({"message": "Logged in successfully"}), 200

@app.route('/entity/auth/logout', methods=['POST'])
def logout():
    """Simulates a successful logout."""
    return jsonify({"message": "Logged out successfully"}), 204

@app.route('/entity', methods=['GET'])
def get_endpoints():
    """
    Provides the list of available API endpoints. The client will parse
    this to find the correct version for the 'Default' endpoint.
    """
    return jsonify({
        "endpoints": [
            {"name": TEST_ENDPOINT_NAME, "version": TEST_ENDPOINT_VERSION},
            {"name": "AnotherEndpoint", "version": "23.100.001"}
        ]
    }), 200

@app.route(f'/entity/{TEST_ENDPOINT_NAME}/{TEST_ENDPOINT_VERSION}/swagger.json', methods=['GET'])
def get_swagger(endpoint_name=TEST_ENDPOINT_NAME, version=TEST_ENDPOINT_VERSION):
    """
    Serves the dynamically generated swagger.json for our test service.
    """
    return jsonify(get_swagger_json()), 200

# You can add more specific endpoints here as your tests grow.
# For example, a GET request handler for the Test model:
@app.route(f'/entity/{TEST_ENDPOINT_NAME}/{TEST_ENDPOINT_VERSION}/Test/123', methods=['GET'])
def get_test_by_id(endpoint_name=TEST_ENDPOINT_NAME, version=TEST_ENDPOINT_VERSION, id='123'):
    """Handles a specific GetById request for testing purposes."""
    return jsonify({
        "id": "123",
        "Name": {"value": "Test Name"},
        "Value": {"value": "Test Value"},
        "IsActive": {"value": True}
    }), 200