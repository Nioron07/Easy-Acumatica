# src/easy_acumatica/models/time_entry_builder.py

from __future__ import annotations
from typing import Any, Dict, List
import copy

class TimeEntryBuilder:
    """
    Fluent builder for the JSON payload to create or update a TimeEntry.
    """

    def __init__(self):
        self._fields: Dict[str, Any] = {}

    def set(self, field: str, value: Any) -> TimeEntryBuilder:
        """Set a top-level field on the time entry."""
        self._fields[field] = {"value": value}
        return self

    def summary(self, summary_text: str) -> TimeEntryBuilder:
        """Shortcut for .set('Summary', summary_text)."""
        return self.set("Summary", summary_text)

    def date(self, date_str: str) -> TimeEntryBuilder:
        """Shortcut for .set('Date', date_str). e.g., '2022-08-17T05:50:43'"""
        return self.set("Date", date_str)

    def employee(self, employee_id: str) -> TimeEntryBuilder:
        """Shortcut for .set('Employee', employee_id)."""
        return self.set("Employee", employee_id)

    def project_id(self, project_id: str) -> TimeEntryBuilder:
        """Shortcut for .set('ProjectID', project_id)."""
        return self.set("ProjectID", project_id)

    def project_task_id(self, task_id: str) -> TimeEntryBuilder:
        """Shortcut for .set('ProjectTaskID', task_id)."""
        return self.set("ProjectTaskID", task_id)

    def cost_code(self, cost_code: str) -> TimeEntryBuilder:
        """Shortcut for .set('CostCode', cost_code)."""
        return self.set("CostCode", cost_code)

    def earning_type(self, earning_type: str) -> TimeEntryBuilder:
        """Shortcut for .set('EarningType', earning_type)."""
        return self.set("EarningType", earning_type)

    def time_spent(self, time_spent: str) -> TimeEntryBuilder:
        """Shortcut for .set('TimeSpent', time_spent). e.g., '01:30'. Will be in the HH:MM Format"""
        return self.set("TimeSpent", time_spent)

    def billable_time(self, billable_time: str) -> TimeEntryBuilder:
        """Shortcut for .set('BillableTime', billable_time). e.g., '00:30'. Will be in the HH:MM Format"""
        return self.set("BillableTime", billable_time)
    
    def time_entry_id(self, time_entry_id: str) -> TimeEntryBuilder:
        """Shortcut to set the 'TimeEntryID' field of the time entry. From the API: param has the GuidValue type; however, its value is a sequentially generated string that looks like a GUID. Therefore, the global uniqueness of the values is not guarantee"""
        return self.set("TimeEntryID", time_entry_id)
    
    
    def to_body(self) -> Dict[str, Any]:
        """Constructs the final JSON payload for the API request."""
        return copy.deepcopy(self._fields)