# src/easy_acumatica/models/lead_builder.py

from __future__ import annotations
from typing import Any, Dict
import copy


class LeadBuilder:
    """
    Fluent builder for the JSON payload to create a Lead.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> LeadBuilder:
        """Set a top-level field on the lead."""
        self._fields[field] = {"value": value}
        return self

    def first_name(self, name: str) -> LeadBuilder:
        """Shortcut for .set('FirstName', name)."""
        return self.set("FirstName", name)

    def last_name(self, name: str) -> LeadBuilder:
        """Shortcut for .set('LastName', name)."""
        return self.set("LastName", name)

    def email(self, email: str) -> LeadBuilder:
        """Shortcut for .set('Email', email)."""
        return self.set("Email", email)

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        return copy.deepcopy(self._fields)

