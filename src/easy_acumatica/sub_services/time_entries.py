# src/easy_acumatica/sub_services/time_entries.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..models.time_entry_builder import TimeEntryBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["TimeEntryService"]


class TimeEntriesService:
    """Sub-service for reading Employee Time Activities.
    
    Warning, our current Acumatica Environment does not allow for Time Entries, this is an untested endpoint. 

    Please contact us if any issues arise!
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_time_entries(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of employee time activities.

        Sends a GET request to the /TimeEntry endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        options : QueryOptions, optional
            Allows for specifying $filter, $select, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body from Acumatica, typically a list of time entries.


        In order to get a specific time entries, please filter based upon ID or based upon time using out FilterBuilder class

        Examples
        ---------
        f = (F.CreatedDate >= "2022-08-17") & (F.CreatedDate <= "2022-08-18")

        or f = (F.TimeEntryID == xxxxxxxx)
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/TimeEntry"
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()
    

    def create_time_entry(
            self, 
            api_version: str, 
            builder: TimeEntryBuilder, 
            options: Optional[QueryOptions] = None
    ) -> Any:
        """
        Create a new employee time activity as a time entry.

        Sends a PUT request to the /SalesOrder endpoint.
        """

        if not self._client.persistent_login:
            self._client.login()
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self._client.base_url}/entity/Default/{api_version}/TimeEntry"

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