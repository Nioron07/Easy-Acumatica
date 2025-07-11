# src/easy_acumatica/sub_services/time_entries.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..models.work_calendar_builder import WorkCalendarBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["WorkCalendarService"]


class WorkCalendarsService:
    """Sub-service for creating Work Calendars
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client
    

    def create_work_calendar(
            self, 
            api_version: str, 
            builder: WorkCalendarBuilder, 
            options: Optional[QueryOptions] = None
    ) -> Any:
        """
        Create a new work calendar. 

        Sends a PUT request to the /WorkCalendar endpoint.
        """

        if not self._client.persistent_login:
            self._client.login()
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self._client.base_url}/entity/Default/{api_version}/WorkCalendar"

        resp = self._client._request(
            "put", 
            url, 
            params=params, 
            headers=headers, 
            json=builder.to_body()
        )

        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()
    
    def get_work_calendar(
            self, 
            api_version: str, 
            options: Optional[QueryOptions] = None
    ) -> Any: 
        """
        Get work calendars. 

        REMINDER: THIS ONLY RETURNS THE ID, DESCRIPTION, AND TIME ZONE. THE ACTUAL DAYS DOES NOT SEEM TO BE ACCESSIBLE FROM THIS ENDPOINT THAT ISNT EVEN LISTED IN THE API DOCS 

        Use FilterBuilder to get the ID you want
        
        """
        if not self._client.persistent_login:
            self._client.login()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        params = options.to_params() if options else None
        url = f"{self._client.base_url}/entity/Default/{api_version}/WorkCalendar"

        resp = self._client._request(
            "get", 
            url, 
            headers=headers, 
            params=params, 
        )

        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()