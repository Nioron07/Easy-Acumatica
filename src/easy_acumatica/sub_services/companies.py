# src/easy_acumatica/sub_services/companies.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List

from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["CompaniesService"]


class CompaniesService:
    """Sub-service for retrieving company and branch structure information."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_structure(self, api_version: str) -> List[Dict[str, Any]]:
        """
        Retrieve the companies' structure.

        Sends a PUT request to the /CompaniesStructure endpoint and expands the Results.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').

        Returns
        -------
        List[Dict[str, Any]]
            A list of dictionaries representing the companies' structure.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/CompaniesStructure"
        params = {"$expand": "Results"}
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            params=params,
            json={},
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        # The actual data is in the 'Results' key
        return resp.json().get("Results", [])