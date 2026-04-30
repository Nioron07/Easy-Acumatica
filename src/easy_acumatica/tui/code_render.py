"""Pure helpers for rendering Python code that reproduces a TUI debug call.

Used by the ServiceCallScreen to show developers the equivalent
``easy_acumatica`` call so they can copy it into a script.

No Textual imports — keep this module unit-testable in isolation.
"""
from __future__ import annotations

import re
from dataclasses import fields, is_dataclass
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_args, get_origin

from ..core import BaseDataClassModel
from ..odata import Filter, QueryOptions


# --- Field classification (for the model builder UI) ---------------------


def _is_model_subclass(cls: Any) -> bool:
    """True if cls is a BaseDataClassModel subclass."""
    return isinstance(cls, type) and issubclass(cls, BaseDataClassModel)


def classify_field(annotation: Any) -> Dict[str, Any]:
    """
    Resolve a field annotation to one of four kinds:

    - ``primitive``   - ``int``, ``str``, ``bool``, ``float``, ``datetime``, etc.
    - ``model``       - subclass of ``BaseDataClassModel``
    - ``list-model``  - ``List[Model]`` or ``List[Optional[Model]]``
    - ``list-primitive`` - ``List[primitive]``

    Returned dict shape:
        ``{'kind': str, 'optional': bool, ...kind-specific keys}``

    Kind-specific keys:
        - primitive:   ``{'type': <Python type or Any>}``
        - model:       ``{'model': <model class>}``
        - list-model:  ``{'model': <inner model class>}``
        - list-primitive: ``{'item': <Python type or Any>}``
    """
    is_optional = False
    inner = annotation

    # Strip Optional / Union[..., None]
    if get_origin(inner) is Union:
        non_none = [a for a in get_args(inner) if a is not type(None)]
        if len(non_none) != len(get_args(inner)):
            is_optional = True
        if len(non_none) == 1:
            inner = non_none[0]
        elif len(non_none) > 1:
            # Genuine Union of multiple non-None types — treat as primitive Any
            return {'kind': 'primitive', 'type': Any, 'optional': is_optional}

    # Detect List[...]
    inner_origin = get_origin(inner)
    if inner_origin in (list, List):
        item_args = get_args(inner)
        item_type: Any = item_args[0] if item_args else Any

        # Item itself may be Optional[Model]
        if get_origin(item_type) is Union:
            item_non_none = [a for a in get_args(item_type) if a is not type(None)]
            if len(item_non_none) == 1:
                item_type = item_non_none[0]

        if _is_model_subclass(item_type):
            return {'kind': 'list-model', 'model': item_type, 'optional': is_optional}
        return {'kind': 'list-primitive', 'item': item_type, 'optional': is_optional}

    if _is_model_subclass(inner):
        return {'kind': 'model', 'model': inner, 'optional': is_optional}

    return {'kind': 'primitive', 'type': inner, 'optional': is_optional}


# --- Variable naming ------------------------------------------------------


def _camel_to_snake(name: str) -> str:
    """`ShipToAddress` -> `ship_to_address`. Strips leading underscores
    so private/internal class names produce sensible variable names."""
    name = name.lstrip('_')
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', name)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


class _VarNamer:
    """Deduplicating variable-name picker for nested model construction."""

    def __init__(self) -> None:
        self._used: Set[str] = set()

    def pick(self, hint: str) -> str:
        base = _camel_to_snake(hint or 'item')
        if not base:
            base = 'item'
        if base not in self._used:
            self._used.add(base)
            return base
        i = 2
        while f"{base}_{i}" in self._used:
            i += 1
        unique = f"{base}_{i}"
        self._used.add(unique)
        return unique


# --- Model rendering ------------------------------------------------------


def _format_ctor(cls_name: str, kwargs: List[str]) -> str:
    """Pretty-print a constructor call. Single line when short enough."""
    if not kwargs:
        return f"{cls_name}()"
    one_line = f"{cls_name}({', '.join(kwargs)})"
    if len(one_line) <= 80:
        return one_line
    return f"{cls_name}(\n    " + ',\n    '.join(kwargs) + ',\n)'


def _emit_value(
    value: Any,
    *,
    hint: str,
    lines: List[str],
    imports: Set[str],
    namer: _VarNamer,
) -> str:
    """
    Emit code to materialize ``value``.

    Returns the Python expression that refers to it - a variable name for
    nested models (after appending an assignment to ``lines``), or a literal
    for primitives.
    """
    if value is None:
        return "None"
    if isinstance(value, BaseDataClassModel):
        cls_name = type(value).__name__
        imports.add(cls_name)
        kwargs: List[str] = []
        for f in fields(value):
            v = getattr(value, f.name)
            if v is None:
                continue
            child_expr = _emit_value(
                v, hint=f.name, lines=lines, imports=imports, namer=namer,
            )
            kwargs.append(f"{f.name}={child_expr}")
        ctor = _format_ctor(cls_name, kwargs)
        var = namer.pick(hint)
        lines.append(f"{var} = {ctor}")
        return var
    if isinstance(value, list):
        items = [
            _emit_value(it, hint=hint, lines=lines, imports=imports, namer=namer)
            for it in value
        ]
        return f"[{', '.join(items)}]"
    return repr(value)


def render_model(model: BaseDataClassModel) -> Tuple[List[str], Set[str], str]:
    """
    Render Python code that constructs ``model``.

    Returns:
        (lines, imports, top_var) where ``lines`` are sequential
        ``<var> = <Ctor>(...)`` statements (nested models first, top
        model last), ``imports`` is the set of model class names that
        need to be imported from ``easy_acumatica.models``, and
        ``top_var`` is the variable name the top-level model is bound to.
    """
    namer = _VarNamer()
    lines: List[str] = []
    imports: Set[str] = set()
    top_var = _emit_value(
        model,
        hint=type(model).__name__,
        lines=lines,
        imports=imports,
        namer=namer,
    )
    return lines, imports, top_var


# --- QueryOptions rendering ----------------------------------------------


def _render_query_options(opts: QueryOptions) -> str:
    parts: List[str] = []
    for attr in ('top', 'skip'):
        val = getattr(opts, attr)
        if val is not None:
            parts.append(f"{attr}={val!r}")
    for attr in ('select', 'expand'):
        val = getattr(opts, attr)
        if val:
            parts.append(f"{attr}={val!r}")
    if opts.orderby:
        parts.append(f"orderby={opts.orderby!r}")
    if opts.filter is not None:
        # Filter objects: render their OData string form. Raw strings: repr
        # as-is. Either way, the resulting Python is a valid filter input.
        if isinstance(opts.filter, Filter):
            parts.append(f"filter={str(opts.filter)!r}")
        else:
            parts.append(f"filter={opts.filter!r}")
    return f"QueryOptions({', '.join(parts)})"


# --- Top-level: render a full call snippet -------------------------------


def render_call(
    client_attr: str,
    method_name: str,
    *,
    positional: Optional[List[Any]] = None,
    keyword: Optional[Dict[str, Any]] = None,
    entity_model: Optional[BaseDataClassModel] = None,
) -> str:
    """
    Produce a self-contained Python snippet that reproduces the call.

    ``positional`` and ``keyword`` are the runtime values that would be
    passed to the service method. ``entity_model``, when set, is a model
    instance to construct and pass as the first positional arg (used for
    ``put_entity``).

    The output starts with imports, defines ``client = AcumaticaClient()``,
    builds any nested models, and ends with the actual call line.
    """
    positional = list(positional or [])
    keyword = dict(keyword or {})

    imports: List[str] = ["from easy_acumatica import AcumaticaClient"]
    needs_odata = any(isinstance(v, QueryOptions) for v in keyword.values())
    if needs_odata:
        imports.append("from easy_acumatica.odata import F, QueryOptions")

    helper_lines: List[str] = []
    model_imports: Set[str] = set()
    top_arg_expr: Optional[str] = None
    if entity_model is not None:
        helper_lines, model_imports, top_arg_expr = render_model(entity_model)
        if model_imports:
            imports.append(
                f"from easy_acumatica.models import "
                f"{', '.join(sorted(model_imports))}"
            )

    # Build call argument list
    arg_parts: List[str] = []
    if top_arg_expr is not None:
        arg_parts.append(top_arg_expr)
    for p in positional:
        arg_parts.append(repr(p))
    for k, v in keyword.items():
        if v is None:
            continue
        if isinstance(v, QueryOptions):
            arg_parts.append(f"{k}={_render_query_options(v)}")
        elif isinstance(v, BaseDataClassModel):
            # Inline nested model in a kwarg (rare path)
            sub_lines, sub_imports, sub_var = render_model(v)
            helper_lines.extend(sub_lines)
            model_imports.update(sub_imports)
            arg_parts.append(f"{k}={sub_var}")
        else:
            arg_parts.append(f"{k}={v!r}")

    call_line = f"client.{client_attr}.{method_name}({', '.join(arg_parts)})"

    out: List[str] = []
    out.extend(imports)
    out.append("")
    out.append("client = AcumaticaClient()")
    if helper_lines:
        out.append("")
        out.extend(helper_lines)
    out.append("")
    out.append(call_line)

    return "\n".join(out)
