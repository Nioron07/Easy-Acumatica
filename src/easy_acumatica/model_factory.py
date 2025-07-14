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

    def build_models(self) -> Dict[str, Type[BaseDataClassModel]]:
        """
        Parses the entire schema and generates all corresponding models.
        """
        schemas = self._schema.get("components", {}).get("schemas", {})
        for name in schemas:
            self._get_or_build_model(name)
        # Second pass to resolve all forward references in type hints
        for model in self._models.values():
            model.__annotations__ = {
                k: v.format(**self._models) if isinstance(v, str) else v
                for k, v in model.__annotations__.items()
            }
        return self._models

    def _get_or_build_model(self, name: str) -> Type[BaseDataClassModel]:
        """
        Retrieves a model from the cache or builds, caches, and returns it.
        """
        if name in self._models:
            return self._models[name]

        definition = self._schema.get("components", {}).get("schemas", {}).get(name)
        if not definition:
            raise ValueError(f"Schema definition not found for model: {name}")

        fields: List[Tuple[str, Type, Field]] = []
        
        # --- CORE FIX: Navigate the 'allOf' structure ---
        properties = {}
        if 'allOf' in definition:
            # fields.append(('id', Optional[str], field(default=None)))
            for item in definition['allOf']:
                if 'properties' in item:
                    properties.update(item['properties'])
        else:
            properties = definition.get("properties", {})

        for prop_name, prop_details in properties.items():
            if prop_name in ["id", "note", "rowNumber", "error", "_links"]:
                continue
            
            python_type, default_value = self._map_type(prop_details)
            
            field_info = field(default=default_value)
            # Use default_factory for mutable types like lists
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

    def _map_type(self, prop_details: Dict[str, Any]) -> Tuple[Type, Any]:
        """
        Maps an OpenAPI schema property type to a Python type and a default value.
        """
        if "$ref" in prop_details:
            ref_name = prop_details["$ref"].split("/")[-1]
            # Use a string forward reference to handle circular dependencies
            return Optional[ForwardRef(ref_name)], None

        if prop_details.get("type") == "array":
            item_type, _ = self._map_type(prop_details.get("items", {}))
            return List[item_type], list

        ref_path = prop_details.get("allOf", [{}])[0].get("$ref", "")
        if "StringValue" in ref_path: return Optional[str], None
        if "DecimalValue" in ref_path: return Optional[float], None
        if "BooleanValue" in ref_path: return Optional[bool], False
        if "DateTimeValue" in ref_path: return Optional[datetime.datetime], None
        if "GuidValue" in ref_path: return Optional[str], None
        if "IntValue" in ref_path: return Optional[int], None
        if "ShortValue" in ref_path: return Optional[int], None
        if "LongValue" in ref_path: return Optional[int], None
        if "ByteValue" in ref_path: return Optional[int], None
        if "DoubleValue" in ref_path: return Optional[float], None

        return Optional[Any], None