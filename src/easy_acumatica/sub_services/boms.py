# src/easy_acumatica/sub_services/boms.py
from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
from ..models.bom_builder import BOMBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

class BomsService:
    """Sub-service for creating Bills of Material (BOMs)."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_bom(
        self,
        api_version: str,
        builder: BOMBuilder,
        options: Optional[QueryOptions] = None,
    ) -> dict:
        """
        Create a new BOM.

        Sends a PUT request to the /BillOfMaterial endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/MANUFACTURING/{api_version}/BillOfMaterial"
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
    
    def get_boms(
        self, 
        api_version: str, 
        bom_id: str = None, 
        revision: str = None, 
        options: Optional[QueryOptions] = None
    ) -> Any:
        """
        Retreieve either a list of all BOMS or a single BOM

        Getting one BOM requires bom_id AND revision

        sends a GET request to the BillOfMaterial Endpoint
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/MANUFACTURING/{api_version}/BillOfMaterial"

        if bom_id:
            url += f"/{bom_id}"
            if revision:
                url += f"/{revision}"

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