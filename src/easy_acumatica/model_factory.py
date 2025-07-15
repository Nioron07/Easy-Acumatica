from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, Tuple, ForwardRef
from dataclasses import make_dataclass, field, Field
import datetime

from .core import BaseDataClassModel

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
        schemas = self._schema.get("components", {}).get("schemas", {})
        for name in schemas:
            if name not in self._primitive_wrappers:
                self._get_or_build_model(name)
        
        for model in self._models.values():
            model.__annotations__ = {
                k: v.format(**self._models) if isinstance(v, str) else v
                for k, v in model.__annotations__.items()
            }
        return self._models

    def _get_or_build_model(self, name: str) -> Type[BaseDataClassModel]:
        if name in self._models:
            return self._models[name]

        definition = self._schema.get("components", {}).get("schemas", {}).get(name)
        if not definition:
            raise ValueError(f"Schema definition not found for model: {name}")

        fields: List[Tuple[str, Type, Field]] = []
        
        # Correctly get the list of required fields for this specific model definition
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
            
            # Determine if the field is required and map its type accordingly
            is_required = prop_name in required_fields
            python_type, default_value = self._map_type(prop_details, is_required)
            
            field_info = field(default=default_value)
            if default_value is list:
                field_info = field(default_factory=list)

            fields.append((prop_name, python_type, field_info))
            
        model = make_dataclass(
            name,
            fields=fields,
            bases=(BaseDataClassModel,),
            namespace={'build': BaseDataClassModel.build},
            frozen=False
        )

        self._models[name] = model
        return model

    def _get_base_type(self, prop_details: Dict[str, Any]) -> Tuple[Type, Any]:
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
            if "Value" in ref_name: # Handle primitive wrappers
                if "String" in ref_name or "Guid" in ref_name: return str, None
                if "Decimal" in ref_name or "Double" in ref_name: return float, None
                if "Int" in ref_name or "Short" in ref_name or "Long" in ref_name or "Byte" in ref_name: return int, None
                if "Boolean" in ref_name: return bool, False
                if "DateTime" in ref_name: return datetime.datetime, None
            return ForwardRef(f"'{ref_name}'"), None # Handle complex types

        if schema_type == "array":
            # Item types within a list are considered optional by default
            item_type, _ = self._map_type(prop_details.get("items", {}), False)
            return List[item_type], list

        return Any, None

    def _map_type(self, prop_details: Dict[str, Any], is_required: bool) -> Tuple[Type, Any]:
        """Maps a schema property to a Python type, correctly handling optionality."""
        base_type, default_value = self._get_base_type(prop_details)

        if is_required:
            return base_type, default_value
        else:
            return Optional[base_type], default_value