# src/easy_acumatica/models/case_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class CaseBuilder:
    """
    Fluent builder for the JSON payload to create or update a Case.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._related_cases: List[Dict[str, Dict[str, Any]]] = []
        self._custom_fields: Dict[str, Dict[str, Dict[str, Any]]] = {}

    def set(self, field: str, value: Any) -> CaseBuilder:
        """Set a top-level field on the case."""
        self._fields[field] = {"value": value}
        return self

    def class_id(self, class_id: str) -> CaseBuilder:
        """Shortcut for .set('ClassID', class_id)."""
        return self.set("ClassID", class_id)

    def business_account(self, account: str) -> CaseBuilder:
        """Shortcut for .set('BusinessAccount', account)."""
        return self.set("BusinessAccount", account)

    def contact_id(self, contact_id: str) -> CaseBuilder:
        """Shortcut for .set('ContactID', contact_id)."""
        return self.set("ContactID", contact_id)

    def subject(self, subject: str) -> CaseBuilder:
        """Shortcut for .set('Subject', subject)."""
        return self.set("Subject", subject)

    def add_related_case(self, case_id: str) -> CaseBuilder:
        """Adds a related case to the case's RelatedCases."""
        self._related_cases.append({"CaseID": {"value": case_id}})
        return self

    def set_custom_field(self, view: str, field: str, value: Any, field_type: str = "CustomStringField") -> CaseBuilder:
        """Sets a custom field value."""
        if view not in self._custom_fields:
            self._custom_fields[view] = {}
        self._custom_fields[view][field] = {"type": field_type, "value": value}
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._related_cases:
            body["RelatedCases"] = copy.deepcopy(self._related_cases)
        if self._custom_fields:
            body["custom"] = copy.deepcopy(self._custom_fields)
        return body