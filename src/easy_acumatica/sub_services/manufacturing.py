# src/easy_acumatica/sub_services/manufacturing.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any

from ..models.configuration_entry_builder import ConfigurationEntryBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ManufacturingService"]


class ManufacturingService:
    """Sub-service for manufacturing-related entities."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_configuration_entry(self, api_version: str, configuration_id: str) -> Any:
        """
        Retrieve a configuration entry by its ID.

        Sends a GET request to the /ConfigurationEntry endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '25.100.001').
        configuration_id : str
            The ID of the configuration entry to retrieve.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/MANUFACTURING/{api_version}/ConfigurationEntry/{configuration_id}"
        params = {"$expand": "Attributes,Features/Options"}
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

    def update_configuration_entry(self, api_version: str, builder: ConfigurationEntryBuilder) -> Any:
        """
        Update a configuration entry.

        Sends a PUT request to the /ConfigurationEntry endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '25.100.001').
        builder : ConfigurationEntryBuilder
            A fluent builder instance containing the configuration entry details.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/MANUFACTURING/{api_version}/ConfigurationEntry"
        params = {"$expand": "Attributes,Features/Options"}
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