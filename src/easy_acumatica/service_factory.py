from __future__ import annotations
from typing import Any, Dict, Union
from functools import update_wrapper

from .core import BaseService, BaseDataClassModel
from .odata import QueryOptions

class ServiceFactory:
    """
    Dynamically builds service classes and their methods from an Acumatica OpenAPI schema.

    This factory is the core of the dynamic client. It inspects the `paths` section
    of the `swagger.json` file and programmatically constructs service classes
    (e.g., `ContactService`, `SalesOrderService`) and attaches methods to them
    that correspond to the available API operations (e.g., `get_by_id`, `put_entity`).

    The process involves these key steps:
    1.  **Grouping by Tags**: It first organizes all API paths (like `/Contact/{id}`)
        by their primary "tag" (e.g., "Contact"). Each tag corresponds to one service.
    2.  **Dynamic Class Creation**: For each tag, it creates a new class that inherits
        from the `BaseService`, ensuring all services share the core request logic.
    3.  **Dynamic Method Creation**: For each operation within a tag (GET, PUT, POST),
        it creates a corresponding Python method with a proper signature.
    4.  **Method Binding**: It then attaches these dynamically created methods to the
        service class instances, making them callable (e.g., `client.contacts.get_by_id(...)`).
    """
    def __init__(self, client: "AcumaticaClient", schema: Dict[str, Any]):
        """
        Initializes the factory.

        Args:
            client: The active AcumaticaClient instance. This is needed so that
                    the created services can make API calls.
            schema: The full OpenAPI/swagger JSON schema dictionary.
        """
        self._client = client
        self._schema = schema

    def build_services(self) -> Dict[str, BaseService]:
        """
        Parses the entire schema and generates all corresponding services and methods.

        This is the main entry point for the factory. It orchestrates the entire
        process of building the service layer.

        Returns:
            A dictionary mapping the service tag (e.g., "Contact") to its fully
            constructed service instance.
        """
        # This dictionary will hold the final, instantiated service objects.
        services: Dict[str, BaseService] = {}
        paths = self._schema.get("paths", {})
        
        # --- Step 1: Group all API paths by their primary tag ---
        # A tag in the schema corresponds to a service (e.g., the "Contact" tag
        # groups all contact-related operations).
        tags_to_ops: Dict[str, list] = {}
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if tag not in tags_to_ops: tags_to_ops[tag] = []
                    tags_to_ops[tag].append((path, http_method, details))

        # --- Step 2: Create a service class for each tag ---
        for tag, operations in tags_to_ops.items():
            # Dynamically create a new class, like `ContactService(BaseService): ...`
            service_class = type(f"{tag}Service", (BaseService,), {
                # The __init__ method calls the parent BaseService's __init__
                "__init__": lambda self, client, entity_name=tag: BaseService.__init__(self, client, entity_name)
            })
            # Instantiate the newly created service class
            services[tag] = service_class(self._client)
            
            # --- Step 3: Add methods to the new service instance ---
            for path, http_method, details in operations:
                self._add_method_to_service(services[tag], path, http_method, details)
        
        return services

    def _add_method_to_service(self, service: BaseService, path: str, http_method: str, details: Dict[str, Any]):
        """
        Creates a single Python method based on an API operation and attaches it to a service.

        This function inspects an operation's ID (e.g., "Contact_GetById") and its
        HTTP method (e.g., "get") to determine which base function from `BaseService`
        to call and what the Python method's signature should be.

        Args:
            service: The service instance to which the method will be attached.
            path: The API path for the operation (e.g., "/Contact/{id}").
            http_method: The HTTP verb (e.g., "get", "put").
            details: The full schema dictionary for this specific operation.
        """
        # The operationId provides a unique name for the method.
        # e.g., "Contact_GetById" -> "getbyid"
        operation_id = details.get("operationId", "")
        if not operation_id or '_' not in operation_id: return
        method_name = operation_id.split('_', 1)[-1].lower()

        # --- Step 4: Define Method Templates with Correct Signatures ---
        # These are templates for the real methods we will generate. Each one has the
        # correct arguments for its corresponding operation and calls the
        # appropriate underlying function in BaseService (e.g., _get, _put).
        
        def get_list(self, options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(options=options, api_version=api_version)

        def get_by_id(self, entity_id: Union[str, list], options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(entity_id=entity_id, options=options, api_version=api_version)

        def put_entity(self, data: Union[dict, BaseDataClassModel], options: QueryOptions | None = None, api_version: str | None = None):
            return self._put(data, options=options, api_version=api_version)

        def delete_by_id(self, entity_id: Union[str, list], api_version: str | None = None):
            return self._delete(entity_id=entity_id, api_version=api_version)

        def invoke_action(self, invocation: BaseDataClassModel, api_version: str | None = None):
            action_name = path.split('/')[-1]
            payload = invocation.build()
            entity_payload = payload.get('entity', {})
            params_payload = payload.get('parameters')


            # Clean entity_payload
            entity_payload = {
                k: v for k, v in payload.get("entity", {}).items()
                if (
                    isinstance(v, dict) and (
                        ("value" in v and v["value"] not in [None, "", [], {}]) or
                        ("value" not in v and any(subv not in [None, "", [], {}] for subv in v.values()))
                    )
                ) or (
                    isinstance(v, list) and any(item not in [None, "", [], {}] for item in v)
                ) or (
                    not isinstance(v, (dict, list)) and v not in [None, "", [], {}]
                )
            }
            print(entity_payload)
                
            return self._post_action(action_name, entity_payload, parameters=params_payload, api_version=api_version)
        
        def get_schema(self, api_version: str | None = None):
            return self._get_schema(api_version=api_version)

        # --- Step 5: Select the Correct Template Based on the API Operation ---
        template = None
        if "GetAdHocSchema" in operation_id:
            template = get_schema
        elif "InvokeAction" in operation_id:
            template = invoke_action
        elif "PutEntity" in operation_id:
            template = put_entity
        elif "GetById" in operation_id or "GetByKeys" in operation_id:
            template = get_by_id
        elif "GetList" in operation_id:
            template = get_list
        elif "DeleteById" in operation_id or "DeleteByKeys" in operation_id:
            template = delete_by_id
        
        if not template:
            return # Skip if no pattern matches

        # --- Step 6: Bind the Method to the Service Instance ---
        # `update_wrapper` copies metadata (like the docstring and name) from the
        # template to our new dynamic method.
        final_method = update_wrapper(template, template)
        final_method.__name__ = method_name
        
        # `__get__` binds the function to the instance, making `self` work correctly.
        # This effectively turns our `final_method` into a real instance method.
        setattr(service, method_name, final_method.__get__(service, BaseService))