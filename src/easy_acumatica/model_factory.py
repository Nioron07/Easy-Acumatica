from __future__ import annotations
from typing import Any, Dict, List, Optional, Type, Tuple, ForwardRef
from dataclasses import make_dataclass, field, Field
import datetime

from .core import BaseDataClassModel

class ModelFactory:
    """
    Dynamically builds Python dataclasses from an Acumatica OpenAPI schema.

    This factory is the core of the dynamic model generation system. It reads the
    `components.schemas` section of the `swagger.json` file and programmatically
    constructs Python `dataclass` objects that mirror the structure of the API
    entities.

    Key features:
    - Caches generated models to avoid redundant work and handle recursion.
    - Intelligently parses Acumatica's common schema patterns (e.g., 'allOf').
    - Maps OpenAPI data types to their Python equivalents (e.g., StringValue -> str).
    - Skips creating unnecessary wrapper classes for primitive types.
    """

    def __init__(self, schema: Dict[str, Any]):
        """
        Initializes the factory with the full OpenAPI schema.

        Args:
            schema: The complete dictionary parsed from the swagger.json file.
        """
        self._schema = schema
        # _models serves as a cache. Once a model is built, it's stored here
        # to prevent re-building and to resolve circular dependencies.
        self._models: Dict[str, Type[BaseDataClassModel]] = {}
        # A set of the wrapper types we want to ignore and replace with primitives.
        self._primitive_wrappers = {
            "StringValue", "DecimalValue", "BooleanValue", "DateTimeValue",
            "GuidValue", "IntValue", "ShortValue", "LongValue", "ByteValue",
            "DoubleValue"
        }

    def build_models(self) -> Dict[str, Type[BaseDataClassModel]]:
        """
        Parses the entire schema and generates all corresponding models.

        This is the main public method of the factory. It iterates through all
        the schemas defined in the swagger file and ensures a dataclass is
        created for each one.

        Returns:
            A dictionary mapping model names (e.g., "Contact") to their newly
            created Python `dataclass` type.
        """
        schemas = self._schema.get("components", {}).get("schemas", {})
        for name in schemas:
            # We only build models that are not primitive wrappers.
            if name not in self._primitive_wrappers:
                self._get_or_build_model(name)
        
        # After all models are created, this second pass resolves any ForwardRef
        # type hints, connecting the dataclasses together.
        for model in self._models.values():
            # Using localns=self._models allows the string hints to find the other generated classes
            model.__annotations__ = {
                k: v.format(**self._models) if isinstance(v, str) else v
                for k, v in model.__annotations__.items()
            }
        return self._models

    def _get_or_build_model(self, name: str) -> Type[BaseDataClassModel]:
        """
        Retrieves a model from the cache or builds, caches, and returns it.

        This method is the core worker of the factory. It contains the logic
        for parsing a single schema definition and turning it into a dataclass.
        Using a cache is critical for performance and for handling recursive
        schema definitions (e.g., a model that references itself).

        Args:
            name: The name of the model to get or build (e.g., "Contact").

        Returns:
            The generated or cached dataclass for the given name.
        """
        # Step 1: Check the cache first to avoid re-processing.
        if name in self._models:
            return self._models[name]

        # Step 2: Retrieve the schema definition for the requested model.
        definition = self._schema.get("components", {}).get("schemas", {}).get(name)
        if not definition:
            raise ValueError(f"Schema definition not found for model: {name}")

        # Step 3: Prepare a list to hold the fields for the new dataclass.
        fields: List[Tuple[str, Type, Field]] = []
        
        # Step 4: Intelligently add an 'id' field for top-level entities.
        # Acumatica entity schemas use the 'allOf' keyword. This is a reliable way
        # to check if we're building a main entity (like Contact) versus a simple
        # type (like StringValue). Main entities need an `id` field to be
        # referenced in updates and actions.
        is_entity = 'allOf' in definition
        if is_entity:
            # We add `id` as an optional string that defaults to None.
            # `repr=False` is a small cleanup to make debugging cleaner.
            fields.append(('id', Optional[str], field(default=None, repr=False)))

        # Step 5: Extract the field properties from the schema.
        # The actual fields are usually nested inside the 'allOf' array.
        properties = {}
        if is_entity:
            for item in definition['allOf']:
                if 'properties' in item:
                    properties.update(item['properties'])
        else: # For simple, non-entity models like 'StringValue' or 'Address'
            properties = definition.get("properties", {})

        # Step 6: Iterate over each property and convert it to a dataclass field.
        for prop_name, prop_details in properties.items():
            # Skip read-only or internal fields that shouldn't be part of a
            # request payload created by the user.
            if prop_name in ["id", "note", "rowNumber", "error", "_links"]:
                continue
            
            # Map the OpenAPI type to a Python type (e.g., 'StringValue' -> str).
            python_type, default_value = self._map_type(prop_details)
            
            # Create a dataclass field. Use `default_factory=list` for lists
            # to avoid mutable default argument issues.
            field_info = field(default=default_value)
            if default_value is list:
                field_info = field(default_factory=list)

            fields.append((prop_name, python_type, field_info))

        # Step 7: Create the final dataclass using the collected fields.
        model = make_dataclass(
            name,
            fields=fields,
            bases=(BaseDataClassModel,), # Inherit from our custom base class
            namespace={'build': BaseDataClassModel.build}, # Add the build() method
            frozen=False # The models should be mutable
        )

        # Step 8: Cache the newly created model before returning it.
        self._models[name] = model
        return model

    def _map_type(self, prop_details: Dict[str, Any]) -> Tuple[Type, Any]:
        """
        Maps an OpenAPI schema property type to a Python type and a default value.

        This helper function is responsible for the translation between the JSON
        schema's type system and Python's type system.

        Args:
            prop_details: The schema dictionary for a single property.

        Returns:
            A tuple containing the corresponding Python type and a default value.
        """
        # Case 1: The property is a reference to another model or a primitive wrapper.
        if "$ref" in prop_details:
            ref_name = prop_details["$ref"].split("/")[-1]
            
            # If it's a wrapper type, return the primitive Python type directly.
            if ref_name == "StringValue": return Optional[str], None
            if ref_name == "DecimalValue": return Optional[float], None
            if ref_name == "BooleanValue": return Optional[bool], False
            if ref_name == "DateTimeValue": return Optional[datetime.datetime], None
            if ref_name == "GuidValue": return Optional[str], None
            if ref_name == "IntValue": return Optional[int], None
            if ref_name == "ShortValue": return Optional[int], None
            if ref_name == "LongValue": return Optional[int], None
            if ref_name == "ByteValue": return Optional[int], None
            if ref_name == "DoubleValue": return Optional[float], None

            # Otherwise, it's a reference to another complex model. Use a ForwardRef.
            # This prevents errors from circular dependencies where two models
            # reference each other. The actual type is resolved later.
            return Optional[ForwardRef(ref_name)], None

        # Case 2: The property is an array (a list in Python).
        if prop_details.get("type") == "array":
            # Recursively map the type of the items within the array.
            item_type, _ = self._map_type(prop_details.get("items", {}))
            return List[item_type], list

        # Fallback for any type that doesn't match the patterns above.
        return Optional[Any], None