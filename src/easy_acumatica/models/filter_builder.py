"""
easy_acumatica.models.filters
=============================

Fluent helpers that turn Python objects into **OData-v3** query strings.
Developers can compose complex ``$filter`` expressions and other query
options without worrying about URL encoding, operator precedence, or the
specific syntax of OData math, date, and string functions.

This module provides:
  - ``Filter``: build logical and comparison filters
  - ``MathBuilder``: construct arithmetic expressions
  - ``DateBuilder``: extract date/time parts
  - ``StringBuilder``: manipulate string values
  - ``QueryOptions``: aggregate and serialize all query options
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any

__all__ = [
    "Filter",
    "QueryOptions",
    "MathBuilder",
    "DateBuilder",
    "StringBuilder",
]


# ---------------------------------------------------------------------------
# Filter class – build $filter clauses
# ---------------------------------------------------------------------------
class Filter:
    """
    Represent a single OData $filter clause or a composition thereof.

    Immutable: each predicate returns a new Filter instance, so you can
    chain without side-effects.
    """

    def __init__(self, expr: str = "") -> None:
        """
        Initialize with a raw OData expression fragment (no URL-encoding).
        """
        self.expr = expr

    @staticmethod
    def raw(expr: str) -> "Filter":
        """
        Treat `expr` as already-quoted or literal OData syntax.
        """
        return Filter(expr)

    @staticmethod
    def _lit(value: Any) -> str:
        """
        Quote Python values into OData literals:
        - strings are wrapped in single-quotes and escaped
        - numeric types are rendered without quotes
        - known OData literal prefixes (datetimeoffset, guid, cf.) pass through
        """
        if isinstance(value, str):
            if value.startswith(("datetimeoffset", "guid", "cf.")):
                return value
            return f"'{value.replace("'", "''")}'"
        return str(value)

    @staticmethod
    def cf(type_name: str, view_name: str, field_name: str) -> str:
        """
        Build a custom-field reference: cf.TypeName(f='ViewName.FieldName').
        """
        return f"cf.{type_name}(f='{view_name}.{field_name}')"

    def eq(
        self,
        left: Union[str, MathBuilder, DateBuilder, StringBuilder],
        right: Union[Any, MathBuilder, DateBuilder, StringBuilder],
    ) -> "Filter":
        """left **equals** right (unwraps any builder)."""
        left_expr = left.expr if hasattr(left, "expr") else left
        right_expr = right.expr if hasattr(right, "expr") else self._lit(right)
        return Filter(f"{left_expr} eq {right_expr}")

    def gt(
        self,
        left: Union[str, MathBuilder, DateBuilder, StringBuilder],
        right: Union[Any, MathBuilder, DateBuilder, StringBuilder],
    ) -> "Filter":
        """left **greater-than** right (unwraps any builder)."""
        left_expr = left.expr if hasattr(left, "expr") else left
        right_expr = right.expr if hasattr(right, "expr") else self._lit(right)
        return Filter(f"{left_expr} gt {right_expr}")

    def ge(
        self,
        left: Union[str, MathBuilder, DateBuilder, StringBuilder],
        right: Union[Any, MathBuilder, DateBuilder, StringBuilder],
    ) -> "Filter":
        """left **greater-than or equal-to** right (unwraps any builder)."""
        left_expr = left.expr if hasattr(left, "expr") else left
        right_expr = right.expr if hasattr(right, "expr") else self._lit(right)
        return Filter(f"{left_expr} ge {right_expr}")

    def lt(
        self,
        left: Union[str, MathBuilder, DateBuilder, StringBuilder],
        right: Union[Any, MathBuilder, DateBuilder, StringBuilder],
    ) -> "Filter":
        """left **less-than** right (unwraps any builder)."""
        left_expr = left.expr if hasattr(left, "expr") else left
        right_expr = right.expr if hasattr(right, "expr") else self._lit(right)
        return Filter(f"{left_expr} lt {right_expr}")

    def le(
        self,
        left: Union[str, MathBuilder, DateBuilder, StringBuilder],
        right: Union[Any, MathBuilder, DateBuilder, StringBuilder],
    ) -> "Filter":
        """left **less-than or equal-to** right (unwraps any builder)."""
        left_expr = left.expr if hasattr(left, "expr") else left
        right_expr = right.expr if hasattr(right, "expr") else self._lit(right)
        return Filter(f"{left_expr} le {right_expr}")

    def contains(self, field: str, substring: Union[str, StringBuilder]) -> "Filter":
        """
        substringof helper. If you pass a StringBuilder, it will be
        embedded verbatim; if you pass any other str that looks like
        an expression (contains '(' and ')'), it will be wrapped as a
        raw literal; otherwise it'll be properly escaped.
        """
        # builder instance?
        if hasattr(substring, "expr"):
            return Filter(f"substringof({substring.expr},{field})")
        # raw-looking expression? treat as literal but don't escape inner quotes
        if "(" in substring and ")" in substring:
            return Filter(f"substringof('{substring}',{field})")
        # simple literal: escape quotes
        esc = substring.replace("'", "''")
        return Filter(f"substringof('{esc}',{field})")

    def starts_with(self, field: str, prefix: Union[str, StringBuilder]) -> "Filter":
        """OData startswith; unwraps StringBuilder if given."""
        if hasattr(prefix, "expr"):
            return Filter(f"startswith({field},{prefix.expr})")
        esc = prefix.replace("'", "''")
        return Filter(f"startswith({field},'{esc}')")

    def ends_with(self, field: str, suffix: Union[str, StringBuilder]) -> "Filter":
        """OData endswith; unwraps StringBuilder if given."""
        if hasattr(suffix, "expr"):
            return Filter(f"endswith({field},{suffix.expr})")
        esc = suffix.replace("'", "''")
        return Filter(f"endswith({field},'{esc}')")
    def and_(self, other: "Filter") -> "Filter":
        """Logical **AND** of two filter fragments."""
        return Filter(f"({self.expr} and {other.expr})")

    def or_(self, other: "Filter") -> "Filter":
        """Logical **OR** of two filter fragments."""
        return Filter(f"({self.expr} or {other.expr})")

    def not_(self, other: "Filter") -> "Filter":
        """Logical **NOT** of a filter fragment."""
        return Filter(f"not ({other.expr})")

    def build(self) -> str:
        """Return the raw expression string (no URL-encoding)."""
        return self.expr


# ---------------------------------------------------------------------------
# QueryOptions – bundle all OData query parameters
# ---------------------------------------------------------------------------
class QueryOptions:
    """
    Combine $filter, $expand, $select, $top, $skip, and $custom into
    a single object and serialize to a dict for requests.
    """

    def __init__(
        self,
        filter: Union[str, Filter, None] = None,
        expand: Optional[List[str]] = None,
        select: Optional[List[str]] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        custom: Optional[List[str]] = None,
    ) -> None:
        self.filter = filter
        self.expand = expand
        self.select = select
        self.top = top
        self.skip = skip
        self.custom = custom

    def to_params(self) -> Dict[str, str]:
        """Serialize to a dict ready for requests.get(..., params=...)."""
        params: Dict[str, str] = {}
        if self.filter:
            params["$filter"] = (
                self.filter.build() if isinstance(self.filter, Filter) else str(self.filter)
            )
        if self.expand:
            params["$expand"] = ",".join(self.expand)
        if self.select:
            params["$select"] = ",".join(self.select)
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)
        if self.custom:
            params["$custom"] = ",".join(self.custom)
        return params


# ---------------------------------------------------------------------------
# MathBuilder – construct arithmetic expressions
# ---------------------------------------------------------------------------
class MathBuilder:
    """
    Build OData arithmetic: add, sub, mul, div, mod, and rounding functions.

    Example:
        expr = MathBuilder.field("Price").add(5).mul(2)
        # yields "(Price add 5) mul 2"
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    @classmethod
    def field(cls, name: str) -> "MathBuilder":
        """Start from a field name."""
        return cls(name)

    @classmethod
    def raw(cls, expr: str) -> "MathBuilder":
        """Use a raw OData expression snippet."""
        return cls(expr)

    def add(self, other: Union[MathBuilder, int, float, str]) -> "MathBuilder":
        """Add two operands."""
        rhs = other.expr if isinstance(other, MathBuilder) else str(other)
        return MathBuilder(f"({self.expr} add {rhs})")

    def sub(self, other: Union[MathBuilder, int, float, str]) -> "MathBuilder":
        """Subtract two operands."""
        rhs = other.expr if isinstance(other, MathBuilder) else str(other)
        return MathBuilder(f"({self.expr} sub {rhs})")

    def mul(self, other: Union[MathBuilder, int, float, str]) -> "MathBuilder":
        """Multiply two operands."""
        rhs = other.expr if isinstance(other, MathBuilder) else str(other)
        return MathBuilder(f"({self.expr} mul {rhs})")

    def div(self, other: Union[MathBuilder, int, float, str]) -> "MathBuilder":
        """Divide two operands."""
        rhs = other.expr if isinstance(other, MathBuilder) else str(other)
        return MathBuilder(f"({self.expr} div {rhs})")

    def mod(self, other: Union[MathBuilder, int, float, str]) -> "MathBuilder":
        """Modulo operation."""
        rhs = other.expr if isinstance(other, MathBuilder) else str(other)
        return MathBuilder(f"({self.expr} mod {rhs})")

    def round(self) -> "MathBuilder":
        """Round to nearest integer."""
        return MathBuilder(f"round({self.expr})")

    def floor(self) -> "MathBuilder":
        """Floor function."""
        return MathBuilder(f"floor({self.expr})")

    def ceiling(self) -> "MathBuilder":
        """Ceiling function."""
        return MathBuilder(f"ceiling({self.expr})")

    def __str__(self) -> str:
        return self.expr

    __repr__ = __str__


# ---------------------------------------------------------------------------
# DateBuilder – extract date/time parts
# ---------------------------------------------------------------------------
class DateBuilder:
    """Builds an OData date expression, e.g. day(BirthDate)."""

    @staticmethod
    def day(field: str) -> str:
        return f"day({field})"

    @staticmethod
    def hour(field: str) -> str:
        return f"hour({field})"

    @staticmethod
    def minute(field: str) -> str:
        return f"minute({field})"

    @staticmethod
    def month(field: str) -> str:
        return f"month({field})"

    @staticmethod
    def second(field: str) -> str:
        return f"second({field})"

    @staticmethod
    def year(field: str) -> str:
        return f"year({field})"


# ---------------------------------------------------------------------------
# StringBuilder – string transformations
# ---------------------------------------------------------------------------
class StringBuilder:
    """
    Build OData string functions: length, indexof, replace, substring,
    tolower, toupper, trim, concat.

    Example:
        StringBuilder.field("Name").substring(1,2).toupper()
    """

    def __init__(self, expr: str) -> None:
        self.expr = expr

    @classmethod
    def raw(cls, expr: str) -> "StringBuilder":
        """Use a raw field or expression."""
        return cls(expr)

    @classmethod
    def field(cls, field_name: str) -> "StringBuilder":
        """Start from a bare field name."""
        return cls(field_name)

    def length(self) -> "StringBuilder":
        """Get string length."""
        return StringBuilder(f"length({self.expr})")

    def indexof(self, what: Union[str, StringBuilder]) -> "StringBuilder":
        """Find substring position."""
        arg = what.expr if isinstance(what, StringBuilder) else f"'{what.replace("'","''")}'"
        return StringBuilder(f"indexof({self.expr},{arg})")

    def replace(
        self,
        old: Union[str, StringBuilder],
        new: Union[str, StringBuilder]
    ) -> "StringBuilder":
        """Replace occurrences of old with new."""
        def lit(val):
            return val.expr if isinstance(val, StringBuilder) else f"'{val.replace("'","''")}'"
        return StringBuilder(f"replace({self.expr},{lit(old)},{lit(new)})")

    def substring(
        self,
        pos: Union[int, StringBuilder],
        length: Optional[Union[int, StringBuilder]] = None
    ) -> "StringBuilder":
        """Extract substring at pos, optional length."""
        def fmt(x): return x.expr if isinstance(x, StringBuilder) else str(x)
        if length is None:
            return StringBuilder(f"substring({self.expr},{fmt(pos)})")
        return StringBuilder(f"substring({self.expr},{fmt(pos)},{fmt(length)})")

    def tolower(self) -> "StringBuilder":
        """Convert to lowercase."""
        return StringBuilder(f"tolower({self.expr})")

    def toupper(self) -> "StringBuilder":
        """Convert to uppercase."""
        return StringBuilder(f"toupper({self.expr})")

    def trim(self) -> "StringBuilder":
        """Trim whitespace."""
        return StringBuilder(f"trim({self.expr})")

    def concat(self, other: Union[str, StringBuilder]) -> "StringBuilder":
        """Concatenate two strings."""
        arg = other.expr if isinstance(other, StringBuilder) else f"'{other.replace("'","''")}'"
        return StringBuilder(f"concat({self.expr},{arg})")

    def __str__(self) -> str:
        return self.expr

    __repr__ = __str__
