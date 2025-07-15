def get_swagger_json():
    """
    Returns a mock OpenAPI (swagger) schema tailored for testing.
    
    This schema defines:
    - A 'Test' service with all standard REST operations (GetList, GetById, Put, Delete, etc.).
    - A 'TestModel' with basic fields (Name, Value, IsActive).
    - An action 'TestAction' to verify the action invocation logic.
    - Necessary primitive wrapper types (StringValue, BooleanValue).
    """
    return {
        "openapi": "3.0.1",
        "info": {"title": "Test/v1", "version": "1"},
        "paths": {
            "/Test": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetList",
                    "responses": {"200": {"description": "Success"}},
                },
                "put": {
                    "tags": ["Test"],
                    "operationId": "Test_PutEntity",
                    "requestBody": {
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TestModel"}}}
                    },
                    "responses": {"200": {"description": "Success"}},
                },
            },
            "/Test/{id}": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetById",
                    "responses": {"200": {"description": "Success"}},
                },
                "delete": {
                    "tags": ["Test"],
                    "operationId": "Test_DeleteById",
                    "responses": {"204": {"description": "Success"}},
                },
            },
            "/Test/TestAction": {
                "post": {
                    "tags": ["Test"],
                    "operationId": "Test_InvokeAction_TestAction",
                    "requestBody": {
                        "content": {"application/json": {"schema": {"$ref": "#/components/schemas/TestAction"}}}
                    },
                    "responses": {"204": {"description": "Success"}},
                }
            },
            "/Test/$adHocSchema": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetAdHocSchema",
                    "responses": {"200": {"description": "Success"}},
                }
            }
        },
        "components": {
            "schemas": {
                "TestModel": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Entity"},
                        {
                            "type": "object",
                            "properties": {
                                "Name": {"$ref": "#/components/schemas/StringValue"},
                                "Value": {"$ref": "#/components/schemas/StringValue"},
                                "IsActive": {"$ref": "#/components/schemas/BooleanValue"},
                            },
                        },
                    ]
                },
                "TestAction": {
                    "type": "object",
                    "properties": {
                        "entity": {"$ref": "#/components/schemas/TestModel"},
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "Param1": {"$ref": "#/components/schemas/StringValue"}
                            }
                        }
                    }
                },
                "Entity": {"type": "object", "properties": {}},
                "StringValue": {"type": "object", "properties": {"value": {"type": "string"}}},
                "BooleanValue": {"type": "object", "properties": {"value": {"type": "boolean"}}},
            }
        },
    }