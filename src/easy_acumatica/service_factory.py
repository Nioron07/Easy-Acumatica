from __future__ import annotations
from typing import Any, Dict, Type, Union
from functools import update_wrapper

from .core import BaseService, BaseDataClassModel
from .odata import QueryOptions

class ServiceFactory:
    """
    Dynamically builds service classes and their methods from an Acumatica OpenAPI schema.
    """
    def __init__(self, client: "AcumaticaClient", schema: Dict[str, Any]):
        self._client = client
        self._schema = schema

    def build_services(self) -> Dict[str, BaseService]:
        services: Dict[str, BaseService] = {}
        paths = self._schema.get("paths", {})
        
        # Group all operations by their primary tag
        tags_to_ops: Dict[str, list] = {}
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if tag not in tags_to_ops: tags_to_ops[tag] = []
                    tags_to_ops[tag].append((path, http_method, details))

        # Create a service for each tag
        for tag, operations in tags_to_ops.items():
            service_class = type(f"{tag}Service", (BaseService,), {
                "__init__": lambda self, client, entity_name=tag: BaseService.__init__(self, client, entity_name)
            })
            services[tag] = service_class(self._client)
            
            for path, http_method, details in operations:
                self._add_method_to_service(services[tag], path, http_method, details)
        
        return services

    def _add_method_to_service(self, service: BaseService, path: str, http_method: str, details: Dict[str, Any]):
        operation_id = details.get("operationId", "")
        if not operation_id or '_' not in operation_id: return
        method_name = operation_id.split('_', 1)[-1].lower()

        # --- THIS IS THE FINAL LOGIC ---
        # It creates a unique, correctly-signatured function for each API operation
        
        # Default signature
        def generic_template(self, *args, **kwargs):
            raise NotImplementedError(f"Method {method_name} is not implemented.")

        template = generic_template

        if "GetAdHocSchema" in operation_id:
            def get_schema(self, api_version: str | None = None):
                return self._get_schema(api_version=api_version)
            template = get_schema
            
        elif "InvokeAction" in operation_id:
            def invoke_action(self, invocation: BaseDataClassModel, api_version: str | None = None):
                action_name = path.split('/')[-1]
                payload = invocation.build()
                entity_payload = payload.get('entity', {})
                params_payload = payload.get('parameters')
                return self._post_action(action_name, entity_payload, parameters=params_payload, api_version=api_version)
            template = invoke_action

        elif "PutEntity" in operation_id:
            def put_entity(self, data: Union[dict, BaseDataClassModel], options: QueryOptions | None = None, api_version: str | None = None):
                return self._put(data, options=options, api_version=api_version)
            template = put_entity

        elif "GetById" in operation_id or "GetByKeys" in operation_id:
            def get_by_id(self, entity_id: Union[str, list], options: QueryOptions | None = None, api_version: str | None = None):
                return self._get(entity_id=entity_id, options=options, api_version=api_version)
            template = get_by_id

        elif "GetList" in operation_id:
            def get_list(self, options: QueryOptions | None = None, api_version: str | None = None):
                return self._get(options=options, api_version=api_version)
            template = get_list

        elif "DeleteById" in operation_id or "DeleteByKeys" in operation_id:
            def delete_by_id(self, entity_id: Union[str, list], api_version: str | None = None):
                return self._delete(entity_id=entity_id, api_version=api_version)
            template = delete_by_id

        # Bind the dynamically created method to the service instance
        final_method = update_wrapper(template, template)
        final_method.__name__ = method_name
        setattr(service, method_name, final_method.__get__(service, BaseService))