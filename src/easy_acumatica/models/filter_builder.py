"""easy_acumatica.models.filters
=======================

Fluent helpers that turn Python objects into **OData-v3** query strings.
Developers can compose complex ``$filter`` expressions and other query
options without worrying about URL encoding or operator precedence.

Quick start
-----------
>>> from easy_acumatica.filters import Filter, QueryOptions
>>> flt = (
...     Filter()
...     .eq("ContactID", 102210)
...     .and_(Filter().contains("DisplayName", "Brian"))
... )
>>> opts = QueryOptions(
...     filter=flt,
...     top=5,
...     select=["ContactID", "DisplayName"],
...     custom=["ItemSettings.UsrRepairItemType"]
... )
>>> opts.to_params()
{'$filter': "ContactID eq 102210 and substringof('Brian',DisplayName)",
 '$select': 'ContactID,DisplayName',
 '$top': '5',
 '$custom': 'ItemSettings.UsrRepairItemType'}
"""
from __future__ import annotations

from typing import List, Optional, Union, Dict, Any

__all__ = ["Filter", "QueryOptions"]


# ---------------------------------------------------------------------------
# Filter helper – fluent construction of $filter strings
# ---------------------------------------------------------------------------
class Filter:
    """Represent a **single** OData filter clause or a composition thereof.

    The class is *immutable*: every predicate method returns **a brand-new
    instance**, allowing easy chaining without side-effects.
    """

    def __init__(self, expr: str = "") -> None:
        self.expr = expr  # raw OData expression snippet (no URL-encoding yet)

    @staticmethod
    def _lit(value: Any) -> str:
        """Quote and escape Python literals for OData.

        Strings are wrapped in single quotes and internal quotes doubled
        per the OData grammar.  Other types are coerced with :pyfunc:`str`.
        """
        if isinstance(value, str):
            return "'" + value.replace("'", "''") + "'"
        return str(value)

    @staticmethod
    def cf(type_name: str, view_name: str, field_name: str) -> str:
        """Build an OData custom-field reference string.

        Args:
            type_name: Name of the custom function (e.g., 'Decimal', 'DateTime').
            view_name: Name of the data view containing the field (e.g., 'Document' or 'Details/Transactions').
            field_name: Internal name of the custom field (e.g., 'UsrRepairItemType').

        Returns:
            A string like "cf.<TypeName>(f='<ViewName>.<FieldName>')".

        Examples:
            >>> Filter.cf("Decimal", "Document", "CuryBalanceWOTotal")
            "cf.Decimal(f='Document.CuryBalanceWOTotal')"

            # As part of a compound filter:
            >>> amount_cf = Filter.cf("Decimal", "Document", "CuryBalanceWOTotal")
            >>> date_cf = Filter.cf("DateTime", "Document", "DiscDate")
            >>> flt = (
...                 Filter()
...                 .eq(amount_cf, "0M")
...                 .and_(
...                     Filter().gt(
...                         date_cf,
...                         "datetimeoffset'2024-02-18T23:59:59.999+04:00'"
...                     )
...                 )
...             )
        """
        return f"cf.{type_name}(f='{view_name}.{field_name}')"

    def eq(self, field: str, value: Any) -> "Filter":
        """Field **equals** value."""
        return Filter(f"{field} eq {self._lit(value)}")

    def gt(self, field: str, value: Any) -> "Filter":
        """Field **greater-than** value."""
        return Filter(f"{field} gt {self._lit(value)}")

    def lt(self, field: str, value: Any) -> "Filter":
        """Field **less-than** value."""
        return Filter(f"{field} lt {self._lit(value)}")

    def contains(self, field: str, substring: str) -> "Filter":
        """String containment using the v3 helper ``substringof``.

        Parameters
        ----------
        field : str
            Name of the OData property on the server side.
        substring : str
            The text to search *for*.
        """
        esc = substring.replace("'", "''")
        return Filter(f"substringof('{esc}',{field})")

    def and_(self, other: "Filter") -> "Filter":
        """Logical **AND** of two filter fragments."""
        return Filter(f"{self.expr} and {other.expr}")

    def or_(self, other: "Filter") -> "Filter":
        """Logical **OR** of two filter fragments."""
        return Filter(f"{self.expr} or {other.expr}")

    def build(self) -> str:
        """Return the raw expression string (no URL-encoding)."""
        return self.expr


# ---------------------------------------------------------------------------
# QueryOptions – aggregate $filter, $expand, $select, $top, $skip, $custom
# ---------------------------------------------------------------------------
class QueryOptions:
    """Bundle all common OData query options into a single object, including custom fields."""

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
        """Convert stored options to a **requests-ready** ``dict``.

        The result can be passed directly to ``requests.get(..., params=...)``.
        Values are *not* URL-encoded; :pymod:`requests` will handle that.
        """
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
