# src/easy_acumatica/sub_services/inventory.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import time

from ..models.inventory_issue_builder import InventoryIssueBuilder
from ..models.inquiry_builder import InquiryBuilder
from ..models.item_warehouse_builder import ItemWarehouseBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient
    import requests

__all__ = ["InventoryService"]


class InventoryService:
    """Sub-service for inventory-related entities."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_inventory_issue(self, api_version: str, builder: InventoryIssueBuilder) -> Any:
        """
        Create a new inventory issue.

        Sends a PUT request to the /InventoryIssue endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/InventoryIssue"
        params = {"$expand": "Details"}
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
        
    def get_release_status(self, location_url: str) -> "requests.Response":
        """
        Checks the status of an inventory release operation.

        Sends a GET request to the provided location URL.
        """
        if not self._client.persistent_login:
            self._client.login()

        # Ensure the location URL is absolute
        if location_url.startswith("/"):
            location_url = self._client.base_url + location_url

        headers = {"Accept": "application/json"}
        resp = self._client._request(
            "get",
            location_url,
            headers=headers,
            verify=self._client.verify_ssl
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
            
        return resp

    def release_inventory_issue(
        self,
        api_version: str,
        reference_nbr: str,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Releases an inventory issue.

        Sends a POST to the 'ReleaseInventoryIssue' action of the InventoryIssue endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/InventoryIssue/ReleaseInventoryIssue"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        body = {
            "entity": {
                "ReferenceNbr": {"value": reference_nbr}
            }
        }

        initial_resp = self._client._request(
            "post",
            url,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        
        if initial_resp.status_code == 204:
            if not self._client.persistent_login:
                self._client.logout()
            return
            
        if initial_resp.status_code == 202:
            location_url = initial_resp.headers.get("Location")
            if not location_url:
                raise RuntimeError("Acumatica did not return a Location header for the action.")
                
            start_time = time.time()
            while time.time() - start_time < timeout_sec:
                poll_resp = self.get_release_status(location_url)
                
                if poll_resp.status_code == 204:
                    if not self._client.persistent_login:
                        self._client.logout()
                    return
                    
                if poll_resp.status_code != 202:
                    _raise_with_detail(poll_resp)
                    
                time.sleep(polling_interval_sec)
                
            raise RuntimeError(f"Action 'Release Inventory Issue' timed out after {timeout_sec} seconds.")
            
        _raise_with_detail(initial_resp)

    def get_inventory_quantity_available(
        self,
        api_version: str,
        inventory_id: str,
        last_modified_date_time: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve the available quantity of an inventory item.

        Sends a PUT request to the /InventoryQuantityAvailable endpoint.
        """
        opts = (
            InquiryBuilder()
            .param("InventoryID", inventory_id)
            .param("LastModifiedDateTime", last_modified_date_time)
            .expand("Results")
        )
        response = self._client.inquiries.get_data_from_inquiry_form(api_version, "InventoryQuantityAvailable", opts)
        return response.get("Results", [])

    def get_inventory_summary(self, api_version: str, inventory_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve the summary information about an inventory item.

        Sends a PUT request to the /InventorySummaryInquiry endpoint.
        """
        opts = InquiryBuilder().param("InventoryID", inventory_id).expand("Results")
        response = self._client.inquiries.get_data_from_inquiry_form(api_version, "InventorySummaryInquiry", opts)
        return response.get("Results", [])
    
    def update_item_warehouse_details(self, api_version: str, builder: ItemWarehouseBuilder) -> Any:
        """
        Update item-warehouse details.

        Sends a PUT request to the /ItemWarehouse endpoint.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/ItemWarehouse"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            json=builder.to_body(),
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()