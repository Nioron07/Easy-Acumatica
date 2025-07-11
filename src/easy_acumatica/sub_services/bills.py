# src/easy_acumatica/sub_services/bills.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict

from ..models.bill_builder import BillBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

import json

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["BillsService"]


class BillsService:
    """Sub-service for creating and managing Bills."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_bill(
        self,
        api_version: str,
        builder: BillBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Bill.

        Sends a PUT request to the /Bill endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : BillBuilder
            A fluent builder instance containing the bill details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Bill"
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

    def approve_bill(
        self,
        api_version: str,
        reference_nbr: str,
    ) -> None:
        """
        Approve a bill.

        Sends a POST to the 'Approve' action of the Bill endpoint.
        """

        body = {
            "entity" : {
                "Type" : {"value": "Bill"}, 
                "ReferenceNbr" : {"value": reference_nbr}
            }
        }

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self._client.base_url}/entity/Default/{api_version}/Bill/Approve" 
        self._client._request(
            "post", url, headers=headers, json=body, verify=self._client.verify_ssl,
        )
        
    def release_retainage(
        self,
        api_version: str,
        reference_nbr: str,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Release retainage for a bill.

        Sends a POST to the 'ReleaseRetainage' action of the Bill endpoint.
        """
        entity_payload = {
            "Type": {"value": "Bill"},
            "ReferenceNbr": {"value": reference_nbr}
        }

        final_payload = {
            "entity": entity_payload,
        }

        # 2. Build the "parameters" part by wrapping each value
        if (parameters):
            parameters_payload = {
                key: {"value": value} for key, value in parameters.items()
            }
            final_payload["parameters"] = parameters_payload

            

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        url = f"{self._client.base_url}/entity/Default/{api_version}/Bill/ReleaseRetainage" 
        self._client._request(
            "post", 
            url, 
            headers=headers, 
            json=final_payload, 
            verify=self._client.verify_ssl
        )   