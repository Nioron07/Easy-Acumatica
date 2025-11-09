# src/easy_acumatica/model_factory.py

from __future__ import annotations

import datetime
import textwrap
from dataclasses import Field, field, make_dataclass
from typing import Any, Dict, ForwardRef, List, Optional, Tuple, Type, get_type_hints

from .core import BaseDataClassModel


def _generate_model_docstring(name: str, definition: Dict[str, Any]) -> str:
    """Generates a docstring for a dataclass model."""
    description = definition.get("description", f"Represents the {name} entity.")
    docstring = [f"{description}\n"]
    docstring.append("Attributes:")

    required_fields = definition.get("required", [])
    properties = {}
    if 'allOf' in definition:
        for item in definition['allOf']:
            if 'properties' in item:
                properties.update(item['properties'])
    else:
        properties = definition.get("properties", {})

    if not properties:
        docstring.append("    This model has no defined properties.")
    else:
        for prop_name, prop_details in sorted(properties.items()):
            prop_type = prop_details.get('type', 'Any')
            if '$ref' in prop_details:
                prop_type = prop_details['$ref'].split('/')[-1]

            required_marker = " (required)" if prop_name in required_fields else ""
            docstring.append(f"    {prop_name} ({prop_type}){required_marker}")

    return textwrap.indent("\n".join(docstring), "    ")


class ModelFactory:
    """
    Dynamically builds Python dataclasses from an Acumatica OpenAPI schema.
    """

    def __init__(self, schema: Dict[str, Any]):
        self._schema = schema
        self._models: Dict[str, Type[BaseDataClassModel]] = {}
        self._primitive_wrappers = {
            "StringValue", "DecimalValue", "BooleanValue", "DateTimeValue",
            "GuidValue", "IntValue", "ShortValue", "LongValue", "ByteValue",
            "DoubleValue"
        }

    def build_models(self) -> Dict[str, Type[BaseDataClassModel]]:
        """
        Builds all models from the schema, creating placeholder models first,
        then resolving forward references.
        """
        schemas = self._schema.get("components", {}).get("schemas", {})
        for name in schemas:
            if name not in self._primitive_wrappers:
                self._get_or_build_model(name)

        # Iterate over a copy of the values to prevent RuntimeError
        for model in list(self._models.values()):
            try:
                resolved_annotations = get_type_hints(model, globalns=self._models, localns=self._models)
                model.__annotations__ = resolved_annotations
            except Exception as e:
                print(f"Warning: Could not resolve type hints for model {model.__name__}: {e}")

        return self._models

    def _get_or_build_model(self, name: str) -> Type[BaseDataClassModel]:
        if name in self._models:
            return self._models[name]

        definition = self._schema.get("components", {}).get("schemas", {}).get(name)
        if not definition:
            raise ValueError(f"Schema definition not found for model: {name}")

        fields_list: List[Tuple[str, Type, Field]] = []
        required_fields = definition.get("required", [])

        properties = {}
        if 'allOf' in definition:
            for item in definition['allOf']:
                if 'properties' in item:
                    properties.update(item['properties'])
        else:
            properties = definition.get("properties", {})

        for prop_name, prop_details in properties.items():
            if prop_name in ["note", "rowNumber", "error", "_links"]:
                continue

            is_required = prop_name in required_fields
            python_type, default_value = self._map_type(prop_details, is_required)

            if default_value is list:
                field_info = field(default_factory=list)
            else:
                field_info = field(default=default_value)

            fields_list.append((prop_name, python_type, field_info))

        # Create helper functions that will be shared by all models
        def _simplify_type_impl(field_type, visited: set, model_registry: Dict[str, type]) -> Any:
            """Convert Python type annotation to simple representation with type+fields structure."""
            from typing import get_origin, get_args, Union, ForwardRef
            import dataclasses

            # Handle None type
            if field_type is type(None):
                raise ValueError(f"ERROR: NoneType encountered - field_type={field_type}")

            # Get origin for generic types (List, Optional, etc.)
            origin = get_origin(field_type)

            # Handle Optional types - unwrap before checking ForwardRef
            if origin is Union:
                args = get_args(field_type)
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 0:
                    raise ValueError(f"ERROR: Union with only None types - field_type={field_type}, args={args}")
                elif len(non_none_args) == 1:
                    return _simplify_type_impl(non_none_args[0], visited, model_registry)
                elif len(non_none_args) > 1:
                    # For multi-type unions, return type with empty fields
                    union_str = f"Union[{', '.join(_simplify_type_impl(arg, visited, model_registry)['type'] if isinstance(_simplify_type_impl(arg, visited, model_registry), dict) else str(_simplify_type_impl(arg, visited, model_registry)) for arg in non_none_args)}]"
                    return {"type": union_str, "fields": {}}

            # Handle ForwardRef - try to resolve it from model_registry
            if isinstance(field_type, (ForwardRef, str)):
                ref_name = field_type.__forward_arg__ if isinstance(field_type, ForwardRef) else field_type
                ref_name = ref_name.strip("'\"")  # Remove quotes if present
                if ref_name in model_registry:
                    field_type = model_registry[ref_name]
                    # Re-get origin after resolving ForwardRef
                    origin = get_origin(field_type)
                else:
                    raise ValueError(f"ERROR: ForwardRef '{ref_name}' not found in model_registry. Available: {list(model_registry.keys())[:10]}")

            # Handle List types
            if origin is list:
                args = get_args(field_type)
                if args:
                    inner_type = args[0]

                    # Handle Optional/Union inside List - unwrap it
                    inner_origin = get_origin(inner_type)
                    if inner_origin is Union:
                        inner_args = get_args(inner_type)
                        # Filter out NoneType
                        non_none_inner = [arg for arg in inner_args if arg is not type(None)]
                        if len(non_none_inner) == 1:
                            inner_type = non_none_inner[0]

                    # Handle ForwardRef inside List
                    if isinstance(inner_type, (ForwardRef, str)):
                        ref_name = inner_type.__forward_arg__ if isinstance(inner_type, ForwardRef) else inner_type
                        ref_name = ref_name.strip("'\"")
                        if ref_name in model_registry:
                            inner_type = model_registry[ref_name]

                    # For dataclass types in lists, return type + fields structure
                    if dataclasses.is_dataclass(inner_type):
                        fields_schema = _get_simple_schema_impl(inner_type, visited.copy(), model_registry)
                        return {
                            "type": f"List[{inner_type.__name__}]",
                            "fields": fields_schema
                        }

                    # For primitive lists
                    if hasattr(inner_type, '__name__') and inner_type.__name__ in ('str', 'int', 'float', 'bool', 'datetime'):
                        return {
                            "type": f"List[{inner_type.__name__}]",
                            "fields": {}
                        }

                    # Fallback for unknown list types
                    raise ValueError(f"ERROR: Unknown list inner type - inner_type={inner_type}")
                raise ValueError(f"ERROR: List with no args - field_type={field_type}")

            # Handle dataclass models
            if dataclasses.is_dataclass(field_type):
                class_name = field_type.__name__
                # Prevent circular references
                if class_name in visited:
                    return {"type": f"(circular: {class_name})", "fields": {}}
                visited.add(class_name)
                fields_schema = _get_simple_schema_impl(field_type, visited, model_registry)
                visited.discard(class_name)
                return {
                    "type": class_name,
                    "fields": fields_schema
                }

            # Handle primitive types
            if hasattr(field_type, '__name__'):
                type_name = field_type.__name__
                if type_name in ('str', 'int', 'float', 'bool', 'datetime'):
                    return {"type": type_name, "fields": {}}

            # Default for unknown types
            raise ValueError(f"ERROR: Unknown type - field_type={field_type}, type={type(field_type)}, hasattr __name__={hasattr(field_type, '__name__')}")

        def _get_simple_schema_impl(model_class: type, visited: set, model_registry: Dict[str, type]) -> Dict[str, Any]:
            """Extract simplified schema from dataclass, recursively expanding nested models."""
            if visited is None:
                visited = set()

            simple_schema = {}

            if hasattr(model_class, '__annotations__'):
                for field_name, field_type in model_class.__annotations__.items():
                    simplified = _simplify_type_impl(field_type, visited, model_registry)
                    simple_schema[field_name] = simplified

            return simple_schema

        # Create get_schema classmethod
        @classmethod
        def get_schema(cls) -> Dict[str, Any]:
            """
            Get the schema for this model showing Python types.

            Returns a simplified, recursively expanded schema.
            Nested models are expanded as dictionaries, arrays are shown as lists.

            Returns:
                Dictionary mapping field names to types:
                - Primitives: 'str', 'int', 'bool', 'float', 'datetime'
                - Nested models: {'field1': 'type1', 'field2': 'type2', ...}
                - Arrays: [{'field1': 'type1', ...}]

            Example:
                >>> schema = Customer.get_schema()
                >>> # Returns: {
                >>> #   'CustomerID': 'str',
                >>> #   'CustomerName': 'str',
                >>> #   'BillingContact': {
                >>> #     'Email': 'str',
                >>> #     'DisplayName': 'str',
                >>> #     ...
                >>> #   },
                >>> #   ...
                >>> # }
            """
            return _get_simple_schema_impl(cls, set(), cls._model_registry)

        model = make_dataclass(
            name,
            fields=fields_list,
            bases=(BaseDataClassModel,),
            namespace={
                'build': BaseDataClassModel.build,
                'get_schema': get_schema,
                '_model_registry': self._models  # Store reference to all models
            },
            frozen=False
        )
        model.__module__ = 'easy_acumatica.models'
        model.__doc__ = _generate_model_docstring(name, definition)
        self._models[name] = model
        return model

    def _get_base_type(self, prop_details: Dict[str, Any]) -> Tuple[Type | ForwardRef, Any]:
        """Helper to get the fundamental type and default value, ignoring optionality."""
        schema_type = prop_details.get("type")
        schema_format = prop_details.get("format")

        if schema_type == "string":
            return (datetime.datetime, None) if schema_format == "date-time" else (str, None)
        if schema_type == "integer":
            return int, None
        if schema_type == "number":
            return float, None
        if schema_type == "boolean":
            return bool, False

        if "$ref" in prop_details:
            ref_name = prop_details["$ref"].split("/")[-1]
            if "Value" in ref_name:
                if "String" in ref_name or "Guid" in ref_name: return str, None
                if "Decimal" in ref_name or "Double" in ref_name: return float, None
                if "Int" in ref_name or "Short" in ref_name or "Long" in ref_name or "Byte" in ref_name: return int, None
                if "Boolean" in ref_name: return bool, False
                if "DateTime" in ref_name: return datetime.datetime, None
            return ForwardRef(f"'{ref_name}'"), None

        if schema_type == "array":
            item_type, _ = self._map_type(prop_details.get("items", {}), is_required=False)
            return List[item_type], list

        return Any, None

    def _map_type(self, prop_details: Dict[str, Any], is_required: bool) -> Tuple[Type | ForwardRef, Any]:
        """Maps a schema property to a Python type, correctly handling optionality."""
        base_type, default_value = self._get_base_type(prop_details)

        if is_required:
            return base_type, default_value
        else:
            return Optional[base_type], default_value
