# src/easy_acumatica/sub_services/work_locations.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.work_location_builder import WorkLocationBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["WorkLocationsService"]


class WorkLocationsService:
    """Sub-service for creating and managing Work Locations."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_work_location(
        self,
        api_version: str,
        builder: WorkLocationBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Work Location.

        Sends a PUT request to the /WorkLocation endpoint.

        This endpoint is untested due to our environment not having access to this. Please let us know if something goes wrong!
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/WorkLocation"
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            params=params,
            json=builder.to_body(),
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def get_work_locations(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of work locations.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/WorkLocation"
        params = options.to_params() if options else None
        headers = {"Accept": "application/json"}

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
    

    def get_work_calendar(
            self, 
            api_version: str, 
            options: Optional[QueryOptions] = None
    ) -> Any: 
        """
        Get work locations. 

        REMINDER: This endpoint is untested due to our Acumatica Envirnoment not having work locations. However, it is assumed it should work. 

        Use FilterBuilder to get the ID you want
        
        """
        if not self._client.persistent_login:
            self._client.login()
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        params = options.to_params() if options else None
        url = f"{self._client.base_url}/entity/Default/{api_version}/WorkLocation"

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