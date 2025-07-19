# src/easy_acumatica/models/odata.py
"""
easy_acumatica.models.filter_builder
====================================

A Pythonic, fluent DSL for creating OData v3 filter queries using a
factory object and operator overloading.

This module provides:
  - ``F``: A factory object to create field Filters (e.g., `F.Price`).
  - ``Filter``: An object representing an OData Filter that
    overloads Python operators.

Example:
--------
>>> from easy_acumatica.models.filter_builder import F, QueryOptions
>>> # Build filter: (Price sub 5) gt 10 and startswith(tolower(Name), 'a')
>>> f = ((F.Price - 5) > 10) & F.Name.tolower().startswith('a')
>>>
>>> opts = QueryOptions(filter=f, top=10)
>>> print(opts.to_params()['$filter'])
(((Price sub 5) gt 10) and startswith(tolower(Name),'a'))
"""
from __future__ import annotations
from typing import Optional, Any, List, Union, Dict

__all__ = ["F", "Filter", "QueryOptions"]


class Filter:
    """
    Represents an OData filter expression with overloaded operators for fluent building.

    Instances of this class are typically created via the `F` factory object,
    which allows for a highly readable, declarative syntax for building queries.
    All operator overloads and methods return a new `Filter` instance, allowing
    for safe, immutable chaining of operations.
    """

    def __init__(self, expr: str):
        """Initializes the Filter with a string fragment."""
        self.expr = expr

    def __getattr__(self, name: str) -> "Filter":
        """
        Handles nested attribute access for linked entities.

        This allows for creating expressions like `F.MainContact.Email`,
        which translates to the OData path 'MainContact/Email'.
        """
        # Append the new attribute with a '/' for OData path navigation
        new_expr = f"{self.expr}/{name}"
        return Filter(new_expr)
    
    # --- Private Helpers ---
    @staticmethod
    def _to_literal(value: Any) -> str:
        """
        Converts a Python value to its OData literal string representation.

        - Strings are enclosed in single quotes, with internal quotes escaped.
        - Booleans are converted to 'true' or 'false'.
        - None is converted to 'null'.
        - Filter objects have their expression string extracted.
        - Other types are converted directly to strings.
        """
        if isinstance(value, Filter):
            return value.expr
        if isinstance(value, str):
            # Escape single quotes for OData compliance
            return f"'{value.replace('\'', '\'\'')}"
        if isinstance(value, bool):
            return "true" if value else "false"
        if value is None:
            return "null"
        return str(value)

    def _binary_op(self, op: str, other: Any, right_to_left: bool = False) -> Filter:
        """
        Internal helper for creating infix binary operations (e.g., `a + b`, `x > y`).
        Handles right-hand-side operations for commutativity.
        """
        left = self._to_literal(other) if right_to_left else self.expr
        right = self.expr if right_to_left else self._to_literal(other)
        return Filter(f"({left} {op} {right})")

    def _function(self, func_name: str, *args: Any) -> Filter:
        """Internal helper for creating OData function call expressions."""
        all_args = [self.expr] + [self._to_literal(arg) for arg in args]
        return Filter(f"{func_name}({','.join(all_args)})")

    # --- Comparison Operators (e.g., F.Name == 'John') ---
    def __eq__(self, other: Any) -> Filter: return self._binary_op("eq", other)
    def __ne__(self, other: Any) -> Filter: return self._binary_op("ne", other)
    def __gt__(self, other: Any) -> Filter: return self._binary_op("gt", other)
    def __ge__(self, other: Any) -> Filter: return self._binary_op("ge", other)
    def __lt__(self, other: Any) -> Filter: return self._binary_op("lt", other)
    def __le__(self, other: Any) -> Filter: return self._binary_op("le", other)

    # --- Logical Operators (e.g., (F.A > 1) & (F.B < 2) ) ---
    # Note: These overload the bitwise operators &, |, and ~ for 'and', 'or', and 'not'.
    def __and__(self, other: Any) -> Filter: return self._binary_op("and", other)
    def __or__(self, other: Any) -> Filter: return self._binary_op("or", other)
    def __invert__(self) -> Filter: return Filter(f"not ({self.expr})")

    # --- Arithmetic Operators (e.g., F.Price * 1.1) ---
    # The 'r' versions (e.g., __radd__) handle cases where the Filter is on the right side.
    def __add__(self, other: Any) -> Filter: return self._binary_op("add", other)
    def __radd__(self, other: Any) -> Filter: return self._binary_op("add", other, True)
    def __sub__(self, other: Any) -> Filter: return self._binary_op("sub", other)
    def __rsub__(self, other: Any) -> Filter: return self._binary_op("sub", other, True)
    def __mul__(self, other: Any) -> Filter: return self._binary_op("mul", other)
    def __rmul__(self, other: Any) -> Filter: return self._binary_op("mul", other, True)
    def __truediv__(self, other: Any) -> Filter: return self._binary_op("div", other)
    def __rtruediv__(self, other: Any) -> Filter: return self._binary_op("div", other, True)
    def __mod__(self, other: Any) -> Filter: return self._binary_op("mod", other)
    def __rmod__(self, other: Any) -> Filter: return self._binary_op("mod", other, True)

    # --- OData Function Methods ---
    def contains(self, substring: Any) -> Filter:
        """Creates an OData `substringof(substring, field)` filter."""
        return Filter(f"substringof({self._to_literal(substring)}, {self.expr})")

    def endswith(self, suffix: Any) -> Filter:
        """Creates an OData `endswith(field, suffix)` filter."""
        return self._function("endswith", suffix)

    def startswith(self, prefix: Any) -> Filter:
        """Creates an OData `startswith(field, prefix)` filter."""
        return self._function("startswith", prefix)

    def length(self) -> Filter:
        """Creates an OData `length(field)` filter."""
        return Filter(f"length({self.expr})")

    def indexof(self, substring: Any) -> Filter:
        """Creates an OData `indexof(field, substring)` filter."""
        return self._function("indexof", substring)

    def replace(self, find: Any, replace_with: Any) -> Filter:
        """Creates an OData `replace(field, find, replace_with)` filter."""
        return self._function("replace", find, replace_with)

    def substring(self, pos: int, length: Optional[int] = None) -> Filter:
        """Creates an OData `substring(field, pos, length?)` filter."""
        return self._function("substring", pos) if length is None else self._function("substring", pos, length)

    def tolower(self) -> Filter:
        """Creates an OData `tolower(field)` filter."""
        return Filter(f"tolower({self.expr})")

    def toupper(self) -> Filter:
        """Creates an OData `toupper(field)` filter."""
        return Filter(f"toupper({self.expr})")

    def trim(self) -> Filter:
        """Creates an OData `trim(field)` filter."""
        return Filter(f"trim({self.expr})")

    def concat(self, other: Any) -> Filter:
        """Creates an OData `concat(field, other)` filter."""
        return self._function("concat", other)

    def day(self) -> Filter:
        """Creates an OData `day(date_field)` filter."""
        return Filter(f"day({self.expr})")

    def hour(self) -> Filter:
        """Creates an OData `hour(date_field)` filter."""
        return Filter(f"hour({self.expr})")

    def minute(self) -> Filter:
        """Creates an OData `minute(date_field)` filter."""
        return Filter(f"minute({self.expr})")

    def month(self) -> Filter:
        """Creates an OData `month(date_field)` filter."""
        return Filter(f"month({self.expr})")

    def second(self) -> Filter:
        """Creates an OData `second(date_field)` filter."""
        return Filter(f"second({self.expr})")

    def year(self) -> Filter:
        """Creates an OData `year(date_field)` filter."""
        return Filter(f"year({self.expr})")

    def round(self) -> Filter:
        """Creates an OData `round(numeric_field)` filter."""
        return Filter(f"round({self.expr})")

    def floor(self) -> Filter:
        """Creates an OData `floor(numeric_field)` filter."""
        return Filter(f"floor({self.expr})")

    def ceiling(self) -> Filter:
        """Creates an OData `ceiling(numeric_field)` filter."""
        return Filter(f"ceiling({self.expr})")

    def isof(self, type_name: Optional[str] = None) -> Filter:
        """Creates an OData `isof(type)` or `isof(field, type)` filter."""
        return self._function("isof", self._to_literal(type_name)) if type_name else Filter(f"isof({self.expr})")

    # --- Finalization ---
    def build(self) -> str:
        """Returns the final OData filter string, ready to be used in a query."""
        return self.expr

    def __str__(self) -> str:
        """Allows the Filter object to be cast directly to a string."""
        return self.build()

    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the Filter object."""
        return f"Filter('{self.expr}')"


class _FieldFactory:
    """
    Creates Filter objects for Acumatica field names via simple attribute access.

    This factory allows you to write `F.FieldName` instead of `Filter('FieldName')`,
    making the filter definition syntax much cleaner and more readable.
    """
    def __getattr__(self, name: str) -> Filter:
        """
        Dynamically creates a Filter object representing a field name.

        Example:
            >>> F.OrderID
            Filter('OrderID')
        """
        return Filter(name)

    def cf(self, type_name: str, view_name: str, field_name: str) -> Filter:
        """
        Creates a Filter object for a custom field.

        This helper generates the specific 'cf' syntax required by Acumatica.

        Args:
            type_name (str): The type of the custom element (e.g., 'String', 'Decimal').
            view_name (str): The name of the data view containing the element.
            field_name (str): The internal name of the element.

        Returns:
            A Filter object representing the custom field expression.
        """
        return Filter(f"cf.{type_name}(f='{view_name}.{field_name}')")

# The singleton factory instance to be used for creating all field filters.
F = _FieldFactory()

# The CustomField helper class
class CustomField:
    """
    A helper class to correctly and safely format strings for the OData $custom parameter.

    This class prevents common formatting errors by providing specific factory methods
    for different types of custom fields.
    """
    def __init__(self, view_name: str, field_name_or_id: str, entity_name: Optional[str] = None, is_attribute: bool = False):
        """
        Private constructor. Users should use the .field() or .attribute() class methods.
        """
        self.view_name = view_name
        self.field_name_or_id = field_name_or_id
        self.entity_name = entity_name
        self.is_attribute = is_attribute

    @classmethod
    def field(cls, view_name: str, field_name: str, entity_name: Optional[str] = None) -> "CustomField":
        """
        Creates a custom field for a standard or user-defined field.

        Args:
            view_name (str): The name of the data view containing the field (e.g., 'ItemSettings').
            field_name (str): The internal name of the field (e.g., 'UsrRepairItemType').
            entity_name (str, optional): The name of the detail/linked entity, if applicable.
                                        Providing this will format the string as 'entity/view.field'.
        """
        return cls(view_name, field_name, entity_name, is_attribute=False)

    @classmethod
    def attribute(cls, view_name: str, attribute_id: str) -> "CustomField":
        """
        Creates a custom field for a user-defined attribute.

        Args:
            view_name (str): The name of the data view containing the attribute (e.g., 'Document').
            attribute_id (str): The ID of the attribute (e.g., 'OPERATSYST').
        """
        return cls(view_name, attribute_id, is_attribute=True)

    def __str__(self) -> str:
        """Returns the correctly formatted string for the OData query."""
        if self.is_attribute:
            return f"{self.view_name}.Attribute{self.field_name_or_id}"
        
        field_part = f"{self.view_name}.{self.field_name_or_id}"
        
        if self.entity_name:
            return f"{self.entity_name}/{field_part}"
        else:
            return f"{field_part}"
    
    def __repr__(self) -> str:
        """Provides a developer-friendly representation of the CustomField object."""
        return f"CustomField('{self}')"


class QueryOptions:
    """
    A container for OData query parameters like $filter, $expand, etc.

    This class bundles all possible OData parameters into a single object and
    provides intelligent helpers, such as automatically adding required entities
    to the $expand parameter when a custom field from a detail entity is requested.
    """
    def __init__(
        self,
        filter: Union[str, Filter, None] = None,
        expand: Optional[List[str]] = None,
        select: Optional[List[str]] = None,
        top: Optional[int] = None,
        skip: Optional[int] = None,
        custom: Optional[List[Union[str, CustomField]]] = None,
    ) -> None:
        """
        Initializes the query options.

        Args:
            filter: An OData filter string or a Filter/Expression object.
            expand: A list of entity names to expand.
            select: A list of field names to return.
            top: The maximum number of records to return.
            skip: The number of records to skip for pagination.
            custom: A list of custom fields to include, using the CustomField helper
                    or raw strings.
        """
        self.filter = filter
        self.expand = expand
        self.select = select
        self.top = top
        self.skip = skip
        self.custom = custom

    def to_params(self) -> Dict[str, str]:
        """
        Serializes all options into a dictionary suitable for an HTTP request.

        This method automatically adds required entities to the `$expand`
        parameter based on the custom fields provided, preventing common errors.
        """
        params: Dict[str, str] = {}
        if self.filter:
            params["$filter"] = str(self.filter)
        if self.select:
            params["$select"] = ",".join(self.select)
        if self.top is not None:
            params["$top"] = str(self.top)
        if self.skip is not None:
            params["$skip"] = str(self.skip)

        # --- Combined logic for $custom and $expand ---
        
        # Use a set for expand_values to automatically handle duplicates
        expand_values = set(self.expand) if self.expand else set()
        custom_strings = []

        if self.custom:
            for item in self.custom:
                custom_strings.append(str(item))
                # If it's a CustomField on a detail entity, ensure the entity is expanded
                if isinstance(item, CustomField) and item.entity_name:
                    expand_values.add(item.entity_name)
        
        # Add the parameters to the dictionary if they have content
        if custom_strings:
            params["$custom"] = ",".join(custom_strings)

        if expand_values:
            # Sorting the list provides a consistent, predictable output order
            params["$expand"] = ",".join(sorted(list(expand_values)))

        return params