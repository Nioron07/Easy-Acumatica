import argparse
import sys
import textwrap
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

# Add project source to path to allow importing the package
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / 'src'))

from easy_acumatica.helpers import _raise_with_detail


def _map_schema_type_to_python_type(prop_details: Dict[str, Any], is_required: bool) -> str:
    """Maps a schema property to a Python type hint string."""
    
    def get_base_hint(details: Dict[str, Any]) -> str:
        schema_type = details.get("type")
        schema_format = details.get("format")

        if schema_type == "string":
            return "datetime" if schema_format == "date-time" else "str"
        if schema_type == "integer": return "int"
        if schema_type == "number": return "float"
        if schema_type == "boolean": return "bool"

        if "$ref" in details:
            ref_name = details["$ref"].split("/")[-1]
            if "Value" in ref_name:
                if "String" in ref_name or "Guid" in ref_name: return "str"
                if "Decimal" in ref_name or "Double" in ref_name: return "float"
                if "Int" in ref_name or "Short" in ref_name or "Long" in ref_name or "Byte" in ref_name: return "int"
                if "Boolean" in ref_name: return "bool"
                if "DateTime" in ref_name: return "datetime"
            return f"'{ref_name}'"
            
        if schema_type == "array":
            item_hint = _map_schema_type_to_python_type(details.get("items", {}), False)
            return f"List[{item_hint}]"
        
        return "Any"

    base_hint = get_base_hint(prop_details)
    return base_hint if is_required else f"Optional[{base_hint}]"


def generate_model_stubs(schema: Dict[str, Any]) -> str:
    pyi_content = [
        "from __future__ import annotations",
        "from typing import Any, List, Optional, Union",
        "from dataclasses import dataclass",
        "from datetime import datetime",
        "from .core import BaseDataClassModel\n"
    ]
    
    schemas = schema.get("components", {}).get("schemas", {})
    primitive_wrappers = {
        "StringValue", "DecimalValue", "BooleanValue", "DateTimeValue",
        "GuidValue", "IntValue", "ShortValue", "LongValue", "ByteValue", "DoubleValue"
    }

    for name, definition in sorted(schemas.items()):
        if name in primitive_wrappers:
            continue

        pyi_content.append(f"\n@dataclass")
        class_lines = [f"class {name}(BaseDataClassModel):"]
        required_fields = definition.get("required", [])
        
        properties = {}
        if 'allOf' in definition:
            for item in definition['allOf']:
                if 'properties' in item: properties.update(item['properties'])
        else:
            properties = definition.get("properties", {})

        if not properties:
            class_lines.append("    ...")
        else:
            for prop_name, prop_details in sorted(properties.items()):
                if prop_name in ["note", "rowNumber", "error", "_links"]: continue
                is_required = prop_name in required_fields
                type_hint = _map_schema_type_to_python_type(prop_details, is_required)
                class_lines.append(f"    {prop_name}: {type_hint} = ...")
        
        pyi_content.extend(class_lines)
    
    return "\n".join(pyi_content) + "\n"


def generate_client_stubs(schema: Dict[str, Any]) -> str:
    paths = schema.get("paths", {})
    tags_to_ops: Dict[str, Dict] = {}
    for path, path_info in paths.items():
        for http_method, details in path_info.items():
            tag = details.get("tags", [None])[0]
            if not tag or http_method not in ['get', 'put', 'post', 'delete']: continue
            if tag not in tags_to_ops: tags_to_ops[tag] = {}
            op_id = details.get("operationId", "")
            if op_id: tags_to_ops[tag][op_id] = (path, http_method, details)

    pyi_content = [
        "from __future__ import annotations",
        "from typing import Any, Union, List",
        "from .core import BaseService, BaseDataClassModel",
        "from .odata import QueryOptions",
        "from . import models\n"
    ]

    for tag, operations in sorted(tags_to_ops.items()):
        service_class_name = f"{tag}Service"
        pyi_content.append(f"\nclass {service_class_name}(BaseService):")
        
        if not operations:
            pyi_content.append("    ...")
        else:
            for op_id, (path, http_method, details) in sorted(operations.items()):
                # --- THIS IS THE FIX ---
                # The previous logic created a double underscore for some action names.
                # This ensures the name is always correctly formatted snake_case.
                name_part = op_id.split('_', 1)[-1]
                method_name = ''.join(['_' + i.lower() if i.isupper() else i for i in name_part]).lstrip('_')
                method_name = method_name.replace('__', '_')

                if "InvokeAction" in op_id:
                    ref = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
                    model_name = ref.split("/")[-1]
                    pyi_content.append(f"    def {method_name}(self, invocation: models.{model_name}, api_version: str | None = None) -> Any: ...")
                elif "PutEntity" in op_id:
                    ref = details.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema", {}).get("$ref", "")
                    model_name = ref.split("/")[-1]
                    pyi_content.append(f"    def {method_name}(self, data: Union[dict, models.{model_name}], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "PutFile" in op_id:
                    pyi_content.append(f"    def {method_name}(self, entity_id: str, filename: str, data: bytes, comment: str | None = None, api_version: str | None = None) -> None: ...")
                elif "GetById" in op_id or "GetByKeys" in op_id:
                    pyi_content.append(f"    def {method_name}(self, entity_id: Union[str, List[str]], options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "GetList" in op_id:
                    pyi_content.append(f"    def {method_name}(self, options: QueryOptions | None = None, api_version: str | None = None) -> Any: ...")
                elif "DeleteById" in op_id or "DeleteByKeys" in op_id:
                    pyi_content.append(f"    def {method_name}(self, entity_id: Union[str, List[str]], api_version: str | None = None) -> None: ...")
                elif "GetAdHocSchema" in op_id:
                    pyi_content.append(f"    def {method_name}(self, api_version: str | None = None) -> Any: ...")
    
    pyi_content.append("\nclass AcumaticaClient:")
    for tag in sorted(tags_to_ops.keys()):
        service_class_name = f"{tag}Service"
        attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in tag]).lstrip('_') + 's'
        pyi_content.append(f"    {attr_name}: {service_class_name}")
    pyi_content.append("    models: models\n")

    return "\n".join(pyi_content)


def main():
    parser = argparse.ArgumentParser(description="Generate .pyi stub files for easy-acumatica.")
    parser.add_argument("--url", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--tenant", required=True)
    parser.add_argument("--endpoint-version", required=True)
    parser.add_argument("--endpoint-name", default="Default")
    parser.add_argument("--branch", required=False)
    args = parser.parse_args()

    with requests.Session() as session:
        login_payload = {
            "name": args.username,
            "password": args.password,
            "tenant": args.tenant,
        }
        login_url = f"{args.url.rstrip('/')}/entity/auth/login"
        login_resp = session.post(login_url, json=login_payload)
        _raise_with_detail(login_resp)
        print("Login successful.")

        schema_url = f"{args.url.rstrip('/')}/entity/{args.endpoint_name}/{args.endpoint_version}/swagger.json"
        schema_resp = session.get(schema_url)
        _raise_with_detail(schema_resp)
        schema = schema_resp.json()
        print("Schema fetched successfully.")

        model_pyi = generate_model_stubs(schema)
        Path("src/easy_acumatica/models.pyi").write_text(model_pyi, encoding='utf-8')
        print(f"✅ Success! Model stubs written to src/easy_acumatica/models.pyi")

        client_pyi = generate_client_stubs(schema)
        Path("src/easy_acumatica/client.pyi").write_text(client_pyi, encoding='utf-8')
        print(f"✅ Success! Client stubs written to src/easy_acumatica/client.pyi")

        logout_url = f"{args.url.rstrip('/')}/entity/auth/logout"
        session.post(logout_url)

if __name__ == "__main__":
    main()