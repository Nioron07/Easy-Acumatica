# src/easy_acumatica/sub_services/invoices.py

from __future__ import annotations
import time
from typing import TYPE_CHECKING, Any, Optional

from ..models.invoice_builder import InvoiceBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["InvoicesService"]


class InvoicesService:
    """Sub-service for creating and managing Invoices."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_invoice(
        self,
        api_version: str,
        builder: InvoiceBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new Invoice, potentially with overridden tax details.

        Sends a PUT request to the /Invoice endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : InvoiceBuilder
            A fluent builder instance containing the invoice details.
        options : QueryOptions, optional
            Allows for specifying $expand, etc., in the response.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Invoice"
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
        
    def update_invoice(
        self,
        api_version: str,
        builder: InvoiceBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Update an existing Invoice.

        The builder should be configured with the 'id' of the invoice to update.

        Sends a PUT request to the /Invoice endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : InvoiceBuilder
            A fluent builder instance containing the invoice 'id' and fields to update.
        options : QueryOptions, optional
            Allows for specifying $custom, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body of the updated record.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Invoice"
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        
        body = builder.to_body()
        if 'id' not in body:
            raise ValueError("InvoiceBuilder must have the 'id' set to update an invoice.")

        resp = self._client._request(
            "put",
            url,
            params=params,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def get_invoices(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of invoices.

        Sends a GET request to the /Invoice endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        options : QueryOptions, optional
            Allows for specifying $filter, $select, $expand, etc.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica, typically a list of invoices.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Invoice"
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

    def release_invoice(
        self,
        api_version: str,
        note_id: str,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Releases an AR Invoice, triggering the financial posting process.

        Sends a POST to the 'ReleaseInvoice' action of the Invoice endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        note_id : str
            The NoteID (GUID) of the invoice to release.
        polling_interval_sec : int, optional
            The interval in seconds to wait between polling for completion.
        timeout_sec : int, optional
            The maximum time in seconds to wait for the action to complete.

        Raises
        ------
        RuntimeError
            If the action fails or times out.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Invoice/ReleaseInvoice"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        body = {
            "entity": {"id": note_id}
        }
        
        # 1. Initial POST to start the action
        initial_resp = self._client._request(
            "post",
            url,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        
        # If 204, the action was synchronous and is already complete
        if initial_resp.status_code == 204:
            if not self._client.persistent_login:
                self._client.logout()
            return
            
        # If 202, the action is asynchronous, and we need to poll
        if initial_resp.status_code == 202:
            location_url = initial_resp.headers.get("Location")
            if not location_url:
                raise RuntimeError("Acumatica did not return a Location header for the action.")

            if location_url.startswith("/"):
                location_url = self._client.base_url + location_url
                
            # 2. Poll the Location URL until the action is complete
            start_time = time.time()
            while time.time() - start_time < timeout_sec:
                poll_resp = self._client._request(
                    "get",
                    location_url,
                    headers=headers,
                    verify=self._client.verify_ssl
                )
                
                if poll_resp.status_code == 204:  # Action is complete
                    if not self._client.persistent_login:
                        self._client.logout()
                    return
                    
                if poll_resp.status_code != 202:
                    _raise_with_detail(poll_resp)
                    
                time.sleep(polling_interval_sec)
                
            raise RuntimeError(f"Action 'Release Invoice' timed out after {timeout_sec} seconds.")
            
        # Handle any other unexpected status codes
        _raise_with_detail(initial_resp)
