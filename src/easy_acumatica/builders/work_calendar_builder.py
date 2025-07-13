# src/easy_acumatica/models/work_calendar_builder.py

from __future__ import annotations
from typing import Any, Dict, List, Optional
import copy

class WorkCalendarBuilder:
    """
    Fluent builder for the JSON payload to create or update a WorkCalendar.

    Please note, as of right now, there is no way to actually add workdays and modify them. If someone finds out, please let us know!
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}
        self._exceptions: List[Dict[str, Any]] = []
        self._calendar: List[Dict[str, Any]] = []

    def set(self, field: str, value: Any) -> WorkCalendarBuilder:
        """Set a top-level field on the work calendar."""
        self._fields[field] = {"value": value}
        return self

    def work_calendar_id(self, work_calendar_id: str) -> WorkCalendarBuilder:
        """Shortcut for the WorkCalendarID field."""
        return self.set("WorkCalendarID", work_calendar_id)
    
    def description(self, description: str) -> WorkCalendarBuilder:
        """Shortcut for the Description field."""
        return self.set("Description", description)
    
    def time_zone(self, time_zone: str) -> WorkCalendarBuilder:
        """
        Shortcut for the TimeZone field.
        
        The timezone format used by Acumatica is specific, e.g., 'GMTM0800A'.
        """
        return self.set("TimeZone", time_zone)

    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        body = copy.deepcopy(self._fields)
        if self._exceptions:
            # The nested array is typically named "CalendarExceptions"
            body["CalendarExceptions"] = self._exceptions
        if self._calendar:
            body["Calendar"] = self._calendar
        return body