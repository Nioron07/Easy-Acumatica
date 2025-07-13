# src/easy_acumatica/models/inventory_issue_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class InventoryIssueBuilder:
    """
    Fluent builder for the JSON payload to create an InventoryIssue.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._details: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> InventoryIssueBuilder:
        """Set a top-level field on the inventory issue."""
        self._fields[field] = {"value": value}
        return self

    def date(self, date: str) -> InventoryIssueBuilder:
        """Shortcut for .set('Date', date)."""
        return self.set("Date", date)

    def description(self, description: str) -> InventoryIssueBuilder:
        """Shortcut for .set('Description', description)."""
        return self.set("Description", description)

    def post_period(self, period: str) -> InventoryIssueBuilder:
        """Shortcut for .set('PostPeriod', period)."""
        return self.set("PostPeriod", period)

    def add_detail(self, **kwargs) -> InventoryIssueBuilder:
        """Adds a detail line to the inventory issue."""
        detail = {}
        for key, value in kwargs.items():
            detail[key] = {"value": value}
        self._details.append(detail)
        return self

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._details:
            body["Details"] = copy.deepcopy(self._details)
        return body