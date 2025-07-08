# src/easy_acumatica/sub_services/sales_orders.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models.sales_order_builder import SalesOrderBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["SalesOrdersService"]


class SalesOrdersService:
    """Sub-service for sales order-related entities."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_sales_orders(self, api_version: str, options: Optional[QueryOptions] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of sales orders.

        Sends a GET request to the /SalesOrder endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/SalesOrder"
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

    def create_sales_order(self, api_version: str, builder: SalesOrderBuilder, options: Optional[QueryOptions] = None) -> Any:
        """
        Create a new sales order.

        Sends a PUT request to the /SalesOrder endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/SalesOrder"
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

    def update_sales_order(self, api_version: str, builder: SalesOrderBuilder, options: Optional[QueryOptions] = None) -> Any:
        """
        Update an existing sales order.

        Sends a PUT request to the /SalesOrder endpoint.
        """
        return self.create_sales_order(api_version, builder, options)

    def apply_discounts(self, api_version: str, order_type: str, order_nbr: str) -> Any:
        """
        Apply discounts to a sales order.

        Sends a POST to the 'AutoRecalculateDiscounts' action of the SalesOrder endpoint.
        """
        entity = {"OrderType": {"value": order_type}, "OrderNbr": {"value": order_nbr}}
        return self._client.actions.execute_action(
            api_version, "SalesOrder", "AutoRecalculateDiscounts", entity
        )

    def create_shipment(self, api_version: str, order_id: str, shipment_date: str, warehouse_id: str) -> Any:
        """
        Create a shipment from a sales order.

        Sends a POST to the 'SalesOrderCreateShipment' action of the SalesOrder endpoint.
        """
        entity = {"id": {"value": order_id}}
        parameters = {"ShipmentDate": shipment_date, "WarehouseID": warehouse_id}
        return self._client.actions.execute_action(
            api_version, "SalesOrder", "SalesOrderCreateShipment", entity, parameters
        )