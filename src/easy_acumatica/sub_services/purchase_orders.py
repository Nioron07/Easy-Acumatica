from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models.query_builder import QueryOptions
from ..models.purchase_order_builder import PurchaseOrderBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["PurchaseOrdersService"]


class PurchaseOrdersService:
    """Sub-service for purcahse order related entities"""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_purchase_order(
        self,
        api_version: str,
        builder: PurchaseOrderBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Purchase Order.

        Sends a PUT request to the /PurchaseOrder endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : PurchaseOrderBuilder
            A fluent builder instance containing the purchase order details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/PurchaseOrder"
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