# src/easy_acumatica/sub_services/payments.py

from __future__ import annotations
import time
from typing import TYPE_CHECKING, Any, Optional

from ..models.payment_builder import PaymentBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["PaymentsService"]


class PaymentsService:
    """Sub-service for creating, retrieving, and managing Payments."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def create_payment(
        self,
        api_version: str,
        builder: PaymentBuilder,
    ) -> Any:
        """
        Create a new Payment via the contract-based API.

        This sends a PUT request to the /Payment endpoint. It can be used
        to create a payment that is not linked to a specific invoice or
        sales order.

        Parameters
        ----------
        api_version : str
            The API version segment, e.g. '24.200.001'.
        builder : PaymentBuilder
            A fluent builder instance containing the payment details.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica, typically
            representing the newly created payment record.

        Raises
        ------
        RuntimeError
            If the HTTP response code is not 2xx.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Payment"
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

    def get_payment(
        self,
        api_version: str,
        payment_type: str,
        reference_nbr: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a single payment by its key fields (Type and Reference Number).

        Sends a GET request to:
            {base_url}/entity/Default/{api_version}/Payment/{payment_type}/{reference_nbr}

        Parameters
        ----------
        api_version : str
            The API version segment, e.g. '24.200.001'.
        payment_type : str
            The type of the payment (e.g., 'Payment', 'Prepayment').
        reference_nbr : str
            The reference number of the payment.
        options : QueryOptions, optional
            Allows specifying $select and $expand to get related data like
            ApplicationHistory.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.

        Raises
        ------
        RuntimeError
            If the HTTP response code is not 2xx.
        ValueError
            If the provided QueryOptions object contains a $filter.
        """
        if not self._client.persistent_login:
            self._client.login()

        if options and options.filter:
            raise ValueError(
                "QueryOptions.filter is not supported for getting a single record by key; "
                "the key fields in the URL are the filter."
            )

        url = f"{self._client.base_url}/entity/Default/{api_version}/Payment/{payment_type}/{reference_nbr}"
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

    def release_payment(
        self,
        api_version: str,
        payment_type: str,
        reference_nbr: str,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Releases a payment, triggering the financial posting process.

        Sends a POST to the 'Release' action of the Payment endpoint. This
        action is often asynchronous.

        Parameters
        ----------
        api_version : str
            The API version segment, e.g., '24.200.001'.
        payment_type : str
            The type of the payment to release.
        reference_nbr : str
            The reference number of the payment to release.
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

        url = f"{self._client.base_url}/entity/Default/{api_version}/Payment/Release"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        
        body = {
            "entity": {
                "Type": {"value": payment_type},
                "ReferenceNbr": {"value": reference_nbr},
            }
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
                
            raise RuntimeError(f"Action 'Release Payment' timed out after {timeout_sec} seconds.")
            
        # Handle any other unexpected status codes
        _raise_with_detail(initial_resp)
