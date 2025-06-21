# services/records.py
from __future__ import annotations

import time
from typing import TYPE_CHECKING, Any, Optional, Union, List, Dict, Literal

from ..models.record_builder import RecordBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient
    import requests


class RecordsService:
    """
    Generic CRUD wrapper for *any* **top-level** entity exposed by the
    contract-based REST endpoint (Customer, StockItem, SalesOrder, …).

    Example
    -------
    >>> rec_svc = RecordsService(client)
    >>> customer = (RecordBuilder()
    ...     .field("CustomerID", "JOHNGOOD")
    ...     .field("CustomerName", "John Good")
    ...     .field("CustomerClass", "DEFAULT")
    ...     .link("MainContact")
    ...         .field("Email", "demo@gmail.com")
    ...         .link("Address").field("Country", "US"))
    >>> created = rec_svc.create_record("24.200.001", "Customer", customer)
    """

    # ---------------------------------------------------------------
    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    # ---------------------------------------------------------------
    def create_record(
        self,
        api_version: str,
        entity: str,
        record: Union[dict, RecordBuilder],
        *,
        options: Optional[QueryOptions] = None,
        business_date: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> Any:
        """
        Create a new record (HTTP **PUT**) for *entity*.

        Parameters
        ----------
        api_version : str
            Endpoint version, e.g. ``"24.200.001"``.
        entity : str
            Top-level entity name (``"Customer"``, ``"StockItem"``, …).
        record : dict | RecordBuilder
            The payload.  If a :class:`RecordBuilder` is supplied, its
            :pymeth:`RecordBuilder.build` output is used.
        options : QueryOptions, optional
            Lets you specify ``$expand``, ``$select``, or ``$custom`` so
            the response includes exactly what you need.
        business_date : optional 
            A date string (e.g., "2024-01-01") to use as the business date 
            for this transaction only.
        branch : optional 
            A branch name to use for this transaction only.

        Returns
        -------
        Any
            JSON representation of the newly-created record returned by
            Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()
        
        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}"
        params = options.to_params() if options else None
        headers = {"If-None-Match": "*", "Accept": "application/json", "Content-Type": "application/json"}
        
        # Add optional headers for business date and branch
        if business_date:
            headers["PX-CbApiBusinessDate"] = business_date
        if branch:
            headers["PX-CbApiBranch"] = branch

        body = record.build() if isinstance(record, RecordBuilder) else record
        resp = self._client._request(
            "put",
            url,
            params=params,
            headers=headers,
            json=body,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

    # ------------------------------------------------------------------
    def update_record(
        self,
        api_version: str,
        entity: str,
        record: Union[dict, RecordBuilder],
        *,
        options: Optional[QueryOptions] = None,
        business_date: Optional[str] = None,
        branch: Optional[str] = None,
    ) -> Any:
        """
        Update an existing record (HTTP **PUT**) for *entity*.

        Parameters
        ----------
        api_version : str
            Endpoint version, e.g. ``"24.200.001"``.
        entity : str
            Top-level entity name (``"Customer"``, ``"StockItem"``, …).
        record : dict | RecordBuilder
            JSON payload holding the **key fields** *or* an ``id`` so the
            server can locate the record, plus the fields you want to change.
        options : QueryOptions, optional
            Use this to add ``$filter`` (for additional lookup criteria),
            ``$expand``, ``$select``, or ``$custom``.  
            *Remember*: every linked or detail entity you expect back must be
            listed in ``$expand``.
        business_date : optional 
            A date string to override the business date.    
        branch : optional 
            A branch name to override the current branch.

        Returns
        -------
        Any
            JSON representation of the updated record (server response).
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}"
        params = options.to_params() if options else None
        headers = {"If-Match": "*", "Accept": "application/json", "Content-Type": "application/json"}
        
        # Add optional headers for business date and branch
        if business_date:
            headers["PX-CbApiBusinessDate"] = business_date
        if branch:
            headers["PX-CbApiBranch"] = branch

        body = record.build() if isinstance(record, RecordBuilder) else record
        resp = self._client._request(
            "put",
            url,
            params=params,
            headers=headers,
            json=body,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

    # ------------------------------------------------------------------
    def get_record_by_key_field(
        self,
        api_version: str,
        entity: str,
        key: str,
        value: str,
        options: Optional[QueryOptions] = None
    ) -> dict:
        """
        Retrieve a single record by its key fields from Acumatica ERP.

        Sends a GET request to:
            {base_url}/entity/Default/{api_version}/{entity}/{key}/{value}

        Args:
            api_version (str):
                The version of the contract-based endpoint (e.g. "24.200.001").
            entity (str):
                The name of the top-level entity to retrieve (e.g. "SalesOrder").
            key (str):
                The first key field’s value (e.g. order type “SO”).
            value (str):
                The second key field’s value (e.g. order number “000123”).
            options (QueryOptions, optional):
                Additional query parameters ($select, $expand, $custom).  
                If omitted, no query string is added.

        Returns:
            dict:
                The JSON‐decoded record returned by Acumatica.
        """

        if not self._client.persistent_login:
            self._client.login()
        if options and options.filter:
            raise ValueError(
                "QueryOptions.filter must be None; use get_records_by_filter() instead"
            )
        params = options.to_params() if options else None
        headers = {"Accept": "application/json"}
        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}/{key}/{value}"
        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

    def get_records_by_filter(
        self,
        api_version: str,
        entity: str,
        options: QueryOptions,
        show_archived: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Retrieve one or more records by filter from Acumatica ERP.

        Sends a GET request to:
            {base_url}/entity/Default/{api_version}/{entity}?{params}

        Args:
            api_version (str): Contract version, e.g. "24.200.001".
            entity (str): Top-level entity name.
            options (QueryOptions): Must have options.filter set.
            show_archived (bool): If True, include archived records via PX-ApiArchive header.

        Returns:
            List[Dict[str, Any]]: JSON-decoded records matching the filter.

        Raises:
            ValueError: If options.filter is None.
        """
        if not self._client.persistent_login:
            self._client.login()
        if not options.filter:
            raise ValueError("QueryOptions.filter must be set.")
        params = options.to_params()
        headers = {"Accept": "application/json"}
        if show_archived:
            headers["PX-ApiArchive"] = "SHOW"
        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}"
        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

    def get_record_by_id(
        self,
        api_version: str,
        entity: str,
        id: str,
        options: Optional[QueryOptions] = None
    ) -> dict:
        """
        Retrieve a single record by its id from Acumatica ERP.

        Sends a GET request to:
            {base_url}/entity/Default/{api_version}/{entity}/{id}

        Args:
            api_version (str):
                The version of the contract-based endpoint (e.g. "24.200.001").
            entity (str):
                The name of the top-level entity to retrieve (e.g. "SalesOrder").
            id (str):
                The id of the Record to retrieve (e.g. "000012")
            options (QueryOptions, optional):
                Additional query parameters ($select, $expand, $custom).  
                If omitted, no query string is added.

        Returns:
            dict:
                The JSON‐decoded record returned by Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()
        if options and options.filter:
            raise ValueError(
                "QueryOptions.filter must be None; use get_records_by_filter() instead"
            )
        params = options.to_params() if options else None
        headers = {"Accept": "application/json"}
        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}/{id}"
        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
    
    # ------------------------------------------------------------------
    def delete_record_by_key_field(
        self,
        api_version: str,
        entity: str,
        key: str,
        value: str
    ) -> None:
        """
        Remove a record by its key fields.

        Sends a DELETE request to:
            {base_url}/entity/Default/{api_version}/{entity}/{key}/{value}

        Args:
            api_version (str): Endpoint version, e.g. "24.200.001".
            entity (str): Top-level entity name, e.g. "SalesOrder".
            key (str): First key field’s value (e.g. order type "SO").
            value (str): Second key field’s value (e.g. order number "000123").
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}/{key}/{value}"
        resp = self._client._request(
            "delete",
            url,
            headers={"Accept": "application/json"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

    # ------------------------------------------------------------------
    def delete_record_by_id(
        self,
        api_version: str,
        entity: str,
        record_id: str
    ) -> None:
        """
        Remove a record by its Acumatica session identifier (entity ID).

        Sends a DELETE request to:
            {base_url}/entity/Default/{api_version}/{entity}/{record_id}

        Args:
            api_version (str): Endpoint version, e.g. "24.200.001".
            entity (str): Top-level entity name, e.g. "SalesOrder".
            record_id (str): GUID of the record to remove.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}/{record_id}"
        resp = self._client._request(
            "delete",
            url,
            headers={"Accept": "application/json"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
    
    # ------------------------------------------------------------------
    def get_custom_field_schema(
        self,
        api_version: str,
        entity: str
    ) -> dict:
        """
        Retrieves the schema of custom fields for a given entity.

        This includes user-defined fields and predefined fields not in the
        standard contract. Sends a GET request to the $adHocSchema endpoint.

        Args:
            api_version (str): The contract API version, e.g., "24.200.001".
            entity (str): The name of the entity, e.g., "StockItem".

        Returns:
            dict: The JSON schema describing the custom fields.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}/$adHocSchema"
        headers = {"Accept": "application/json"}
        resp = self._client._request(
            "get",
            url,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def request_report(
        self,
        report_entity: str,
        endpoint_name: str,
        endpoint_version: str,
        parameters: Optional[Dict[str, Any]] = None,
        output_format: Literal["PDF", "HTML", "Excel"] = "PDF",
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> "requests.Response":
        """
        Initiates a report request and polls until the report is ready.

        This method follows Acumatica's asynchronous report generation flow by
        sending a POST to a specific report endpoint.

        Args:
            report_entity (str): The entity name of the report (e.g., "CashAccountSummary").
            endpoint_name (str): The name of the custom endpoint for reports (e.g., "Report").
            endpoint_version (str): The version of the custom endpoint (e.g., "0001").
            parameters (dict, optional): Report parameters to send in the request body.
            output_format (str, optional): "PDF", "HTML", or "Excel". Defaults to "PDF".
            polling_interval_sec (int, optional): Seconds to wait between polls. Defaults to 2.
            timeout_sec (int, optional): Maximum seconds to wait. Defaults to 120.

        Returns:
            requests.Response: The final response object containing the report content.
        
        Raises:
            RuntimeError: If the report generation fails or times out.
        """
        if not self._client.persistent_login:
            self._client.login()
            
        format_map = {
            "PDF": "application/pdf",
            "HTML": "text/html",
            "Excel": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        # 1. Initial POST to start report generation
        url = f"{self._client.base_url}/entity/{endpoint_name}/{endpoint_version}/{report_entity}"
        headers = {"Accept": format_map[output_format], "Content-Type": "application/json"}
        
        initial_resp = self._client._request(
            "post",
            url,
            json=parameters or {},
            headers=headers,
            verify=self._client.verify_ssl,
        )
        
        if initial_resp.status_code != 202:
            raise RuntimeError(f"Expected status 202 to start report generation, but got {initial_resp.status_code}")

        location_url = initial_resp.headers.get("Location")
        if not location_url:
            raise RuntimeError("Acumatica did not return a Location header for the report.")

        # Ensure the location URL is absolute
        if location_url.startswith("/"):
            location_url = self._client.base_url + location_url

        # 2. Poll the Location URL until the report is ready
        start_time = time.time()
        while time.time() - start_time < timeout_sec:
            poll_resp = self._client._request(
                "get",
                location_url,
                headers=headers, # Pass the same headers
                verify=self._client.verify_ssl
            )

            if poll_resp.status_code == 200:
                if not self._client.persistent_login:
                    self._client.logout()
                return poll_resp  # Success!
            
            if poll_resp.status_code != 202:
                 _raise_with_detail(poll_resp) # Raise a detailed error for other failures

            time.sleep(polling_interval_sec)

        raise RuntimeError(f"Report generation timed out after {timeout_sec} seconds.")