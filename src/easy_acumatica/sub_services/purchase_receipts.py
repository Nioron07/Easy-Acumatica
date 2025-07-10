# src/easy_acumatica/sub_services/purchase_receipts.py

from __future__ import annotations
import time
from typing import TYPE_CHECKING, Any, Optional

from ..models.purchase_receipt_builder import PurchaseReceiptBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["PurchaseReceiptsService"]


class PurchaseReceiptsService:
    """Sub-service for creating and managing Purchase Receipts."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create(
        self,
        api_version: str,
        builder: PurchaseReceiptBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Purchase Receipt.

        Sends a PUT request to the /PurchaseReceipt endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : PurchaseReceiptBuilder
            A fluent builder instance containing the purchase receipt details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/PurchaseReceipt"
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

    def release_purchase_receipt(
        self,
        api_version: str,
        id: str,
    ) -> None:
        """
        Releases a purchase receipt, triggering the financial posting process.

        Sends a POST to the 'ReleasePurchaseReceipt' action of the PurchaseReceipt endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        id : str
            The id of the purchase receipt to release.
        polling_interval_sec : int, optional
            The interval in seconds to wait between polling for completion.
        timeout_sec : int, optional
            The maximum time in seconds to wait for the action to complete.

        Raises
        ------
        RuntimeError
            If the action fails or times out.
        """

        url = f"{self._client.base_url}/entity/Default/{api_version}/PurchaseReceipt/ReleasePurchaseReceipt"
        body = {
            "entity": {"id": id}
        }
        
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self._client._request(
            "post", url, headers=headers, json=body, verify=self._client.verify_ssl,
        )

        if not self._client.persistent_login:
            self._client.logout()