# easy_acumatica/sub_services/customers.py

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..models.filter_builder import F
from ..models.customer_builder import CustomerBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["CustomersService"]


class CustomersService:
    """Sub-service for Contract-based Customer retrieval and creation."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_customers(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of Customer records via the contract-based REST API.

        Sends an HTTP GET to:
            {base_url}/entity/Default/{api_version}/Customer

        You can optionally supply a QueryOptions object to filter, expand related
        entities, select specific fields, page results, or include custom fields.

        Parameters
        ----------
        api_version : str
            The API version segment, e.g. '24.200.001'.
        options : QueryOptions, optional
            Fluent container for OData query parameters:
            - filter: Filter expressions (eq, gt, contains, etc.)
            - expand: list of related entities to expand
            - select: list of fields to return
            - top: maximum number of records
            - skip: number of records to skip
            - custom: custom field paths
            If None, no query parameters are sent.

        Returns
        -------
        Any
            The parsed JSON body of the response (typically a list of customer dicts).

        Raises
        ------
        AcumaticaError (RuntimeError)
            If the HTTP response code is not 2xx, with detailed error text 
            extracted from the response.

        Example
        -------
        >>> from easy_acumatica.models.filter_builder import Filter, QueryOptions
        >>> opts = QueryOptions(
        ...     filter=Filter().eq("Status", "Active"),
        ...     select=["CustomerID", "CustomerName"],
        ...     expand=["BillingContact"]
        ... )
        >>> clients = client.customers.get_customers("24.200.001", opts)
        >>> for c in clients:
        ...     print(c["CustomerID"], c["CustomerName"])
        """
        # ensure we have a session cookie
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Customer"
        params = options.to_params() if options else None

        resp = self._client.session.get(
            url,
            params=params,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        # if doing per-call login/logout, log out now
        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def create_customer(
        self,
        api_version: str,
        builder: CustomerBuilder,
    ) -> Any:
        """
        Create (or update) a Customer via the contract-based API.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/Customer
        with a body like:
        {
            "CustomerID":   {"value": "..."},
            "CustomerName": {"value": "..."},
            "CustomerClass":{"value": "..."},
            ...
        }

        Returns the newly created Customer record as JSON.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Customer"
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

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
    
    def update_customer(
        self,
        api_version: str,
        builder: CustomerBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Update existing customer(s) via contract-based API.

        You must supply a Filter in options to pick which record(s) to update,
        for example:

            opts = QueryOptions(
                filter=Filter().eq("MainContact/Email", "info@jevy-comp.con"),
                expand=["MainContact", "BillingContact"],
                select=["CustomerID", "CustomerClass", "BillingContact/Email"],
            )

        Then:

            cb = (CustomerBuilder()
                  .set("CustomerClass", "INTL")
                  .set("BillingContactOverride", True)
                  .set("BillingContact", {
                      "Email": {"value": "green@jevy-comp.con"},
                      "Attention": {"value": "Mr. Jack Green"},
                      "JobTitle": {"value": ""}
                  }))
            updated = client.customers.update_customer("24.200.001", cb, opts)
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Customer"
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
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
    
    def update_customer_currency_overriding(
        self,
        api_version: str,
        customer_id: str,
        enable: bool,
        currency_rate_type: str = "SPOT"
    ) -> Any:
        """
        Enable currency and rate overriding for a given customer.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/Customer

        with a body:
        {
            "CustomerID": {"value": customer_id},
            "EnableCurrencyOverride": {"value": true},
            "EnableRateOverride": {"value": true},
            "CurrencyRateType": {"value": currency_rate_type}
        }
        """
        if not self._client.persistent_login:
            self._client.login()

        # build the minimal payload
        body = (
            CustomerBuilder()
            .customer_id(customer_id)
            .set("EnableCurrencyOverride", enable)
            .set("EnableRateOverride", enable)
            .set("CurrencyRateType", currency_rate_type)
            .to_body()
        )

        url = f"{self._client.base_url}/entity/Default/{api_version}/Customer"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
    
    def get_shipping_contact(
        self,
        api_version: str,
        customer_id: str,
    ) -> Optional[dict[str, Any]]:
        """
        Retrieve the ShippingContact sub-object for a single customer.

        Performs a GET with:
            $expand=ShippingContact
            $filter=CustomerID eq '{customer_id}'

        Returns the 'ShippingContact' dict for that customer, or None if not found.
        """
        opts = QueryOptions(
            filter=F.CustomerID == customer_id,
            expand=["ShippingContact"]
        )
        results = self.get_customers(api_version, opts)
        if not isinstance(results, list) or not results:
            return None
        # assume unique CustomerID → first record
        return results[0].get("ShippingContact")
    
    def assign_tax_zone(
        self,
        api_version: str,
        customer_id: str,
        tax_zone: str,
    ) -> Any:
        """
        Assign a Tax Zone to a Customer.

        Sends a PUT to:
            {base_url}/entity/Default/{api_version}/Customer
        with:
          params: {'$select': 'CustomerID,TaxZone'}
          body: {
            "CustomerID": {"value": customer_id},
            "TaxZone":    {"value": tax_zone}
          }

        Returns the updated record JSON.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Customer"
        params = QueryOptions(select=["CustomerID", "TaxZone"]).to_params()
        body = (
            CustomerBuilder()
            .customer_id(customer_id)
            .set("TaxZone", tax_zone)
            .to_body()
        )
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            params=params,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()