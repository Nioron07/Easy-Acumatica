#!/usr/bin/env python3
"""
Enhanced Generate PEP 561 compliant stub files for easy-acumatica with proper typing.

This script generates .pyi stub files in a proper structure:
- stubs/
  - __init__.pyi
  - client.pyi  
  - models.pyi
  - services.pyi
  - core.pyi
  - odata.pyi
  - py.typed
"""

import argparse
import getpass
import inspect
import easy_acumatica
import os
import sys
from dataclasses import fields, is_dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Type, get_type_hints

from easy_acumatica.client import AcumaticaClient
from easy_acumatica.core import BaseDataClassModel, BaseService


def get_type_annotation_string(annotation: Any) -> str:
    """Convert a type annotation to its string representation for stub files."""
    if annotation is inspect._empty:
        return "Any"
    
    # Handle None type
    if annotation is type(None):
        return "None"
    
    # Get the string representation
    type_str = str(annotation)
    
    # Clean up common patterns
    replacements = {
        "<class '": "",
        "'>": "",
        "typing.": "",
        "builtins.": "",
        "NoneType": "None",
    }
    
    for old, new in replacements.items():
        type_str = type_str.replace(old, new)
    
    # Handle forward references
    if "ForwardRef" in type_str:
        # Extract the string inside ForwardRef
        start = type_str.find("('") + 2
        end = type_str.find("')")
        if start > 1 and end > start:
            type_str = f"'{type_str[start:end]}'"
    
    return type_str


def generate_model_stub(model_class: Type[BaseDataClassModel]) -> List[str]:
    """Generate stub lines for a single dataclass model."""
    lines = []
    
    # Add @dataclass decorator
    lines.append("@dataclass")
    lines.append(f"class {model_class.__name__}(BaseDataClassModel):")
    
    # Add docstring if it exists
    if model_class.__doc__:
        # Format docstring properly
        doc_lines = model_class.__doc__.strip().split('\n')
        if len(doc_lines) == 1:
            lines.append(f'    """{doc_lines[0]}"""')
        else:
            lines.append('    """')
            for doc_line in doc_lines:
                lines.append(f'    {doc_line}' if doc_line.strip() else '    ')
            lines.append('    """')
    
    # Get type hints for the class
    try:
        hints = get_type_hints(model_class)
    except:
        # If we can't get type hints, fall back to field annotations
        hints = {}
        if hasattr(model_class, '__annotations__'):
            hints = model_class.__annotations__
    
    # Get dataclass fields
    dataclass_fields = fields(model_class) if is_dataclass(model_class) else []
    
    if not dataclass_fields and not hints:
        lines.append("    ...")
    else:
        # Generate field definitions
        for field in dataclass_fields:
            field_name = field.name
            
            # Skip internal fields
            if field_name.startswith('_'):
                continue
            
            # Get type annotation
            if field_name in hints:
                type_str = get_type_annotation_string(hints[field_name])
            else:
                type_str = "Any"
            
            # All fields have default values in our models
            lines.append(f"    {field_name}: {type_str} = ...")
    
    return lines


def get_return_type_from_schema(operation_details: Dict[str, Any], schema: Dict[str, Any], default_type: str = "Any") -> str:
    """Extract return type from OpenAPI operation details."""
    if not operation_details:
        return default_type

    # Check responses for successful response types
    responses = operation_details.get("responses", {})
    success_response = responses.get("200", responses.get("201", {}))

    if success_response:
        content = success_response.get("content", {})
        json_content = content.get("application/json", {})
        response_schema = json_content.get("schema", {})

        if response_schema:
            # Handle array types
            if response_schema.get("type") == "array":
                items = response_schema.get("items", {})
                if "$ref" in items:
                    type_name = items["$ref"].split("/")[-1]
                    return f"List[{type_name}]"
                else:
                    return "List[Any]"

            # Handle reference types
            elif "$ref" in response_schema:
                type_name = response_schema["$ref"].split("/")[-1]
                return type_name

            # Handle primitive types
            elif "type" in response_schema:
                type_mapping = {
                    "string": "str",
                    "integer": "int",
                    "number": "float",
                    "boolean": "bool",
                    "object": "Dict[str, Any]"
                }
                return type_mapping.get(response_schema["type"], "Any")

    return default_type


def generate_typed_method_signature(
    service_name: str,
    method_name: str,
    method: Any,
    schema: Dict[str, Any]
) -> List[str]:
    """Generate a typed method signature based on OpenAPI schema."""
    lines = []

    # Map method names to their likely OpenAPI operation patterns
    operation_patterns = {
        'get_list': 'GetList',
        'get_by_id': 'GetById',
        'get_by_keys': 'GetByKeys',
        'put_entity': 'PutEntity',
        'delete_by_id': 'DeleteById',
        'delete_by_keys': 'DeleteByKeys',
        'put_file': 'PutFile',
        'get_files': 'GetFiles',
        'get_ad_hoc_schema': 'GetAdHocSchema'
    }

    # Find the operation in the schema
    operation_details = None
    operation_id_pattern = None

    # Handle invoke_action methods
    if method_name.startswith('invoke_action_'):
        action_name = method_name.replace('invoke_action_', '').replace('_', '')
        operation_id_pattern = f"{service_name}_InvokeAction_"
        # Look for specific action or generic custom action
        for path, path_info in schema.get("paths", {}).items():
            for http_method, details in path_info.items():
                operation_id = details.get("operationId", "")
                if (operation_id.startswith(operation_id_pattern) and
                    action_name.lower() in operation_id.lower()):
                    operation_details = details
                    break
            if operation_details:
                break
    else:
        # Handle standard CRUD operations
        pattern = operation_patterns.get(method_name)
        if pattern:
            operation_id_pattern = f"{service_name}_{pattern}"
            for path, path_info in schema.get("paths", {}).items():
                for http_method, details in path_info.items():
                    if details.get("operationId") == operation_id_pattern:
                        operation_details = details
                        break
                if operation_details:
                    break
    
    # Get return type from schema
    return_type = get_return_type_from_schema(operation_details, schema, default_type=service_name)

    # Generate method signature based on operation type
    if method_name == 'get_list':
        # For get_list, always return List of the service entity
        return_type = f"List[{service_name}]" if operation_details else f"List[{service_name}]"
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        options: Optional[QueryOptions] = None,",
            "        api_version: Optional[str] = None",
            f"    ) -> {return_type}:",
        ])
    elif method_name == 'get_by_id':
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        entity_id: Union[str, List[str]],",
            "        options: Optional[QueryOptions] = None,",
            "        api_version: Optional[str] = None",
            f"    ) -> {return_type}:",
        ])
    elif method_name == 'get_by_keys':
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        options: Optional[QueryOptions] = None,",
            "        api_version: Optional[str] = None,",
            "        **key_fields: Any",
            f"    ) -> {return_type}:",
        ])
    elif method_name == 'put_entity':
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            f"        data: Union[Dict[str, Any], {service_name}],",
            "        options: Optional[QueryOptions] = None,",
            "        api_version: Optional[str] = None",
            f"    ) -> {return_type}:",
        ])
    elif method_name in ['delete_by_id', 'delete_by_keys']:
        # Deletes typically return None/void
        delete_return_type = get_return_type_from_schema(operation_details, schema, default_type="None")
        if delete_return_type == service_name:  # If it defaults to service name, use None
            delete_return_type = "None"
        if method_name == 'delete_by_id':
            params = [
                "        self,",
                "        entity_id: Union[str, List[str]],",
                "        api_version: Optional[str] = None"
            ]
        else:
            params = [
                "        self,",
                "        api_version: Optional[str] = None,",
                "        **key_fields: Any"
            ]
        lines.extend([f"    def {method_name}("] + params + [f"    ) -> {delete_return_type}:"])
    elif method_name == 'put_file':
        file_return_type = get_return_type_from_schema(operation_details, schema, default_type="None")
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        entity_id: str,",
            "        filename: str,",
            "        data: bytes,",
            "        comment: Optional[str] = None,",
            "        api_version: Optional[str] = None",
            f"    ) -> {file_return_type}:",
        ])
    elif method_name == 'get_files':
        files_return_type = get_return_type_from_schema(operation_details, schema, default_type="List[Dict[str, Any]]")
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        entity_id: str,",
            "        api_version: Optional[str] = None",
            f"    ) -> {files_return_type}:",
        ])
    elif method_name == 'get_ad_hoc_schema':
        schema_return_type = get_return_type_from_schema(operation_details, schema, default_type=service_name)
        lines.extend([
            f"    def {method_name}(",
            "        self,",
            "        api_version: Optional[str] = None",
            f"    ) -> {schema_return_type}:",
        ])
    elif method_name.startswith('invoke_action_'):
        # For action methods, try to determine the correct input and return types from schema
        input_type = "Any"
        action_return_type = get_return_type_from_schema(operation_details, schema, default_type=f"Optional[{service_name}]")

        if operation_details:
            request_body = operation_details.get("requestBody", {})
            content = request_body.get("content", {})
            json_content = content.get("application/json", {})
            schema_ref = json_content.get("schema", {}).get("$ref", "")
            if schema_ref:
                input_type = schema_ref.split("/")[-1]

        lines.extend([
            f"    def {method_name}(",
            "        self,",
            f"        invocation: {input_type},",
            "        api_version: Optional[str] = None",
            f"    ) -> {action_return_type}:",
        ])
    else:
        # Fallback for unknown methods
        lines.extend([
            f"    def {method_name}(self, *args, **kwargs) -> Any:"
        ])
    
    # Add docstring if it exists
    if hasattr(method, '__doc__') and method.__doc__:
        doc_lines = method.__doc__.strip().split('\n')
        if len(doc_lines) == 1:
            lines.append(f'        """{doc_lines[0]}"""')
        else:
            lines.append('        """')
            for doc_line in doc_lines:
                lines.append(f'        {doc_line}' if doc_line.strip() else '        ')
            lines.append('        """')
    
    lines.append("        ...")
    
    return lines


def generate_service_stub(service_name: str, service_instance: BaseService, schema: Dict[str, Any]) -> List[str]:
    """Generate stub lines for a service class with proper typing from OpenAPI schema."""
    lines = []
    
    # Generate class definition
    lines.append(f"class {service_name}Service(BaseService):")
    
    # Get all public methods of the service
    methods = []
    for attr_name in dir(service_instance):
        if attr_name.startswith('_'):
            continue
        
        attr = getattr(service_instance, attr_name)
        if callable(attr) and not isinstance(attr, type):
            methods.append((attr_name, attr))
    
    if not methods:
        lines.append("    ...")
    else:
        # Sort methods alphabetically for consistent output
        methods.sort(key=lambda x: x[0])
        
        for method_name, method in methods:
            # Generate typed method signature based on OpenAPI schema
            method_signature = generate_typed_method_signature(
                service_name, method_name, method, schema
            )
            lines.extend(method_signature)
    
    return lines


def create_stub_structure(client: AcumaticaClient, output_dir: Path) -> None:
    """
    Generate stub files in a proper structure in a stubs/ folder.
    """
    print("Generating enhanced stub files with proper structure...")
    
    # Create stubs directory
    stubs_dir = output_dir / "stubs"
    stubs_dir.mkdir(parents=True, exist_ok=True)
    
    # Get the schema for typing information
    schema = client._fetch_schema(client.endpoint_name, client.endpoint_version)
    
    # Create py.typed file to mark package as supporting type checking
    py_typed_path = stubs_dir / "py.typed"
    py_typed_path.write_text("")
    print(f"✅ Created py.typed marker at {py_typed_path}")
    
    # Generate __init__.pyi
    print("Generating __init__.pyi...")
    init_lines = [
        '"""Type stubs for easy_acumatica."""',
        "from .client import AcumaticaClient",
        "from .batch import BatchCall, CallableWrapper, batch_call, create_batch_from_ids, create_batch_from_filters",
        "",
        "__all__ = [",
        '    "AcumaticaClient",',
        '    "BatchCall",',
        '    "CallableWrapper", ',
        '    "batch_call",',
        '    "create_batch_from_ids",',
        '    "create_batch_from_filters"',
        "]",
    ]
    (stubs_dir / "__init__.pyi").write_text("\n".join(init_lines))
    print("✅ Generated __init__.pyi")
    
    # Generate core.pyi
    print("Generating core.pyi...")
    core_lines = [
        "from __future__ import annotations",
        "from typing import Any, Dict, Optional, TYPE_CHECKING",
        "from .odata import QueryOptions",
        "",
        "if TYPE_CHECKING:",
        "    from .client import AcumaticaClient",
        "",
        "class BaseDataClassModel:",
        "    def to_acumatica_payload(self) -> Dict[str, Any]: ...",
        "    def build(self) -> Dict[str, Any]: ...",
        "",
        "class BaseService:",
        "    _client: AcumaticaClient",
        "    entity_name: str",
        "    endpoint_name: str",
        "    ",
        "    def __init__(self, client: AcumaticaClient, entity_name: str, endpoint_name: str = 'Default') -> None: ...",
        "",
    ]
    (stubs_dir / "core.pyi").write_text("\n".join(core_lines))
    print("✅ Generated core.pyi")
    
    # Generate odata.pyi
    print("Generating odata.pyi...")
    odata_lines = [
        "from __future__ import annotations",
        "from typing import Any, Dict, List, Optional, Union",
        "from datetime import date, datetime",
        "",
        "class Filter:",
        "    expr: str",
        "    def __init__(self, expr: str) -> None: ...",
        "    def __getattr__(self, name: str) -> Filter: ...",
        "    def __eq__(self, other: Any) -> Filter: ...",
        "    def __ne__(self, other: Any) -> Filter: ...",
        "    def __gt__(self, other: Any) -> Filter: ...",
        "    def __ge__(self, other: Any) -> Filter: ...",
        "    def __lt__(self, other: Any) -> Filter: ...",
        "    def __le__(self, other: Any) -> Filter: ...",
        "    def __and__(self, other: Any) -> Filter: ...",
        "    def __or__(self, other: Any) -> Filter: ...",
        "    def __invert__(self) -> Filter: ...",
        "    def build(self) -> str: ...",
        "    def __str__(self) -> str: ...",
        "",
        "class _FieldFactory:",
        "    def __getattr__(self, name: str) -> Filter: ...",
        "    def cf(self, type_name: str, view_name: str, field_name: str) -> Filter: ...",
        "",
        "F: _FieldFactory",
        "",
        "class QueryOptions:",
        "    def __init__(",
        "        self,",
        "        filter: Optional[Union[str, Filter]] = None,",
        "        expand: Optional[List[str]] = None,",
        "        select: Optional[List[str]] = None,",
        "        top: Optional[int] = None,",
        "        skip: Optional[int] = None,",
        "        custom: Optional[List[Any]] = None,",
        "        orderby: Optional[Union[str, List[str]]] = None,",
        "        count: Optional[bool] = None,",
        "        search: Optional[str] = None,",
        "        format: Optional[str] = None,",
        "        skiptoken: Optional[str] = None,",
        "        deltatoken: Optional[str] = None,",
        "        apply: Optional[str] = None,",
        "    ) -> None: ...",
        "    ",
        "    def to_params(self) -> Dict[str, str]: ...",
        "    def to_dict(self) -> Dict[str, Any]: ...",
        "    def copy(self, **kwargs: Any) -> QueryOptions: ...",
        "",
    ]
    (stubs_dir / "odata.pyi").write_text("\n".join(odata_lines))
    print("✅ Generated odata.pyi")
    
    # Generate batch.pyi
    print("Generating batch.pyi...")
    batch_lines = [
        "from __future__ import annotations",
        "from typing import Any, Callable, List, Optional, Tuple, Union",
        "from dataclasses import dataclass",
        "",
        "@dataclass",
        "class BatchCallResult:",
        "    success: bool",
        "    result: Any = None",
        "    error: Optional[Exception] = None",
        "    execution_time: float = 0.0",
        "    call_index: int = 0",
        "",
        "@dataclass", 
        "class BatchCallStats:",
        "    total_calls: int = 0",
        "    successful_calls: int = 0",
        "    failed_calls: int = 0",
        "    total_time: float = 0.0",
        "    average_call_time: float = 0.0",
        "    max_call_time: float = 0.0",
        "    min_call_time: float = 0.0",
        "    concurrency_level: int = 0",
        "",
        "class CallableWrapper:",
        "    func: Callable",
        "    args: Tuple[Any, ...]",
        "    kwargs: Dict[str, Any]",
        "    method_name: str",
        "    ",
        "    def __init__(self, func: Callable, *args: Any, **kwargs: Any) -> None: ...",
        "    def execute(self) -> Any: ...",
        "",
        "class BatchCall:",
        "    calls: List[CallableWrapper]",
        "    max_concurrent: int",
        "    timeout: Optional[float]",
        "    fail_fast: bool",
        "    return_exceptions: bool",
        "    results: List[BatchCallResult]",
        "    stats: BatchCallStats",
        "    executed: bool",
        "    ",
        "    def __init__(",
        "        self,",
        "        *calls: Union[CallableWrapper, Callable],",
        "        max_concurrent: Optional[int] = None,",
        "        timeout: Optional[float] = None,",
        "        fail_fast: bool = False,",
        "        return_exceptions: bool = True,",
        "        progress_callback: Optional[Callable[[int, int], None]] = None",
        "    ) -> None: ...",
        "    ",
        "    def execute(self) -> Tuple[Any, ...]: ...",
        "    def get_results_tuple(self) -> Tuple[Any, ...]: ...",
        "    def get_successful_results(self) -> List[Any]: ...",
        "    def get_failed_calls(self) -> List[Tuple[int, CallableWrapper, Exception]]: ...",
        "    def retry_failed_calls(self, max_concurrent: Optional[int] = None) -> BatchCall: ...",
        "    def print_summary(self) -> None: ...",
        "",
        "def batch_call(*calls: Any, **kwargs: Any) -> BatchCall: ...",
        "def create_batch_from_ids(service: Any, entity_ids: List[str], method_name: str = 'get_by_id', **method_kwargs: Any) -> BatchCall: ...",
        "def create_batch_from_filters(service: Any, filters: List[Any], method_name: str = 'get_list', **method_kwargs: Any) -> BatchCall: ...",
    ]
    (stubs_dir / "batch.pyi").write_text("\n".join(batch_lines))
    print("✅ Generated batch.pyi")
    
    # Generate models.pyi
    print("Generating models.pyi...")
    model_lines = [
        "from __future__ import annotations",
        "from typing import Any, List, Optional, Union",
        "from dataclasses import dataclass",
        "from datetime import datetime",
        "import easy_acumatica",
        "from .core import BaseDataClassModel",
        ""
    ]
    
    # Get all model classes from client.models
    model_classes = []
    for attr_name in dir(client.models):
        if not attr_name.startswith('_'):
            attr = getattr(client.models, attr_name)
            if isinstance(attr, type) and issubclass(attr, BaseDataClassModel):
                model_classes.append((attr_name, attr))
    
    # Sort models alphabetically
    model_classes.sort(key=lambda x: x[0])
    
    # Generate stub for each model
    for model_name, model_class in model_classes:
        model_lines.extend(generate_model_stub(model_class))
        model_lines.append("")  # Empty line between classes
    
    # Write models.pyi
    (stubs_dir / "models.pyi").write_text("\n".join(model_lines))
    print(f"✅ Generated models.pyi with {len(model_classes)} models")
    
    # Generate services.pyi
    print("Generating services.pyi...")
    service_lines = [
        "from __future__ import annotations",
        "from typing import Any, Dict, List, Optional, Union",
        "from .core import BaseService",
        "from .odata import QueryOptions",
        "from .models import *  # Import all model types",
        "",
        ""
    ]
    
    # Get all service attributes from the client
    services = []
    for attr_name in dir(client):
        if not attr_name.startswith('_') and attr_name not in ['models', 'session', 'base_url', 
                                                                'tenant', 'username', 'verify_ssl',
                                                                'persistent_login', 'retry_on_idle_logout',
                                                                'endpoint_name', 'endpoint_version',
                                                                'timeout', 'endpoints', 'cache_enabled',
                                                                'cache_dir', 'cache_ttl_hours', 'force_rebuild']:
            attr = getattr(client, attr_name)
            if isinstance(attr, BaseService):
                # Convert attribute name to PascalCase service name
                # Handle proper English pluralization rules
                clean_attr_name = attr_name
                if attr_name.endswith('s') and len(attr_name) > 1:
                    # Handle special cases and common English pluralization patterns
                    if attr_name.endswith('ies'):
                        # companies -> company, categories -> category
                        clean_attr_name = attr_name[:-3] + 'y'
                    elif attr_name.endswith('ses') or attr_name.endswith('xes') or attr_name.endswith('ches') or attr_name.endswith('shes'):
                        # addresses -> address, boxes -> box, batches -> batch, dishes -> dish
                        # but warehouses -> warehouse (keep the 'e')
                        if attr_name.endswith('houses'):
                            clean_attr_name = attr_name[:-1]  # Remove just the 's'
                        else:
                            clean_attr_name = attr_name[:-2]
                    elif attr_name.endswith('ves'):
                        # leaves -> leaf, knives -> knife
                        clean_attr_name = attr_name[:-3] + 'f'
                    elif not any(attr_name.endswith(suffix) for suffix in ['ss', 'us', 'is', 'as', 'class']):
                        # Regular plural (orders -> order), but keep words naturally ending in s (class, address, etc.)
                        # Check if removing 's' creates a valid word by looking at common patterns
                        potential_singular = attr_name[:-1]
                        # If the word without 's' ends in these patterns, it's likely a regular plural
                        if (potential_singular.endswith('_account') or 
                            potential_singular.endswith('_item') or 
                            potential_singular.endswith('_order') or
                            potential_singular.endswith('_contact') or
                            potential_singular.endswith('_customer') or
                            potential_singular.endswith('_vendor') or
                            potential_singular.endswith('_employee') or
                            '_' in potential_singular):  # Most compound words are regular plurals
                            clean_attr_name = potential_singular
                        # Special handling for common word endings that might be naturally singular
                        elif not any(potential_singular.endswith(ending) for ending in ['addres', 'clas', 'proces', 'acces']):
                            clean_attr_name = potential_singular
                
                parts = clean_attr_name.split('_')
                service_name = ''.join(part.title() for part in parts)
                services.append((service_name, attr_name, attr))
    
    # Generate service class stubs with proper typing
    for service_name, attr_name, service_instance in services:
        service_stub_lines = generate_service_stub(service_name, service_instance, schema)
        service_lines.extend(service_stub_lines)
        service_lines.append("")  # Empty line between classes
    
    # Write services.pyi
    (stubs_dir / "services.pyi").write_text("\n".join(service_lines))
    print(f"✅ Generated services.pyi with {len(services)} services")
    
    # Generate client.pyi
    print("Generating client.pyi...")
    client_lines = [
        "from __future__ import annotations",
        "from typing import Any, Dict, List, Optional, Union",
        "from pathlib import Path",
        "import requests",
        "from .services import *  # Import all service types",
        "from . import models",
        "",
        "class AcumaticaClient:",
        '    """Main client for interacting with Acumatica API."""',
        "    ",
        "    # Configuration attributes",
        "    base_url: str",
        "    tenant: str", 
        "    username: str",
        "    verify_ssl: bool",
        "    persistent_login: bool",
        "    retry_on_idle_logout: bool",
        "    endpoint_name: str",
        "    endpoint_version: Optional[str]",
        "    timeout: int",
        "    endpoints: Dict[str, Dict[str, Any]]",
        "    session: requests.Session",
        "    cache_enabled: bool",
        "    cache_dir: Path",
        "    cache_ttl_hours: int",
        "    force_rebuild: bool",
        "    ",
        "    # Service attributes"
    ]
    
    for service_name, attr_name, _ in services:
        client_lines.append(f"    {attr_name}: {service_name}Service")
    
    client_lines.extend([
        "    models: Any  # This points to the models module",
        "    ",
        "    def __init__(",
        "        self,",
        "        base_url: Optional[str] = None,",
        "        username: Optional[str] = None,",
        "        password: Optional[str] = None,",
        "        tenant: Optional[str] = None,",
        "        branch: Optional[str] = None,",
        "        locale: Optional[str] = None,",
        "        verify_ssl: bool = True,",
        "        persistent_login: bool = True,",
        "        retry_on_idle_logout: bool = True,",
        "        endpoint_name: str = 'Default',",
        "        endpoint_version: Optional[str] = None,",
        "        config: Optional[Any] = None,",
        "        rate_limit_calls_per_second: float = 10.0,",
        "        timeout: Optional[int] = None,",
        "        cache_methods: bool = False,",
        "        cache_ttl_hours: int = 24,",
        "        cache_dir: Optional[Path] = None,",
        "        force_rebuild: bool = False,",
        "        env_file: Optional[Union[str, Path]] = None,",
        "        auto_load_env: bool = True,",
        "    ) -> None: ...",
        "    ",
        "    def login(self) -> int: ...",
        "    def logout(self) -> int: ...", 
        "    def close(self) -> None: ...",
        "    def list_models(self) -> List[str]: ...",
        "    def list_services(self) -> List[str]: ...",
        "    def get_model_info(self, model_name: str) -> Dict[str, Any]: ...",
        "    def get_service_info(self, service_name: str) -> Dict[str, Any]: ...",
        "    def get_performance_stats(self) -> Dict[str, Any]: ...",
        "    def clear_cache(self) -> None: ...",
        "    def help(self, topic: Optional[str] = None) -> None: ...",
        "    def __enter__(self) -> AcumaticaClient: ...",
        "    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...",
    ])
    
    # Write client.pyi
    (stubs_dir / "client.pyi").write_text("\n".join(client_lines))
    print("✅ Generated client.pyi")
    
    print(f"\n✅ Generated enhanced stub files in {stubs_dir}")
    print("Folder structure:")
    print("stubs/")
    print("├── __init__.pyi")
    print("├── batch.pyi") 
    print("├── client.pyi")
    print("├── core.pyi")
    print("├── models.pyi")
    print("├── odata.pyi")
    print("├── services.pyi")
    print("└── py.typed")
    print("\nThese stubs include:")
    print("- Proper service types in services.pyi")
    print("- All model imports in services.pyi")
    print("- Correct return and parameter types")
    print("- Full action method typing")


def main():
    parser = argparse.ArgumentParser(description="Generate enhanced PEP 561 compliant stub files for easy-acumatica.")
    parser.add_argument("--url", help="Base URL of the Acumatica instance.")
    parser.add_argument("--username", help="Username for authentication.")
    parser.add_argument("--password", help="Password for authentication.")
    parser.add_argument("--tenant", help="The tenant to connect to.")
    parser.add_argument("--endpoint-version", help="The API endpoint version to use.")
    parser.add_argument("--endpoint-name", default="Default", help="The API endpoint name.")
    parser.add_argument("--output-dir", default=".", help="Output directory for stub files.")
    args = parser.parse_args()

    # Try to load from .env file if it exists
    env_path = Path(".env")
    if env_path.exists():
        print("Found .env file, loading configuration...")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    
                    # Set arguments from env if not provided
                    if key == 'ACUMATICA_URL' and not args.url:
                        args.url = value
                    elif key == 'ACUMATICA_USERNAME' and not args.username:
                        args.username = value
                    elif key == 'ACUMATICA_PASSWORD' and not args.password:
                        args.password = value
                    elif key == 'ACUMATICA_TENANT' and not args.tenant:
                        args.tenant = value
                    elif key == 'ACUMATICA_ENDPOINT_NAME' and not args.endpoint_name:
                        args.endpoint_name = value
                    elif key == 'ACUMATICA_ENDPOINT_VERSION' and not args.endpoint_version:
                        args.endpoint_version = value

    # Get credentials interactively if not provided
    if not args.url:
        args.url = input("Enter Acumatica URL: ")
    if not args.tenant:
        args.tenant = input("Enter Tenant: ")
    if not args.username:
        args.username = input("Enter Username: ")
    if not args.password:
        args.password = getpass.getpass("Enter Password: ")

    print(f"\nConnecting to {args.url}...")
    
    # Create client instance
    client = AcumaticaClient(
        base_url=args.url,
        username=args.username,
        password=args.password,
        tenant=args.tenant,
        endpoint_name=args.endpoint_name,
        endpoint_version=args.endpoint_version,
        cache_methods=False, # Explicitly disable caching for stub generation
    )
    
    print("✅ Successfully connected and initialized client")
    
    # Generate stubs
    output_dir = Path(args.output_dir)
    create_stub_structure(client, output_dir)
    
    # Clean up
    client.logout()
    print("\n✅ Logged out successfully")
    print("\n" + "="*60)
    print("ENHANCED STUB GENERATION COMPLETE!")
    print("="*60)


if __name__ == "__main__":
    main()