# src/easy_acumatica/model_factory.py

from __future__ import annotations

import datetime
import logging
import textwrap
from dataclasses import Field, field, make_dataclass
from typing import Any, Dict, ForwardRef, List, Optional, Tuple, Type, get_type_hints

from .core import BaseDataClassModel

logger = logging.getLogger(__name__)


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

        # Annotations on dynamically-built dataclasses can reference
        # ``Optional`` / ``List`` / ``Dict`` / ``Any`` etc. - and because
        # this module uses ``from __future__ import annotations`` they're
        # stored as strings, so ``get_type_hints`` needs the ``typing``
        # symbols in its namespace to resolve them.
        import typing as _typing
        ns = {**vars(_typing), **self._models}

        # Iterate over a copy of the values to prevent RuntimeError
        for model in list(self._models.values()):
            try:
                resolved_annotations = get_type_hints(model, globalns=ns, localns=ns)
                model.__annotations__ = resolved_annotations
            except Exception as e:
                logger.warning(f"Could not resolve type hints for model {model.__name__}: {e}")

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

            # Unknown / unrenderable annotations fall back to ``Any`` so a
            # single odd field never crashes whole-schema introspection.
            unknown = {"type": "Any", "fields": {}}

            # Handle None type
            if field_type is type(None):
                return unknown

            # Get origin for generic types (List, Optional, etc.)
            origin = get_origin(field_type)

            # Handle Optional types - unwrap before checking ForwardRef
            if origin is Union:
                args = get_args(field_type)
                # Filter out NoneType
                non_none_args = [arg for arg in args if arg is not type(None)]
                if len(non_none_args) == 0:
                    return unknown
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
                    return unknown

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
                    return {"type": "List[Any]", "fields": {}}
                return {"type": "List[Any]", "fields": {}}

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

            # Handle typing.Any
            if field_type is Any or str(field_type) == 'typing.Any':
                return {"type": "Any", "fields": {}}

            # Handle primitive types
            if hasattr(field_type, '__name__'):
                type_name = field_type.__name__
                if type_name in ('str', 'int', 'float', 'bool', 'datetime'):
                    return {"type": type_name, "fields": {}}

            # Default for unknown types
            return unknown

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
            return ForwardRef(ref_name), None

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


# ---------------------------------------------------------------------------
# Custom-field discovery + augmentation
# ---------------------------------------------------------------------------
#
# After the OpenAPI schema is parsed into dataclasses we walk the per-service
# ``$adHocSchema`` response to discover custom-field metadata that doesn't
# appear in the OpenAPI surface. The walker yields tuples of
# ``(model_name, view_name, field_name, custom_type)``; the augmenter rebuilds
# the affected dataclasses with those fields included so users can set them
# via the constructor (``client.models.SalesOrder(AttributeColor=...)``)
# and the TUI's ``ModelBuilderScreen`` picks them up automatically.

_CUSTOM_TYPE_TO_PYTHON: Dict[str, Type] = {
    "CustomStringField": str,
    "CustomGuidField": str,
    "CustomIntField": int,
    "CustomShortField": int,
    "CustomLongField": int,
    "CustomByteField": int,
    "CustomDecimalField": float,
    "CustomDoubleField": float,
    "CustomBooleanField": bool,
    "CustomDateTimeField": datetime.datetime,
    "CustomDateField": datetime.datetime,
}


def _python_type_for_custom_field(custom_type: str) -> Type:
    return _CUSTOM_TYPE_TO_PYTHON.get(custom_type, Any)


def _resolve_dataclass_name(annotation: Any) -> Optional[str]:
    """Return the underlying dataclass name from an annotation.

    Handles ``Optional[Foo]``, ``List[Foo]``, ``ForwardRef("Foo")``, and
    bare classes. Returns ``None`` for primitives or anything we can't
    map to a dataclass.
    """
    from typing import get_args, get_origin, Union
    from dataclasses import is_dataclass

    if isinstance(annotation, ForwardRef):
        return annotation.__forward_arg__.strip("'\"")

    origin = get_origin(annotation)
    if origin is Union:
        non_none = [a for a in get_args(annotation) if a is not type(None)]
        if len(non_none) == 1:
            return _resolve_dataclass_name(non_none[0])
        return None

    if origin is list:
        args = get_args(annotation)
        if args:
            return _resolve_dataclass_name(args[0])
        return None

    if isinstance(annotation, type) and is_dataclass(annotation):
        return annotation.__name__

    return None


def walk_custom_fields(
    ad_hoc_schema: Dict[str, Any],
    model_classes: Dict[str, Type],
    entity_name: str,
) -> List[Tuple[str, str, str, str]]:
    """Walk an ``$adHocSchema`` response and yield custom-field tuples.

    Each tuple is ``(target_model_name, view_name, field_name,
    custom_type)``. Nested entities are followed via the OpenAPI-derived
    annotations on the model classes, so a custom block on
    ``Details[0].custom.Transactions`` correctly attaches to the
    ``SalesOrderDetail`` model rather than ``SalesOrder``.
    """
    results: List[Tuple[str, str, str, str]] = []

    def visit(node: Any, current_model_name: str) -> None:
        if not isinstance(node, dict):
            return

        custom = node.get("custom")
        if isinstance(custom, dict):
            for view_name, view_fields in custom.items():
                if not isinstance(view_fields, dict):
                    continue
                for field_name, meta in view_fields.items():
                    if isinstance(meta, dict) and "type" in meta:
                        results.append((
                            current_model_name,
                            view_name,
                            field_name,
                            meta["type"],
                        ))

        model = model_classes.get(current_model_name)
        if model is None:
            return
        annotations = getattr(model, "__annotations__", {}) or {}

        for key, value in node.items():
            if key == "custom":
                continue
            ann = annotations.get(key)
            if ann is None:
                continue
            child_name = _resolve_dataclass_name(ann)
            if child_name is None:
                continue

            if isinstance(value, list):
                for item in value:
                    visit(item, child_name)
            elif isinstance(value, dict):
                visit(value, child_name)

    visit(ad_hoc_schema, entity_name)
    return results


def augment_model_with_custom_fields(
    model_class: Type,
    custom_fields: List[Tuple[str, str, str]],
) -> Type:
    """Return a new dataclass that adds custom fields to ``model_class``.

    Each entry is ``(view, field_name, custom_type)``. The new dataclass
    keeps every original field and metadata, plus typed Optional fields
    for each custom entry, and exposes ``__custom_field_meta__`` so
    ``BaseDataClassModel.to_acumatica_payload`` knows how to route them.
    """
    from dataclasses import MISSING, fields as dc_fields, make_dataclass

    if not custom_fields:
        return model_class

    base_fields: List[Tuple[str, Any, Any]] = []
    for f in dc_fields(model_class):
        if f.default is not MISSING:
            base_fields.append((f.name, f.type, field(default=f.default)))
        elif f.default_factory is not MISSING:
            base_fields.append((f.name, f.type, field(default_factory=f.default_factory)))
        else:
            base_fields.append((f.name, f.type, field()))

    # De-duplicate by field name (later discovery may revisit the same view).
    seen_names = {f.name for f in dc_fields(model_class)}
    new_meta = dict(getattr(model_class, "__custom_field_meta__", {}) or {})
    new_field_specs: List[Tuple[str, Any, Any]] = []

    for view, fname, ctype in custom_fields:
        if fname in seen_names:
            # Already a field on this model - don't shadow it. Custom-field
            # metadata still wins so it serializes to the custom block.
            new_meta[fname] = (view, ctype)
            continue
        # Acumatica exposes related-field expansions like
        # ``ResponseActivityNoteID!subject`` in the $adHocSchema custom
        # blocks. Those aren't valid Python identifiers (``!``) so they
        # can't become dataclass fields. Skip them - the user can still
        # set them through ``model.set_custom(view, fname, value)`` if
        # ever needed, since that path doesn't go through the dataclass.
        if not fname.isidentifier():
            continue
        py_type = _python_type_for_custom_field(ctype)
        new_field_specs.append((fname, Optional[py_type], field(default=None)))
        new_meta[fname] = (view, ctype)
        seen_names.add(fname)

    namespace = {
        k: v for k, v in model_class.__dict__.items()
        if k not in (
            "__dict__", "__weakref__", "__dataclass_fields__",
            "__dataclass_params__", "__init__", "__repr__", "__eq__",
            "__hash__", "__match_args__",
        )
    }
    namespace["__custom_field_meta__"] = new_meta

    new_cls = make_dataclass(
        model_class.__name__,
        fields=base_fields + new_field_specs,
        bases=model_class.__bases__,
        namespace=namespace,
        frozen=False,
    )
    new_cls.__module__ = model_class.__module__
    new_cls.__doc__ = model_class.__doc__
    return new_cls


def apply_custom_field_discoveries(
    model_classes: Dict[str, Type],
    discoveries: List[Tuple[str, str, str, str]],
) -> Dict[str, Type]:
    """Apply a flat list of discoveries to a model registry, in place.

    Groups by model name, augments each affected class once, replaces the
    class in ``model_classes``. Callers should invoke
    :func:`re_link_dataclass_annotations` afterwards so parent classes
    pick up the augmented child classes via their nested annotations.
    """
    by_model: Dict[str, List[Tuple[str, str, str]]] = {}
    for model_name, view, fname, ctype in discoveries:
        by_model.setdefault(model_name, []).append((view, fname, ctype))

    for model_name, entries in by_model.items():
        if model_name not in model_classes:
            continue
        new_cls = augment_model_with_custom_fields(model_classes[model_name], entries)
        model_classes[model_name] = new_cls

    return model_classes


def _substitute_dataclass_refs(annotation: Any, registry: Dict[str, Type]) -> Any:
    """Walk a typing annotation, replace any embedded dataclass classes
    with the current registry entry for that dataclass name.

    Used after :func:`apply_custom_field_discoveries` has replaced classes
    in the registry: parent classes' resolved annotations still reference
    the *old* class objects, so the new (augmented) child wouldn't be
    used during construction or serialization without this fix-up.
    """
    from dataclasses import is_dataclass
    from typing import Union, get_args, get_origin

    origin = get_origin(annotation)

    if origin is Union:
        args = tuple(_substitute_dataclass_refs(a, registry) for a in get_args(annotation))
        return Union[args]

    if origin is list:
        args = get_args(annotation)
        if args:
            return List[_substitute_dataclass_refs(args[0], registry)]
        return list

    if isinstance(annotation, type) and is_dataclass(annotation):
        return registry.get(annotation.__name__, annotation)

    return annotation


def re_link_dataclass_annotations(model_classes: Dict[str, Type]) -> None:
    """Re-link nested dataclass references to the current registry version.

    After ``apply_custom_field_discoveries`` swaps out a child class
    (e.g. ``SalesOrderDetail``) for an augmented copy, the parent's
    already-resolved annotation still points at the *old* class object.
    This walker rewrites every class's ``__annotations__`` so each
    dataclass reference resolves to ``model_classes[name]``.
    """
    for cls in list(model_classes.values()):
        annotations = getattr(cls, "__annotations__", None)
        if not annotations:
            continue
        cls.__annotations__ = {
            fname: _substitute_dataclass_refs(ann, model_classes)
            for fname, ann in annotations.items()
        }
