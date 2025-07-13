import argparse
import requests
import sys
from pathlib import Path
from typing import Dict, Any, Type, List, Optional
import textwrap

# Add the project's source directory to the Python path
project_root = Path(__file__).resolve().parent
sys.path.insert(0, str(project_root / 'src'))

from easy_acumatica.model_factory import ModelFactory
from easy_acumatica.helpers import _raise_with_detail

def generate_pyi_stubs(schema: Dict[str, Any]) -> str:
    """
    Parses the OpenAPI schema and generates the content for a .pyi stub file.
    """
    factory = ModelFactory(schema)
    models = factory.build_models()
    
    pyi_content = [
        "from __future__ import annotations",
        "from typing import Any, List, Optional",
        "from dataclasses import dataclass",
        "from datetime import datetime",
        "from easy_acumatica.core import BaseDataClassModel\n\n"
    ]

    for name, model_class in sorted(models.items()):
        class_lines = [f"@dataclass", f"class {name}(BaseDataClassModel):"]
        
        # --- CORE FIX: Introspect fields and write them to the stub ---
        fields = model_class.__dataclass_fields__
        if not fields:
            class_lines.append("    ...")
        else:
            for field_name, field_obj in fields.items():
                type_hint = str(field_obj.type).replace('typing.', '')
                # Clean up ForwardRef for cleaner .pyi file
                type_hint = type_hint.replace("ForwardRef('", "'").replace("')", "'")
                class_lines.append(f"    {field_name}: {type_hint}")

        pyi_content.extend(class_lines)
        pyi_content.append("\n")

    return "\n".join(pyi_content)

def main():
    """ Main function to fetch schema and generate .pyi file. """
    parser = argparse.ArgumentParser(
        description="Generate .pyi stub files for easy-acumatica models.",
        formatter_class=argparse.RawTextHelpFormatter
    )
    parser.add_argument("--url", required=True, help="Base URL of the Acumatica instance")
    parser.add_argument("--username", required=True, help="Acumatica username")
    parser.add_argument("--password", required=True, help="Acumatica password")
    parser.add_argument("--tenant", required=True, help="Acumatica tenant")
    parser.add_argument("--branch", required=False, help="Acumatica branch (optional)")
    parser.add_argument("--endpoint-name", default="Default", help="The endpoint name")
    parser.add_argument("--endpoint-version", required=True, help="The endpoint version")
    parser.add_argument("--output-path", default="src/easy_acumatica/models.pyi", help="Path for the .pyi file")
    
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

        print("Generating .pyi stub content...")
        pyi_content = generate_pyi_stubs(schema)

        output_file = Path(args.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(pyi_content, encoding='utf-8')
        print(f"\n✅ Success! Stub file generated at: {output_file.absolute()}")

        logout_url = f"{args.url.rstrip('/')}/entity/auth/logout"
        session.post(logout_url)

if __name__ == "__main__":
    main()