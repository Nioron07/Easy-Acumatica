# src/easy_acumatica/sub_services/shipments.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from ..models.shipment_builder import ShipmentBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ShipmentsService"]


class ShipmentsService:
    """Sub-service for shipment-related entities."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_shipments(self, api_version: str, options: Optional[QueryOptions] = None) -> List[Dict[str, Any]]:
        """
        Retrieve a list of shipments.

        Sends a GET request to the /Shipment endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Shipment"
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

    def create_shipment(self, api_version: str, builder: ShipmentBuilder, options: Optional[QueryOptions] = None) -> Any:
        """
        Create a new shipment.

        Sends a PUT request to the /Shipment endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Shipment"
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

    def update_shipment(self, api_version: str, builder: ShipmentBuilder, options: Optional[QueryOptions] = None) -> Any:
        """
        Update an existing shipment.

        Sends a PUT request to the /Shipment endpoint.
        """
        return self.create_shipment(api_version, builder, options)

    def confirm_shipment(self, api_version: str, shipment_nbr: str) -> Any:
        """
        Confirm a shipment.

        Sends a POST to the 'ConfirmShipment' action of the SalesOrder endpoint.
        """
        entity = {"ShipmentNbr": {"value": shipment_nbr}}
        return self._client.actions.execute_action(
            api_version, "SalesOrder", "ConfirmShipment", entity
        )

    def prepare_invoice(self, api_version: str, shipment_nbr: str) -> Any:
        """
        Prepare an invoice for a shipment.

        Sends a POST to the 'PrepareInvoice' action of the Shipment endpoint.
        """
        entity = {"ShipmentNbr": {"value": shipment_nbr}}
        return self._client.actions.execute_action(
            api_version, "Shipment", "PrepareInvoice", entity
        )