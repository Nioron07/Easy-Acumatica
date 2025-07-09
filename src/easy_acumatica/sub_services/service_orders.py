from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ServiceOrdersService"]

class ServiceOrdersService:
    """This is  a sub-service to retrieve a service order from acumatica 

        Please note: 
        ------------
        this service is currently untested due to our subscription of
        Acumatica lacking service orders. Please contact Nioron07 or Typhlosion123 on Github
        if any issues have been encountered with this specific endpoint
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_service_orders(
        self, 
        api_version: str, 
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieves service orders depending on user input filters

        Sends a GET request to the /ServiceOrder Endpoint

        api_version : str
            The API version segment (e.g., '24.200.001').
        options : QueryOptions, optional
            Allows for specifying $filter, $select, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body from Acumatica, typically a list of ServiceOrders.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/ServiceOrder"
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