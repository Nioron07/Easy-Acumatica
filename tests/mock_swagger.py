# tests/mock_swagger.py

def get_swagger_json():
    """
    Returns the base mock OpenAPI (swagger) schema.
    """
    return {
        "openapi": "3.0.1",
        "info": {"title": "Test/v1", "version": "1"},
        "paths": {
            "/Test": {
                "get": {"tags": ["Test"], "operationId": "Test_GetList", "summary": "Retrieves a list of Test entities.", "responses": {"200": {"description": "Success"}}},
                "put": {"tags": ["Test"], "operationId": "Test_PutEntity", "summary": "Creates or updates a Test entity.", "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/TestModel"}}}}, "responses": {"200": {"description": "Success"}}},
            },
            "/Test/{id}": {
                "get": {"tags": ["Test"], "operationId": "Test_GetById", "summary": "Retrieves a Test entity by its ID.", "responses": {"200": {"description": "Success"}}},
                "delete": {"tags": ["Test"], "operationId": "Test_DeleteById", "summary": "Deletes a Test entity by its ID.", "responses": {"204": {"description": "Success"}}},
            },
            "/Test/TestAction": {
                "post": {"tags": ["Test"], "operationId": "Test_InvokeAction_TestAction", "summary": "Invokes the TestAction on a Test entity.", "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/TestAction"}}}}, "responses": {"204": {"description": "Success"}}}
            },
            "/Test/$adHocSchema": {
                "get": {"tags": ["Test"], "operationId": "Test_GetAdHocSchema", "summary": "Retrieves the ad-hoc schema for a Test entity.", "responses": {"200": {"description": "Success"}}}
            },
            "/Test/{ids}/files/{filename}": {
                "put": {
                    "tags": ["Test"], "operationId": "Test_PutFile", "summary": "Attaches a file to a Test entity.",
                    "parameters": [{"$ref": "#/components/parameters/ids"}, {"$ref": "#/components/parameters/filename"}],
                    "responses": {"204": {"description": "File attached"}}
                }
            }
        },
        "components": {
            "parameters": {
                "ids": {"name": "ids", "in": "path", "required": True, "schema": {"type": "string"}},
                "filename": {"name": "filename", "in": "path", "required": True, "schema": {"type": "string"}}
            },
            "schemas": {
                "TestModel": {
                    "allOf": [
                        {"$ref": "#/components/schemas/Entity"},
                        {
                            "type": "object",
                            "properties": {
                                "id": {"$ref": "#/components/schemas/GuidValue"},
                                "Name": {"$ref": "#/components/schemas/StringValue"},
                                "Value": {"$ref": "#/components/schemas/StringValue"},
                                "IsActive": {"$ref": "#/components/schemas/BooleanValue"},
                                "files": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/FileLink"}
                                }
                            },
                        },
                    ]
                },
                "FileLink": {
                    "type": "object",
                    "properties": {
                        "id": {"type": "string", "format": "uuid"},
                        "filename": {"type": "string"},
                        "href": {"type": "string"},
                        "comment": {"type": "string", "nullable": True}
                    }
                },
                "TestAction": {
                    "required": ["entity"],
                    "type": "object",
                    "properties": {
                        "entity": {"$ref": "#/components/schemas/TestModel"},
                        "parameters": {"type": "object", "properties": {"Param1": {"$ref": "#/components/schemas/StringValue"}}}
                    }
                },
                "Entity": {"type": "object", "properties": {}},
                "StringValue": {"type": "object", "properties": {"value": {"type": "string"}}},
                "GuidValue": {"type": "object", "properties": {"value": {"type": "string", "format": "uuid"}}},
                "BooleanValue": {"type": "object", "properties": {"value": {"type": "boolean"}}},
            }
        },
    }


def get_modified_swagger_json():
    """
    Returns a modified version of the swagger schema to test differential caching.
    This version adds new fields and models to simulate schema changes.
    """
    base_schema = get_swagger_json()
    
    # Modify the TestModel to add new fields
    test_model = base_schema["components"]["schemas"]["TestModel"]
    test_model["allOf"][1]["properties"].update({
        "NewField": {"$ref": "#/components/schemas/StringValue"},
        "CreatedDate": {"$ref": "#/components/schemas/DateTimeValue"},
        "ModifiedBy": {"$ref": "#/components/schemas/StringValue"},
    })
    
    # Add a new model to test model additions
    base_schema["components"]["schemas"]["ExtendedTestModel"] = {
        "allOf": [
            {"$ref": "#/components/schemas/TestModel"},
            {
                "type": "object",
                "properties": {
                    "ExtensionField": {"$ref": "#/components/schemas/StringValue"},
                    "Priority": {"$ref": "#/components/schemas/IntValue"},
                }
            }
        ]
    }
    
    # Add DateTimeValue and IntValue schemas
    base_schema["components"]["schemas"]["DateTimeValue"] = {
        "type": "object", 
        "properties": {"value": {"type": "string", "format": "date-time"}}
    }
    base_schema["components"]["schemas"]["IntValue"] = {
        "type": "object", 
        "properties": {"value": {"type": "integer"}}
    }
    
    # Add new paths for ExtendedTest service
    base_schema["paths"]["/ExtendedTest"] = {
        "get": {"tags": ["ExtendedTest"], "operationId": "ExtendedTest_GetList", "summary": "Retrieves a list of ExtendedTest entities.", "responses": {"200": {"description": "Success"}}},
        "put": {"tags": ["ExtendedTest"], "operationId": "ExtendedTest_PutEntity", "summary": "Creates or updates an ExtendedTest entity.", "requestBody": {"content": {"application/json": {"schema": {"$ref": "#/components/schemas/ExtendedTestModel"}}}}, "responses": {"200": {"description": "Success"}}},
    }
    
    base_schema["paths"]["/ExtendedTest/{id}"] = {
        "get": {"tags": ["ExtendedTest"], "operationId": "ExtendedTest_GetById", "summary": "Retrieves an ExtendedTest entity by its ID.", "responses": {"200": {"description": "Success"}}},
        "delete": {"tags": ["ExtendedTest"], "operationId": "ExtendedTest_DeleteById", "summary": "Deletes an ExtendedTest entity by its ID.", "responses": {"204": {"description": "Success"}}},
    }
    
    return base_schema