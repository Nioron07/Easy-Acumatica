# services/records.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union, List, Dict

from ..models.record_builder import RecordBuilder
from ..models.query_builder import QueryOptions
from ..sub_services.contacts import _raise_with_detail   # reuse your shared helper

if TYPE_CHECKING:                                       # pragma: no cover
    from ..client import AcumaticaClient


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
        headers = {"If-None-Match": "*", "Accept": "application/json"}
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

        Returns
        -------
        Any
            JSON representation of the updated record (server response).
        """
        if not self._client.persistent_login:
            self._client.login()
        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}"
        params = options.to_params() if options else None
        headers = {"If-Match": "*", "Accept": "application/json"}
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
    ):
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

        Raises:
            AcumaticaError:
                If the HTTP response status is not 200, 
                `_raise_with_detail` will raise with response details.

        HTTP Status Codes:
            200: Successful retrieval; JSON body contains the record.
            401: Unauthorized – client is not authenticated.
            403: Forbidden – insufficient rights to the entity/form.
            429: Too Many Requests – license request limit exceeded.
            500: Internal Server Error.

        Example:
            >>> opts = QueryOptions().select("OrderNbr", "Status").expand("Details")
            >>> rec = client.get_record_by_key_field(
            ...     "24.200.001", "SalesOrder", "SO", "000123", opts
            ... )
            >>> print(rec["OrderNbr"], rec["Status"])
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
    ):
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

        Raises:
            AcumaticaError:
                If the HTTP response status is not 200, 
                `_raise_with_detail` will raise with response details.

        HTTP Status Codes:
            200: Successful retrieval; JSON body contains the record.
            401: Unauthorized – client is not authenticated.
            403: Forbidden – insufficient rights to the entity/form.
            429: Too Many Requests – license request limit exceeded.
            500: Internal Server Error.

        Example:
            >>> opts = QueryOptions().select("OrderNbr", "Status").expand("Details")
            >>> rec = client.get_record_by_id(
            ...     "24.200.001", "SalesOrder", "000012", opts
            ... )
            >>> print(rec["OrderNbr"], rec["Status"])
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

        No query parameters or body are required.

        Args:
            api_version (str): Endpoint version, e.g. "24.200.001".
            entity (str): Top-level entity name, e.g. "SalesOrder".
            key (str): First key field’s value (e.g. order type "SO").
            value (str): Second key field’s value (e.g. order number "000123").

        Returns:
            None

        Raises:
            AcumaticaError (RuntimeError):
                If the HTTP response status is not 204, with detailed error
                text extracted by `_raise_with_detail`.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = (
            f"{self._client.base_url}"
            f"/entity/Default/{api_version}/{entity}/{key}/{value}"
        )
        # perform the DELETE; will raise on non-2xx
        resp = self._client._request(
            "delete",
            url,
            headers={"Accept": "application/json"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        # DELETE returns 204 No Content on success; we return None


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

        No query parameters or body are required.

        Args:
            api_version (str): Endpoint version, e.g. "24.200.001".
            entity (str): Top-level entity name, e.g. "SalesOrder".
            record_id (str): GUID of the record to remove.

        Raises:
            RuntimeError: If the HTTP response status is not 204,
                          `_raise_with_detail` will raise with details.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = (
            f"{self._client.base_url}"
            f"/entity/Default/{api_version}/{entity}/{record_id}"
        )
        resp = self._client._request(
            "delete",
            url,
            headers={"Accept": "application/json"},
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        # on 204 No Content, simply return None
