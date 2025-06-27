# src/easy_acumatica/sub_services/ledgers.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["LedgersService"]


class LedgersService:
    """Sub-service for retrieving Ledger information."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_ledgers(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of ledgers.

        Sends a GET request to the /Ledger endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        options : QueryOptions, optional
            Allows for specifying $filter, $select, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body from Acumatica, typically a list of ledgers.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Ledger"
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
