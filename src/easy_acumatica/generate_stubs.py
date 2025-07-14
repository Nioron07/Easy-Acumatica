import argparse
import requests
import sys
from pathlib import Path
from typing import Dict, Any, Type, List, Optional, Union
import textwrap

# Add the project's source directory to the Python path.
# This allows the script to import from the `easy_acumatica` package
# as if it were an installed module, which is necessary for accessing
# the factories and core classes.
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / 'src'))

from easy_acumatica.client import AcumaticaClient
from easy_acumatica.model_factory import ModelFactory
from easy_acumatica.service_factory import ServiceFactory
from easy_acumatica.helpers import _raise_with_detail
from easy_acumatica.core import BaseService

def _map_schema_type_to_python_type(prop_details: Dict[str, Any]) -> str:
    """
    Helper function to map a schema property to a Python type hint string.

    This is the core logic for creating clean type hints in the .pyi file. It
    translates Acumatica's wrapper types directly into Python's primitive types.

    Args:
        prop_details: The schema dictionary for a single property.

    Returns:
        A string representing the Python type hint (e.g., "Optional[str]").
    """
    if "$ref" in prop_details:
        ref_name = prop_details["$ref"].split("/")[-1]
        
        if ref_name == "StringValue": return "Optional[str]"
        if ref_name == "DecimalValue": return "Optional[float]"
        if ref_name == "BooleanValue": return "Optional[bool]"
        if ref_name == "DateTimeValue": return "Optional[datetime]"
        if ref_name == "GuidValue": return "Optional[str]"
        if ref_name == "IntValue": return "Optional[int]"
        if ref_name == "ShortValue": return "Optional[int]"
        if ref_name == "LongValue": return "Optional[int]"
        if ref_name == "ByteValue": return "Optional[int]"
        if ref_name == "DoubleValue": return "Optional[float]"

        return f"Optional['{ref_name}']"

    if prop_details.get("type") == "array":
        item_type_hint = _map_schema_type_to_python_type(prop_details.get("items", {}))
        return f"List[{item_type_hint}]"

    return "Optional[Any]"

def generate_model_stubs(schema: Dict[str, Any]) -> str:
    """
    Generates the content for the models.pyi stub file.
    """
    pyi_content = [
        "from __future__ import annotations",
        "from typing import Any, List, Optional, Union",
        "from dataclasses import dataclass",
        "from datetime import datetime",
        "from .core import BaseDataClassModel\n\n"
    ]
    
    schemas = schema.get("components", {}).get("schemas", {})
    primitive_wrappers = {
        "StringValue", "DecimalValue", "BooleanValue", "DateTimeValue",
        "GuidValue", "IntValue", "ShortValue", "LongValue", "ByteValue",
        "DoubleValue"
    }

    for name, definition in sorted(schemas.items()):
        if name in primitive_wrappers:
            continue

        class_lines = [f"@dataclass", f"class {name}(BaseDataClassModel):"]
        
        properties = {}
        if 'allOf' in definition:
            for item in definition['allOf']:
                if 'properties' in item:
                    properties.update(item['properties'])
        else:
            properties = definition.get("properties", {})

        if not properties and 'allOf' not in definition:
            class_lines.append("    ...")
        else:
            if 'allOf' in definition:
                class_lines.append("    id: Optional[str] = ...")

            for prop_name, prop_details in sorted(properties.items()):
                if prop_name in ["id", "note", "rowNumber", "error", "_links"]:
                    continue
                type_hint = _map_schema_type_to_python_type(prop_details)
                class_lines.append(f"    {prop_name}: {type_hint} = ...")
        
        pyi_content.extend(class_lines)
        pyi_content.append("\n")
        
    return "\n".join(pyi_content)

def generate_client_stubs(schema: Dict[str, Any], client_instance: "AcumaticaClient") -> str:
    """
    Generates the content for the client.pyi stub file with detailed methods.
    """
    paths = schema.get("paths", {})
    tags_to_ops: Dict[str, Dict] = {}
    for path, path_info in paths.items():
        for http_method, details in path_info.items():
            tag = details.get("tags", [None])[0]
            if not tag or http_method not in ['get', 'put', 'post', 'delete']: continue
            if tag not in tags_to_ops: tags_to_ops[tag] = {}
            operation_id = details.get("operationId", "")
            if operation_id:
                tags_to_ops[tag][operation_id] = (path, http_method, details)

    pyi_content = [
        "from __future__ import annotations",
        "from typing import Any, Union, List",
        "from .core import BaseService, BaseDataClassModel",
        "from .odata import QueryOptions",
        "from . import models\n\n"
    ]

    for tag, operations in sorted(tags_to_ops.items()):
        service_class_name = f"{tag}Service"
        class_lines = [f"class {service_class_name}(BaseService):"]
        
        if not operations:
            class_lines.append("    ...")
        else:
            for op_id, (path, http_method, details) in sorted(operations.items()):
                method_name = op_id.split('_', 1)[-1].lower()
                
                if "InvokeAction" in op_id:
                    ref = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
                    model_name = ref.split("/")[-1]
                    class_lines.append(f"    def {method_name}(self, invocation: models.{model_name}, api_version: str | None = None) -> Any: ...")
                elif "PutEntity" in op_id:
                    ref = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
                    model_name = ref.split("/")[-1]
                    class_lines.append(f"    def {method_name}(self, data: Union[dict, models.{model_name}], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "GetById" in op_id or "GetByKeys" in op_id:
                    class_lines.append(f"    def {method_name}(self, entity_id: Union[str, List[str]], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "GetList" in op_id:
                    class_lines.append(f"    def {method_name}(self, options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "DeleteById" in op_id or "DeleteByKeys" in op_id:
                    class_lines.append(f"    def {method_name}(self, entity_id: Union[str, List[str]], api_version: str | None = None) -> None: ...")
                elif "GetAdHocSchema" in op_id:
                     class_lines.append(f"    def {method_name}(self, api_version: str | None = None) -> Any: ...")

        pyi_content.extend(class_lines)
        pyi_content.append("\n")

    pyi_content.append("class AcumaticaClient:")
    for tag in sorted(tags_to_ops.keys()):
        service_class_name = f"{tag}Service"
        attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in tag]).lstrip('_') + 's'
        pyi_content.append(f"    {attr_name}: {service_class_name}")
    pyi_content.append("    models: models\n")

    return "\n".join(pyi_content)

def main():
    """
    Main entry point for the command-line script.
    """
    parser = argparse.ArgumentParser(
        description="Generate .pyi stub files for easy-acumatica.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--url", required=True, help="Base URL of the Acumatica instance")
    parser.add_argument("--username", required=True, help="Acumatica username")
    parser.add_argument("--password", required=True, help="Acumatica password")
    parser.add_argument("--tenant", required=True, help="Acumatica tenant")
    parser.add_argument("--branch", required=False, help="Acumatica branch (optional)")
    parser.add_argument("--endpoint-name", default="Default", help="The endpoint name")
    parser.add_argument("--endpoint-version", required=True, help="The endpoint version")
    
    args = parser.parse_args()

    print("Attempting to log in and fetch schema...")
    with requests.Session() as session:
        login_payload = {"name": args.username, "password": args.password, "tenant": args.tenant}
        if args.branch:
            login_payload["branch"] = args.branch
        login_url = f"{args.url.rstrip('/')}/entity/auth/login"
        login_resp = session.post(login_url, json=login_payload)
        _raise_with_detail(login_resp)
        print("Login successful.")

        schema_url = f"{args.url.rstrip('/')}/entity/{args.endpoint_name}/{args.endpoint_version}/swagger.json"
        schema_resp = session.get(schema_url)
        _raise_with_detail(schema_resp)
        schema = schema_resp.json()
        print("Schema fetched successfully.")

        # Generate and write both stub files
        print("Generating models.pyi stub content...")
        model_pyi_content = generate_model_stubs(schema)
        model_output_file = Path("src/easy_acumatica/models.pyi")
        model_output_file.parent.mkdir(parents=True, exist_ok=True)
        model_output_file.write_text(model_pyi_content, encoding='utf-8')
        print(f"✅ Success! Model stubs generated at: {model_output_file.absolute()}")

        print("Generating client.pyi stub content...")
        client_pyi_content = generate_client_stubs(schema, None) # Passing None for dummy client
        client_output_file = Path("src/easy_acumatica/client.pyi")
        client_output_file.write_text(client_pyi_content, encoding='utf-8')
        print(f"✅ Success! Client stubs generated at: {client_output_file.absolute()}")

        print("\nYour IDE should now provide autocompletion for both models and services.")

        logout_url = f"{args.url.rstrip('/')}/entity/auth/logout"
        session.post(logout_url)

if __name__ == "__main__":
    main()