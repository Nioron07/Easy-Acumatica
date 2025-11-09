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

def to_snake_case(name: str) -> str:
    """
    Convert a service name to snake_case form without pluralization.

    Args:
        name: The service name in PascalCase (e.g., 'SalesOrder', 'Company', 'Branch')

    Returns:
        snake_case name (e.g., 'sales_order', 'company', 'branch', 'inquiries')

    Examples:
        >>> to_snake_case('SalesOrder')
        'sales_order'
        >>> to_snake_case('Company')
        'company'
        >>> to_snake_case('Inquiries')
        'inquiries'
    """
    # Convert PascalCase to snake_case
    return ''.join(['_' + c.lower() if c.isupper() else c for c in name]).lstrip('_')

def _generate_docstring(service_name: str, operation_id: str, details: Dict[str, Any], is_get_files: bool = False, is_get_by_keys: bool = False) -> str:
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

    if is_get_by_keys:
        description = f"Retrieves a {service_name} entity by its key field values."
        args_section = [
            "Args:",
            "    **key_fields: Key field values as keyword arguments (e.g., CustomerID='ABCCOMP').",
            "                  The key values will be appended to the URL path as: /{value1}/{value2}/...",
            "    options (QueryOptions, optional): OData query options like $expand, $select, etc.",
            "    api_version (str, optional): The API version to use for this request."
        ]
        returns_section = "Returns:\n    A dictionary containing the entity data."
        example_section = [
            "Example:",
            f"    # For a Customer entity:",
            f"    customer = service.get_by_keys(CustomerID='ABCCOMP')",
            f"    # This creates URL: .../Customer/ABCCOMP"
        ]
        full_docstring = f"{description}\n\n"
        full_docstring += "\n".join(args_section) + "\n\n"
        full_docstring += returns_section + "\n\n"
        full_docstring += "\n".join(example_section)
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

    if any(s in operation_id for s in ["GetList", "GetById", "PutEntity"]):
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
            fields_str = "\n".join([f"        - {prop.get('Name')} ({prop.get('Type').split('.', 1)[-1]})" for prop in properties])
        else:
            fields_str = "        (No properties found for this EntityType)"

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
        paths = self._schema.get("paths", {})
        tags_to_ops: Dict[str, list] = {}
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if tag not in tags_to_ops: tags_to_ops[tag] = []
                    tags_to_ops[tag].append((path, http_method, details))

        for tag, operations in tags_to_ops.items():
            # Create get_signature method for this service
            def create_get_signature_method():
                def get_signature(self, method_name: str) -> str:
                    """
                    Get the Python signature for a method on this service.

                    Args:
                        method_name: Name of the method (e.g., 'get_list', 'put_entity')

                    Returns:
                        String representation of the method signature

                    Example:
                        >>> sig = client.sales_order.get_signature('get_list')
                        >>> print(sig)
                        >>> # Output: sales_order.get_list(options: QueryOptions = None, api_version: str = None)
                    """
                    if not hasattr(self, '_method_signatures'):
                        raise ValueError("Method signatures not available for this service")
                    if method_name not in self._method_signatures:
                        available = ', '.join(self._method_signatures.keys())
                        raise ValueError(f"Method '{method_name}' not found. Available methods: {available}")
                    return self._method_signatures[method_name]
                return get_signature

            service_class = type(f"{tag}Service", (BaseService,), {
                "__init__": lambda s, client, entity_name=tag, endpoint_name=None: BaseService.__init__(s, client, entity_name, endpoint_name),
                "get_signature": create_get_signature_method()
            })
            service_instance = service_class(self._client, entity_name=tag, endpoint_name=self._client.endpoint_name)
            service_instance._method_signatures = {}

            # Check if this is a custom endpoint (Generic Inquiry) and get metadata
            is_custom_endpoint = self._is_custom_endpoint(tag, operations)
            custom_endpoint_metadata = None

            if is_custom_endpoint:
                # Get the description and custom name for this endpoint
                description = self._get_tag_description(tag)
                custom_name = self._get_custom_endpoint_name(description) if description else None
                custom_endpoint_metadata = {
                    'is_custom': True,
                    'description': description,
                    'custom_name': custom_name
                }
                # Store custom metadata on the service instance for the client to use
                service_instance._custom_endpoint_metadata = custom_endpoint_metadata

            for path, http_method, details in operations:
                if is_custom_endpoint:
                    self._add_custom_endpoint_method(service_instance, path, http_method, details)
                else:
                    self._add_method_to_service(service_instance, path, http_method, details)
            services[tag] = service_instance

        tag = "Inquiries"
        service_class = type(f"{tag}Service", (BaseService,), {
            "__init__": lambda s, client, entity_name=tag, endpoint_name=None: BaseService.__init__(s, client, entity_name, endpoint_name)
        })
        inquiries_service = service_class(self._client, entity_name=tag, endpoint_name=self._client.endpoint_name)
        services[tag] = inquiries_service

        # Now populate it using the refactored loop
        try:
            inquiries_service = services["Inquiries"]
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

        return services

    def _get_custom_endpoint_name(self, description: str) -> str:
        """
        Generate a readable service attribute name from a Generic Inquiry description.

        Args:
            description: Description like "PE All Items (GI908032)"

        Returns:
            Snake_case name like "pe_all_items" or None if not a GI description
        """
        # Extract name before (GI...) pattern
        match = re.search(r'^(.*?)\s*\(GI\d+\)$', description)
        if match:
            name_part = match.group(1).strip()
            # Convert to snake_case by splitting on spaces and word boundaries
            # First split by spaces, then handle camelCase within each part
            space_parts = name_part.split()
            all_words = []
            for part in space_parts:
                # Split camelCase/PascalCase parts
                camel_words = re.findall(r'[A-Z]+(?=[A-Z][a-z]|\b)|[A-Z][a-z]*|[a-z]+|\d+', part)
                all_words.extend(camel_words)
            return '_'.join(word.lower() for word in all_words if word)
        return None

    def _get_tag_description(self, tag: str) -> str:
        """
        Get the description for a tag from the schema.

        Args:
            tag: The tag name to look up

        Returns:
            Description string or None if not found
        """
        if 'tags' in self._schema:
            for tag_info in self._schema['tags']:
                if tag_info.get('name') == tag:
                    return tag_info.get('description', '')
        return None

    def _is_custom_endpoint(self, tag: str, operations: list) -> bool:
        """
        Determines if a service tag represents a custom endpoint (Generic Inquiry).

        Custom endpoints are identified by:
        1. Having a description that mentions "GI" followed by numbers (e.g., "GI908032")
        2. Having operations that suggest they're read-only inquiries
        """
        # Look for GI pattern in schema tags
        if 'tags' in self._schema:
            for tag_info in self._schema['tags']:
                if tag_info.get('name') == tag:
                    description = tag_info.get('description', '')
                    # Check if description contains GI followed by numbers (Generic Inquiry pattern)
                    if re.search(r'\(GI\d+\)', description):
                        return True

        # Additional heuristic: if the tag only has GET operations and PUT that might be for querying
        has_create_update_ops = any(
            'Post' in details.get('operationId', '') or
            ('Put' in details.get('operationId', '') and 'Entity' in details.get('operationId', ''))
            for _, _, details in operations
        )

        # Custom endpoints typically don't have true creation operations
        return not has_create_update_ops

    def _add_custom_endpoint_method(self, service: BaseService, path: str, http_method: str, details: Dict[str, Any]):
        """
        Creates methods for custom endpoint (Generic Inquiry) operations.
        For custom endpoints, we modify the PutEntity method to work with the GI query pattern.
        """
        operation_id = details.get("operationId", "")
        if not operation_id or '_' not in operation_id:
            return

        name_part = operation_id.split('_', 1)[-1]
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name_part)
        method_name = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()
        method_name = method_name.replace('__', '_')

        # For custom endpoints, we replace put_entity with a special query method
        if "PutEntity" in operation_id:
            def query_custom_endpoint(self, data: dict = None, options: QueryOptions | None = None, api_version: str | None = None):
                """
                Queries a custom endpoint (Generic Inquiry) using PUT method.

                Args:
                    data (dict, optional): Query body (typically empty {} for GI queries)
                    options (QueryOptions, optional): OData query options like $expand, $filter, etc.
                                                    If None, defaults to $expand=none for full output.
                    api_version (str, optional): The API version to use for this request.

                Returns:
                    A dictionary containing the query results.
                """
                if data is None:
                    data = {}

                return self._put_custom_endpoint(data, options=options, api_version=api_version)

            # Generate docstring
            docstring = f"""Queries the {service.entity_name} custom endpoint (Generic Inquiry).

    This is a custom endpoint that requires a PUT request to retrieve data from the Generic Inquiry.

    Args:
        data (dict, optional): Query body, typically empty dict for GI queries. Defaults to {{}}.
        options (QueryOptions, optional): OData query options like $expand, $filter, $top, etc.
        api_version (str, optional): The API version to use for this request.

    Returns:
        A dictionary containing the data from the Generic Inquiry.

    Example:
        # Query all results with default expand=none
        results = service.query_custom_endpoint()

        # Query with custom options
        from easy_acumatica.odata import QueryOptions
        options = QueryOptions(expand=['PEALLPRODSDetails'], filter="InventoryID ne null", top=100)
        results = service.query_custom_endpoint(options=options)

        # Query with specific field expansion
        options = QueryOptions(expand=['Results'])  # or whatever field name your GI uses
        results = service.query_custom_endpoint(options=options)
    """

            query_custom_endpoint.__doc__ = textwrap.indent(docstring, '    ')
            final_method = update_wrapper(query_custom_endpoint, query_custom_endpoint)
            final_method.__name__ = "query_custom_endpoint"
            setattr(service, "query_custom_endpoint", final_method.__get__(service, BaseService))

            # Also keep the original put_entity method name for backward compatibility
            setattr(service, method_name, final_method.__get__(service, BaseService))

        else:
            # For non-PutEntity operations, use the standard method generation
            self._add_method_to_service(service, path, http_method, details)

    def _fetch_gi_xml(self):
        """
        Fetches the Generic Inquiries XML document and saves it to a .metadata folder inside the package directory.
        """
        metadata_url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/$metadata"

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

        # Store signature for introspection
        service_snake = to_snake_case(service.entity_name)
        signature_str = f"{service_snake}.get_files(entity_id: str, api_version: str = None) -> list"
        if hasattr(service, '_method_signatures'):
            service._method_signatures['get_files'] = signature_str

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

        # Separate method templates for different operations
        def get_list(self, options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(options=options, api_version=api_version)

        def get_by_id(self, entity_id: Union[str, list], options: QueryOptions | None = None, api_version: str | None = None):
            return self._get(entity_id=entity_id, options=options, api_version=api_version)

        def get_by_keys(self, options: QueryOptions | None = None, api_version: str | None = None, **key_fields):
            """
            Retrieves a record by key field values.
            Key field values are passed as keyword arguments and appended to the URL path.
            """
            if not key_fields:
                raise ValueError("At least one key field must be provided as a keyword argument")
            return self._get_by_keys(key_fields=key_fields, options=options, api_version=api_version)

        def put_entity(self, data: Union[dict, BaseDataClassModel], options: QueryOptions | None = None, api_version: str | None = None):
            return self._put(data, options=options, api_version=api_version)

        def delete_by_id(self, entity_id: Union[str, list], api_version: str | None = None):
            return self._delete(entity_id=entity_id, api_version=api_version)

        def delete_by_keys(self, api_version: str | None = None, **key_fields):
            """
            Deletes a record by key field values.
            Key field values are passed as keyword arguments and appended to the URL path.
            """
            if not key_fields:
                raise ValueError("At least one key field must be provided as a keyword argument")
            # Build key path for deletion
            key_values = [str(value) for value in key_fields.values()]
            key_path = "/".join(key_values)
            return self._delete(entity_id=key_path, api_version=api_version)

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

        # Map operation IDs to appropriate method templates and generate docstrings
        template = None
        is_get_by_keys = False

        if "PutFile" in operation_id:
            template = put_file
            self._add_get_files_method(service)
        elif "GetAdHocSchema" in operation_id:
            template = get_schema
        elif "InvokeAction" in operation_id:
            template = invoke_action
        elif "PutEntity" in operation_id:
            template = put_entity
        elif "GetById" in operation_id:
            template = get_by_id
        elif "GetByKeys" in operation_id:
            template = get_by_keys
            is_get_by_keys = True
        elif "GetList" in operation_id:
            template = get_list
        elif "DeleteById" in operation_id:
            template = delete_by_id
        elif "DeleteByKeys" in operation_id:
            template = delete_by_keys
            is_get_by_keys = True  # Use similar docstring pattern for delete by keys

        if not template:
            return

        # Generate appropriate docstring
        if is_get_by_keys and "Delete" not in operation_id:
            docstring = _generate_docstring(service.entity_name, operation_id, details, is_get_by_keys=True)
        else:
            docstring = _generate_docstring(service.entity_name, operation_id, details)

        template.__doc__ = docstring
        template.__name__ = method_name

        setattr(service, method_name, template.__get__(service, BaseService))

        # Store the method signature
        import inspect
        sig = inspect.signature(template)
        params = []
        for param_name, param in sig.parameters.items():
            if param_name == 'self':
                continue
            # Build parameter string with type and default
            type_str = ''
            if param.annotation != inspect.Parameter.empty:
                ann = param.annotation
                if hasattr(ann, '__name__'):
                    type_str = f": {ann.__name__}"
                else:
                    type_str = f": {str(ann).replace('typing.', '')}"

            if param.default != inspect.Parameter.empty:
                params.append(f"{param_name}{type_str} = {param.default}")
            else:
                params.append(f"{param_name}{type_str}")

        # Get return type
        return_type = ''
        if sig.return_annotation != inspect.Signature.empty:
            ret = sig.return_annotation
            if hasattr(ret, '__name__'):
                return_type = f" -> {ret.__name__}"
            else:
                return_type = f" -> {str(ret).replace('typing.', '')}"

        # Convert service entity name to snake_case
        service_snake = to_snake_case(service.entity_name)
        params_str = ', '.join(params)
        signature_str = f"{service_snake}.{method_name}({params_str}){return_type}"

        if hasattr(service, '_method_signatures'):
            service._method_signatures[method_name] = signature_str

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