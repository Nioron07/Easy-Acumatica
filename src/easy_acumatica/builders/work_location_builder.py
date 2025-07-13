# src/easy_acumatica/models/work_location_builder.py

from __future__ import annotations
from typing import Any, Dict, Optional
import copy

class WorkLocationBuilder:
    """
    Fluent builder for the JSON payload to create or update a WorkLocation.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._address_info: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> WorkLocationBuilder:
        """Set a top-level field on the work location."""
        self._fields[field] = {"value": value}
        return self

    def work_location_id(self, location_id: str) -> WorkLocationBuilder:
        """Shortcut for .set('WorkLocationID', location_id)."""
        return self.set("WorkLocationID", location_id)

    def work_location_name(self, name: str) -> WorkLocationBuilder:
        """Shortcut for .set('WorkLocationName', name)."""
        return self.set("WorkLocationName", name)

    def active(self, is_active: bool) -> WorkLocationBuilder:
        """Shortcut for .set('Active', is_active)."""
        return self.set("Active", is_active)

    def address_info(
        self,
        address_line_1: Optional[str] = None,
        address_line_2: Optional[str] = None,
        city: Optional[str] = None,
        country: Optional[str] = None,
        postal_code: Optional[str] = None,
        state: Optional[str] = None
    ) -> WorkLocationBuilder:
        """
        Set fields within the AddressInfo object.
        """
        fields_to_set = {
            "AddressLine1": address_line_1,
            "AddressLine2": address_line_2,
            "City": city,
            "Country": country,
            "PostalCode": postal_code,
            "State": state
        }
        for key, value in fields_to_set.items():
            if value is not None:
                self._address_info[key] = {"value": value}
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._address_info:
            body["AddressInfo"] = copy.deepcopy(self._address_info)
        return body