from __future__ import annotations

from typing import List, Optional, Union, Dict
from .filter_builder import Filter

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