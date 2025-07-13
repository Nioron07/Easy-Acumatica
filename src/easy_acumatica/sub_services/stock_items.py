# src/easy_acumatica/sub_services/stock_items.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..builders.stock_item_builder import StockItemBuilder
from ..odata import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["StockItemsService"]


class StockItemsService:
    """Sub-service for stock item-related entities."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_stock_items(self, api_version: Optional[str] = None, options: Optional[QueryOptions] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of stock items.

        Sends a GET request to the /StockItem endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        if api_version == None:
            url = f"{self._client.base_url}/entity/Default/{self._client.endpoints["Default"]['version']}/StockItem"
        else:
            url = f"{self._client.base_url}/entity/Default/{api_version}/StockItem"
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

    def get_stock_item_by_id(self, inventory_id: str, api_version: Optional[str] = None, options: Optional[QueryOptions] = None) -> Dict[str, Any]:
        """
        Retrieve a single stock item by its ID.

        Sends a GET request to the /StockItem/{inventory_id} endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        if api_version == None:
            url = f"{self._client.base_url}/entity/Default/{self._client.endpoints["Default"]['version']}/StockItem/{inventory_id}"
        else:
            url = f"{self._client.base_url}/entity/Default/{api_version}/StockItem/{inventory_id}"
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

    def create_stock_item(self, builder: StockItemBuilder, api_version: Optional[str] = None, options: Optional[QueryOptions] = None) -> Any:
        """
        Create a new stock item.

        Sends a PUT request to the /StockItem endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        if api_version == None:
            url = f"{self._client.base_url}/entity/Default/{self._client.endpoints["Default"]['version']}/StockItem"
        else:
            url = f"{self._client.base_url}/entity/Default/{api_version}/StockItem"
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

    def update_stock_item(self, builder: StockItemBuilder, api_version: Optional[str] = None, options: Optional[QueryOptions] = None) -> Any:
        """
        Update an existing stock item.

        Sends a PUT request to the /StockItem endpoint.
        """
        return self.create_stock_item(api_version, builder, options)

    def get_stock_item_attachments(self, inventory_id: str, api_version: Optional[str] = None,) -> List[Dict[str, Any]]:
        """
        Retrieve the list of attachments for a stock item.

        Sends a GET request to the /StockItem/{inventory_id} endpoint with $expand=files.
        """
        options = QueryOptions(select=["InventoryID", "files"], expand=["files"])
        stock_item = self.get_stock_item_by_id(api_version, inventory_id, options)
        return stock_item.get("files", [])