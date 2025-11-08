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
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetList",
                    "summary": "Retrieves a list of Test entities.",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/TestModel"}
                                    }
                                }
                            }
                        }
                    }
                },
                "put": {
                    "tags": ["Test"],
                    "operationId": "Test_PutEntity",
                    "summary": "Creates or updates a Test entity.",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TestModel"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestModel"}
                                }
                            }
                        }
                    }
                },
            },
            "/Test/{id}": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetById",
                    "summary": "Retrieves a Test entity by its ID.",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestModel"}
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "tags": ["Test"],
                    "operationId": "Test_DeleteById",
                    "summary": "Deletes a Test entity by its ID.",
                    "responses": {
                        "204": {"description": "Success"}
                    }
                },
            },
            "/Test/TestAction": {
                "post": {
                    "tags": ["Test"],
                    "operationId": "Test_InvokeAction_TestAction",
                    "summary": "Invokes the TestAction on a Test entity.",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/TestAction"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestModel"}
                                }
                            }
                        }
                    }
                }
            },
            "/Test/$adHocSchema": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetAdHocSchema",
                    "summary": "Retrieves the ad-hoc schema for a Test entity.",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestModel"}
                                }
                            }
                        }
                    }
                }
            },
            "/Test/{ids}/files": {
                "get": {
                    "tags": ["Test"],
                    "operationId": "Test_GetFiles",
                    "summary": "Gets files attached to a Test entity.",
                    "parameters": [{"$ref": "#/components/parameters/ids"}],
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/FileLink"}
                                    }
                                }
                            }
                        }
                    }
                }
            },
            "/Test/{ids}/files/{filename}": {
                "put": {
                    "tags": ["Test"],
                    "operationId": "Test_PutFile",
                    "summary": "Attaches a file to a Test entity.",
                    "parameters": [{"$ref": "#/components/parameters/ids"}, {"$ref": "#/components/parameters/filename"}],
                    "responses": {"204": {"description": "File attached"}}
                }
            },
            "/TestCustomGI": {
                "put": {
                    "tags": ["TestCustomGI"],
                    "operationId": "TestCustomGI_PutEntity",
                    "summary": "Queries the TestCustomGI generic inquiry.",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {"type": "object"}
                            }
                        }
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestCustomGI"}
                                }
                            }
                        }
                    }
                },
                "get": {
                    "tags": ["TestCustomGI"],
                    "operationId": "TestCustomGI_GetList",
                    "summary": "Retrieves TestCustomGI generic inquiry results.",
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/TestCustomGI"}
                                }
                            }
                        }
                    }
                }
            }
        },
        "tags": [
            {
                "name": "Test",
                "description": "Test Entity (AR303000)"
            },
            {
                "name": "TestCustomGI",
                "description": "Test Custom Generic Inquiry (GI123456)"
            }
        ],
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
                                },
                                "Owner": {"$ref": "#/components/schemas/TestContact"},
                                "RelatedItems": {
                                    "type": "array",
                                    "items": {"$ref": "#/components/schemas/TestRelatedItem"}
                                }
                            },
                        },
                    ]
                },
                "TestContact": {
                    "type": "object",
                    "properties": {
                        "ContactID": {"type": "integer"},
                        "DisplayName": {"$ref": "#/components/schemas/StringValue"},
                        "Email": {"$ref": "#/components/schemas/StringValue"},
                        "Phone": {"$ref": "#/components/schemas/StringValue"},
                        "Address": {"$ref": "#/components/schemas/TestAddress"},
                        "IsActive": {"$ref": "#/components/schemas/BooleanValue"}
                    }
                },
                "TestAddress": {
                    "type": "object",
                    "properties": {
                        "AddressLine1": {"$ref": "#/components/schemas/StringValue"},
                        "AddressLine2": {"$ref": "#/components/schemas/StringValue"},
                        "City": {"$ref": "#/components/schemas/StringValue"},
                        "State": {"$ref": "#/components/schemas/StringValue"},
                        "PostalCode": {"$ref": "#/components/schemas/StringValue"},
                        "Country": {"$ref": "#/components/schemas/StringValue"}
                    }
                },
                "TestRelatedItem": {
                    "type": "object",
                    "properties": {
                        "ItemID": {"$ref": "#/components/schemas/StringValue"},
                        "Description": {"$ref": "#/components/schemas/StringValue"},
                        "Quantity": {"type": "number", "format": "decimal"},
                        "RelatedContact": {"$ref": "#/components/schemas/TestContact"}
                    }
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
                "TestCustomGI": {
                    "type": "object",
                    "properties": {
                        "TestCustomGIDetails": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string", "format": "uuid"},
                                    "rowNumber": {"type": "integer"},
                                    "ItemID": {"$ref": "#/components/schemas/StringValue"},
                                    "Description": {"$ref": "#/components/schemas/StringValue"},
                                    "QtyOnHand": {"type": "number", "format": "decimal"},
                                    "custom": {"type": "object"}
                                }
                            }
                        }
                    }
                }
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
        "get": {
            "tags": ["ExtendedTest"],
            "operationId": "ExtendedTest_GetList",
            "summary": "Retrieves a list of ExtendedTest entities.",
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/ExtendedTestModel"}
                            }
                        }
                    }
                }
            }
        },
        "put": {
            "tags": ["ExtendedTest"],
            "operationId": "ExtendedTest_PutEntity",
            "summary": "Creates or updates an ExtendedTest entity.",
            "requestBody": {
                "content": {
                    "application/json": {
                        "schema": {"$ref": "#/components/schemas/ExtendedTestModel"}
                    }
                }
            },
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ExtendedTestModel"}
                        }
                    }
                }
            }
        },
    }

    base_schema["paths"]["/ExtendedTest/{id}"] = {
        "get": {
            "tags": ["ExtendedTest"],
            "operationId": "ExtendedTest_GetById",
            "summary": "Retrieves an ExtendedTest entity by its ID.",
            "responses": {
                "200": {
                    "description": "Success",
                    "content": {
                        "application/json": {
                            "schema": {"$ref": "#/components/schemas/ExtendedTestModel"}
                        }
                    }
                }
            }
        },
        "delete": {
            "tags": ["ExtendedTest"],
            "operationId": "ExtendedTest_DeleteById",
            "summary": "Deletes an ExtendedTest entity by its ID.",
            "responses": {
                "204": {"description": "Success"}
            }
        },
    }
    
    return base_schema