#!/usr/bin/env python3
"""
Generate PEP 561 compliant stub files for easy-acumatica.

This script generates .pyi stub files that work properly with VSCode, mypy, and other type checkers
by placing them in the correct locations according to PEP 561.
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


def generate_service_stub(service_name: str, service_instance: BaseService) -> List[str]:
    """Generate stub lines for a service class."""
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
            # Get method signature
            try:
                sig = inspect.signature(method)
            except:
                # If we can't get signature, create a generic one
                lines.append(f"    def {method_name}(self, *args, **kwargs) -> Any: ...")
                continue
            
            # Build parameter list
            params = []
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    params.append('self')
                    continue
                
                # Get parameter annotation
                if param.annotation != inspect._empty:
                    type_str = get_type_annotation_string(param.annotation)
                else:
                    type_str = "Any"
                
                # Handle default values
                if param.default != inspect._empty:
                    if param.default is None:
                        params.append(f"{param_name}: {type_str} = None")
                    elif isinstance(param.default, str):
                        params.append(f"{param_name}: {type_str} = '{param.default}'")
                    elif isinstance(param.default, (int, float, bool)):
                        params.append(f"{param_name}: {type_str} = {param.default}")
                    else:
                        params.append(f"{param_name}: {type_str} = ...")
                else:
                    params.append(f"{param_name}: {type_str}")
            
            # Get return annotation
            if sig.return_annotation != inspect._empty:
                return_type = get_type_annotation_string(sig.return_annotation)
            else:
                return_type = "Any"
            
            # Generate method definition
            param_str = ", ".join(params)
            lines.append(f"    def {method_name}({param_str}) -> {return_type}:")
            
            # Add docstring if it exists
            if method.__doc__:
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


def create_py_typed_file(package_dir: Path) -> None:
    """Create a py.typed file to mark the package as PEP 561 compliant."""
    py_typed_path = package_dir / "py.typed"
    py_typed_path.write_text("")
    print(f"✅ Created py.typed marker at {py_typed_path}")


def generate_stubs_inline(client: AcumaticaClient, package_dir: Path) -> None:
    """
    Generate stub files inline with the package (PEP 561 compliant).
    This places .pyi files alongside .py files in the package.
    """
    print("Generating inline stub files (PEP 561 compliant)...")
    
    # Create py.typed file to mark package as supporting type checking
    create_py_typed_file(package_dir)
    
    # Generate client.pyi
    print("Generating client.pyi...")
    client_lines = [
        "from __future__ import annotations",
        "from typing import Any, Union, List, Dict, Optional",
        "from . import models",
        "from .core import BaseService, BaseDataClassModel",
        "from .odata import QueryOptions",
        "import requests",
        "",
        "",
    ]
    
    # Get all service attributes from the client
    services = []
    for attr_name in dir(client):
        if not attr_name.startswith('_') and attr_name not in ['models', 'session', 'base_url', 
                                                                'tenant', 'username', 'verify_ssl',
                                                                'persistent_login', 'retry_on_idle_logout',
                                                                'endpoint_name', 'endpoint_version',
                                                                'timeout', 'endpoints']:
            attr = getattr(client, attr_name)
            if isinstance(attr, BaseService):
                # Convert attribute name to PascalCase service name
                parts = attr_name.rstrip('s').split('_')
                service_name = ''.join(part.title() for part in parts)
                services.append((service_name, attr_name, attr))
    
    # Generate service class stubs
    for service_name, attr_name, service_instance in services:
        service_lines = generate_service_stub(service_name, service_instance)
        client_lines.extend(service_lines)
        client_lines.append("")  # Empty line between classes
    
    # Generate client class
    client_lines.extend([
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
        "    endpoints: Dict[str, Dict]",
        "    session: requests.Session",
        "    ",
        "    # Service attributes"
    ])
    
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
        "    ) -> None: ...",
        "    ",
        "    def login(self) -> int: ...",
        "    def logout(self) -> int: ...", 
        "    def close(self) -> None: ...",
        "    def __enter__(self) -> 'AcumaticaClient': ...",
        "    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...",
    ])
    
    # Write client.pyi
    (package_dir / "client.pyi").write_text("\n".join(client_lines))
    print("✅ Generated client.pyi")
    
    # Generate models.pyi
    print("Generating models.pyi...")
    model_lines = [
        "from __future__ import annotations",
        "from typing import Any, List, Optional, Union",
        "from dataclasses import dataclass",
        "from datetime import datetime",
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
    (package_dir / "models.pyi").write_text("\n".join(model_lines))
    print(f"✅ Generated models.pyi with {len(model_classes)} models")
    
    print(f"\n✅ Generated inline stub files in {package_dir}")
    print("These stubs will be automatically discovered by VSCode, mypy, and other type checkers!")


def generate_stubs_external(client: AcumaticaClient, output_dir: Path) -> None:
    """
    Generate external stub package (easy_acumatica-stubs).
    This creates a separate installable package with stubs.
    """
    stubs_dir = output_dir / "easy_acumatica-stubs"
    stubs_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"Generating external stub package in {stubs_dir}...")
    
    # Generate the same files as inline method
    generate_stubs_inline(client, stubs_dir)
    
    # Create __init__.pyi for the stub package
    init_lines = [
        '"""Type stubs for easy_acumatica."""',
        "from .client import AcumaticaClient",
        "",
        "__all__ = ['AcumaticaClient']",
    ]
    (stubs_dir / "__init__.pyi").write_text("\n".join(init_lines))
    
    # Create setup.py for the stub package
    setup_py_content = '''"""Setup script for easy_acumatica-stubs package."""
from setuptools import setup, find_packages

setup(
    name="easy_acumatica-stubs",
    version="0.1.0",
    description="Type stubs for easy_acumatica",
    packages=find_packages(),
    package_data={
        "easy_acumatica-stubs": ["*.pyi", "py.typed"],
    },
    install_requires=[
        "easy_acumatica",  # The runtime package
    ],
    python_requires=">=3.8",
)
'''
    (output_dir / "setup.py").write_text(setup_py_content)
    
    print(f"\n✅ Generated external stub package in {stubs_dir}")
    print("To install: cd to the output directory and run 'pip install -e .'")


def main():
    parser = argparse.ArgumentParser(description="Generate PEP 561 compliant stub files for easy-acumatica.")
    parser.add_argument("--url", help="Base URL of the Acumatica instance.")
    parser.add_argument("--username", help="Username for authentication.")
    parser.add_argument("--password", help="Password for authentication.")
    parser.add_argument("--tenant", help="The tenant to connect to.")
    parser.add_argument("--endpoint-version", help="The API endpoint version to use.")
    parser.add_argument("--endpoint-name", default="Default", help="The API endpoint name.")
    parser.add_argument("--output-dir", default=".", help="Output directory for stub files.")
    parser.add_argument("--mode", choices=["inline", "external", "both"], default="inline", 
                       help="Stub generation mode: 'inline' (PEP 561 compliant, recommended), 'external' (separate package), or 'both'")
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
    )
    
    print("✅ Successfully connected and initialized client")
    
    # Generate stubs based on mode
    output_dir = Path(args.output_dir)
    
    if args.mode in ["inline", "both"]:
        # Find the package installation directory
        package_dir = Path(easy_acumatica.__file__).parent
        generate_stubs_inline(client, package_dir)
    
    if args.mode in ["external", "both"]:
        generate_stubs_external(client, output_dir)
    
    # Clean up
    client.logout()
    print("\n✅ Logged out successfully")
    print("\n" + "="*60)
    print("STUB GENERATION COMPLETE!")
    print("="*60)
    
    if args.mode in ["inline", "both"]:
        print("\n📝 INLINE STUBS (Recommended):")
        print("✅ Generated PEP 561 compliant stub files")
        print("✅ Added py.typed marker file")
        print("✅ Stubs will be automatically discovered by:")
        print("   - VSCode with Pylance")
        print("   - mypy")
        print("   - PyCharm")
        print("   - Other PEP 561 compliant type checkers")
        print("\n🔄 No action needed - restart your IDE and enjoy type hints!")
    
    if args.mode in ["external", "both"]:
        print(f"\n📦 EXTERNAL STUB PACKAGE:")
        print(f"✅ Generated installable stub package in {output_dir}")
        print("📋 To use:")
        print(f"   cd {output_dir}")
        print("   pip install -e .")


if __name__ == "__main__":
    main()