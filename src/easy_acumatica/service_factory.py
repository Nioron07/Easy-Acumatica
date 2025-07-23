# src/easy_acumatica/service_factory.py

from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import os
import requests
import textwrap
from functools import update_wrapper
from typing import TYPE_CHECKING, Any, Dict, Union

from .core import BaseDataClassModel, BaseService
from .odata import QueryOptions

if TYPE_CHECKING:
    from .client import AcumaticaClient

def _generate_docstring(service_name: str, operation_id: str, details: Dict[str, Any], is_get_files: bool = False) -> str:
    """Generates a detailed docstring from OpenAPI schema details."""

    if is_get_files:
        description = f"Retrieves files attached to a {service_name} entity."
        args_section = [
            "Args:",
            "    entity_id (str): The primary key of the entity.",
            "    api_version (str, optional): The API version to use for this request."
        ]
        returns_section = "Returns:\n    A list of file information dictionaries."
        full_docstring = f"{description}\n\n"
        full_docstring += "\n".join(args_section) + "\n\n"
        full_docstring += returns_section
        return textwrap.indent(full_docstring, '    ')


    summary = details.get("summary", "No summary available.")
    description = f"{summary} for the {service_name} entity."

    args_section = ["Args:"]
    # Handle request body for PUT/POST
    if 'requestBody' in details:
        try:
            ref = details['requestBody']['content']['application/json']['schema']['$ref']
            model_name = ref.split('/')[-1]
            if "InvokeAction" in operation_id:
                args_section.append(f"    invocation (models.{model_name}): The action invocation data.")
            else:
                args_section.append(f"    data (Union[dict, models.{model_name}]): The entity data to create or update.")
        except KeyError:
            args_section.append("    data (dict): The entity data.")

    # Handle path parameters like ID
    if 'parameters' in details:
        for param in details['parameters']:
            if param['$ref'].split("/")[-1] == "id":
                args_section.append("    entity_id (str): The primary key of the entity.")

    if "PutFile" in operation_id:
        args_section.append("    entity_id (str): The primary key of the entity.")
        args_section.append("    filename (str): The name of the file to upload.")
        args_section.append("    data (bytes): The file content.")
        args_section.append("    comment (str, optional): A comment about the file.")

    if any(s in operation_id for s in ["GetList", "GetById", "GetByKeys", "PutEntity"]):
        args_section.append("    options (QueryOptions, optional): OData query options.")

    args_section.append("    api_version (str, optional): The API version to use for this request.")

    # Handle return value
    returns_section = "Returns:\n"
    try:
        response_schema = details['responses']['200']['content']['application/json']['schema']
        if '$ref' in response_schema:
            model_name = response_schema['$ref'].split('/')[-1]
            returns_section += f"    A dictionary or a {model_name} data model instance."
        elif response_schema.get('type') == 'array':
            item_ref = response_schema['items']['$ref']
            model_name = item_ref.split('/')[-1]
            returns_section += f"    A list of dictionaries or {model_name} data model instances."
        else:
            returns_section += "    The JSON response from the API."
    except KeyError:
        if details['responses'].get('204'):
            returns_section += "    None."
        else:
            returns_section += "    The JSON response from the API or None."


    full_docstring = f"{description}\n\n"
    if len(args_section) > 1:
        full_docstring += "\n".join(args_section) + "\n\n"
    full_docstring += returns_section

    return textwrap.indent(full_docstring, '    ')

def generate_inquiry_docstring(xml_file_path: str, container_name: str, inquiry_name: str) -> str:
    """
    Parses an OData XML file to generate a docstring for a specific inquiry.

    Args:
        xml_file_path (str): The path to the local XML metadata file.
        container_name (str): The name of the EntityContainer to search within (e.g., "Default").
        inquiry_name (str): The name of the EntitySet to generate the docstring for (e.g., "PE All Items").

    Returns:
        A formatted docstring string.
    """
    try:
        namespaces = {'edm': 'http://docs.oasis-open.org/odata/ns/edm'}
        tree = ET.parse(xml_file_path)
        root = tree.getroot()

        # 1. Find the EntityType directly using the provided name
        entity_type_path = f'.//edm:EntityType[@Name="{container_name}"]'
        entity_type = root.find(entity_type_path, namespaces)

        if entity_type is None:
            return f"Error: EntityType '{container_name}' not found in the XML."

        # 2. Extract all properties (the fields) from that EntityType
        properties = [prop.attrib for prop in entity_type.findall('edm:Property', namespaces)]

        # 3. Format the fields and the final docstring
        if properties:
            fields_str = "\n".join([f"    - {prop.get('Name')} ({prop.get('Type').split('.', 1)[-1]})" for prop in properties])
        else:
            fields_str = "    (No properties found for this EntityType)"

        docstring = f"""Generic Inquiry for the '{inquiry_name}' endpoint

    Args:
        options (QueryOptions, optional): OData query options like $filter, $top, etc.

    Returns:
        A dictionary containing the API response, typically a list of records with the following fields:
{fields_str}
    """
        return docstring

    except (FileNotFoundError, ET.ParseError) as e:
        return f"Error processing XML file: {e}"


class ServiceFactory:
    """
    Dynamically builds service classes and their methods from an Acumatica OpenAPI schema.
    """
    def __init__(self, client: AcumaticaClient, schema: Dict[str, Any]):
        self._client = client
        self._schema = schema

    def build_services(self) -> Dict[str, BaseService]:
        """
        Parses all schemas (OpenAPI and OData XML) and generates all
        corresponding services in a single dictionary.
        """
        services: Dict[str, BaseService] = {}

        # --- Part 1: Build services from OpenAPI Schema ---
        print("\n--- Building services from OpenAPI Schema ---")
        paths = self._schema.get("paths", {})
        tags_to_ops: Dict[str, list] = {}
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if tag not in tags_to_ops: tags_to_ops[tag] = []
                    tags_to_ops[tag].append((path, http_method, details))

        for tag, operations in tags_to_ops.items():
            service_class = type(f"{tag}Service", (BaseService,), {
                "__init__": lambda s, client, entity_name=tag: BaseService.__init__(s, client, entity_name)
            })
            service_instance = service_class(self._client)
            for path, http_method, details in operations:
                self._add_method_to_service(service_instance, path, http_method, details)
            services[tag] = service_instance
        print(f"Completed building {len(services)} services from OpenAPI schema.")


        tag = "Inquirie"
        service_class = type(f"{tag}Service", (BaseService,), {
            "__init__": lambda s, client, entity_name=tag: BaseService.__init__(s, client, entity_name)
        })
        inquiries_service = service_class(self._client)
        services[tag] = inquiries_service


        # Now populate it using the refactored loop
        try:
            inquiries_service = services["Inquirie"]
            xml_file_path = self._fetch_gi_xml()
            self._xml_file_path = xml_file_path
            namespaces = {'edmx': 'http://docs.oasis-open.org/odata/ns/edmx', 'edm': 'http://docs.oasis-open.org/odata/ns/edm'}
            tree = ET.parse(xml_file_path)
            container = tree.find('.//edm:EntityContainer[@Name="Default"]', namespaces)

            if container is not None:
                for entity_set in container.findall('edm:EntitySet', namespaces):
                    original_name = entity_set.get('Name')
                    entity_type = entity_set.get('EntityType')
                    if not original_name: continue
                    method_name = re.sub(r"[-\s]+", "_", original_name)
                    self._add_inquiry_method(inquiries_service, original_name, method_name, entity_type)

        except Exception as e:
            print(f"Could not build methods for Inquiries service: {e}")

        print("\n--- Build Complete ---")
        return services
    
    def _fetch_gi_xml(self):
        """
        Fetches the Generic Inquiries XML document and saves it to a .metadata folder inside the package directory.
        """
        metadata_url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/$metadata"
        print(f"Fetching schema from {metadata_url}...")

        try:
            response = requests.get(
                url=metadata_url,
                auth=(self._client.username, self._client._password)
            )
            response.raise_for_status()

            # Determine package root directory based on this file's location
            package_dir = os.path.dirname(os.path.abspath(__file__))
            metadata_dir = os.path.join(package_dir, ".metadata")
            os.makedirs(metadata_dir, exist_ok=True)

            output_path = os.path.join(metadata_dir, "odata_schema.xml")
            with open(output_path, 'wb') as f:
                f.write(response.content)

            print(f"Schema saved to {output_path}")
            return output_path

        except requests.exceptions.RequestException as e:
            print(f"Error fetching metadata: {e}")
            raise

    def _add_get_files_method(self, service: BaseService):
        """Adds the get_files method to a service."""

        def get_files(self, entity_id: str, api_version: str | None = None):
            return self._get_files(entity_id=entity_id, api_version=api_version)

        docstring = _generate_docstring(service.entity_name, "", {}, is_get_files=True)
        get_files.__doc__ = docstring
        final_method = update_wrapper(get_files, get_files)
        final_method.__name__ = "get_files"
        service.get_files = final_method.__get__(service, BaseService)

    def _add_method_to_service(self, service: BaseService, path: str, http_method: str, details: Dict[str, Any]):
        """
        Creates a single Python method based on an API operation and attaches it to a service.
        """
        operation_id = details.get("operationId", "")
        if not operation_id or '_' not in operation_id: return

        name_part = operation_id.split('_', 1)[-1]
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name_part)
        method_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        method_name = method_name.replace('__', '_')

        docstring = _generate_docstring(service.entity_name, operation_id, details)

        def get_list(self, options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(options=options, api_version=api_version)

        def get_by_id(self, entity_id: Union[str, list], options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(entity_id=entity_id, options=options, api_version=api_version)

        def put_entity(self, data: Union[dict, BaseDataClassModel], options: QueryOptions | None = None, api_version: str | None = None):
            return self._put(data, options=options, api_version=api_version)

        def delete_by_id(self, entity_id: Union[str, list], api_version: str | None = None):
            return self._delete(entity_id=entity_id, api_version=api_version)

        def put_file(self, entity_id: str, filename: str, data: bytes, comment: str | None = None, api_version: str | None = None):
            return self._put_file(entity_id, filename, data, comment=comment, api_version=api_version)

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

        template = None
        if "PutFile" in operation_id:
            template = put_file
            self._add_get_files_method(service)
        elif "GetAdHocSchema" in operation_id:
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
            return

        template.__doc__ = docstring
        final_method = update_wrapper(template, template)
        final_method.__name__ = method_name

        setattr(service, method_name, final_method.__get__(service, BaseService))

    def _add_inquiry_method(self, service: BaseService, inquiry_name: str, method_name: str, entity_type: str):
        """
        Creates a simple wrapper method that calls the BaseService._get_inquiry method.
        """
    
        # This factory function creates the method we will attach
        def create_inquiry_method(name_of_inquiry: str):
            
            # This is the simplified function that will be attached
            def api_method(self, options: QueryOptions | None = None) -> Any:
                """Fetches data for the Generic Inquiry: {name_of_inquiry}"""
                # It just calls the method on its base class!
                return self._get_inquiry(name_of_inquiry, options=options)
            
            return api_method

        # Create the method and attach it to the service instance
        docstring = generate_inquiry_docstring(self._xml_file_path, entity_type.split('.', 1)[-1], inquiry_name=inquiry_name)
        inquiry_method = create_inquiry_method(inquiry_name)
        inquiry_method.__doc__ = docstring
        inquiry_method.__name__ = method_name
        
        setattr(service, method_name, inquiry_method.__get__(service, BaseService))

