# src/easy_acumatica/sub_services/cases.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.case_builder import CaseBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["CasesService"]


class CasesService:
    """Sub-service for creating and managing Cases."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_case(
        self,
        api_version: str,
        builder: CaseBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Case.

        Sends a PUT request to the /Case endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : CaseBuilder
            A fluent builder instance containing the case details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Case"
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

    def link_case_to_another_case(
        self,
        api_version: str,
        builder: CaseBuilder,
    ) -> Any:
        """
        Create a new case and link it to another case.

        Sends a PUT request to the /Case endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment, e.g. '24.200.001'.
        builder : CaseBuilder
            A fluent builder instance containing the case details, including related cases.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        options = QueryOptions(expand=["RelatedCases"])
        return self.create_case(api_version, builder, options)