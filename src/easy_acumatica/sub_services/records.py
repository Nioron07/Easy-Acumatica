# services/records.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union, List, Dict

from ..models.record_builder import RecordBuilder
from ..models.filter_builder import QueryOptions
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
        url = (
            f"{self._client.base_url}/entity/Default/"
            f"{api_version}/{entity}"
        )

        params = options.to_params() if options else None
        headers = {
            "If-None-Match": "*",            # ← asterisk enforces create-only
            "Accept": "application/json",    # good practice, though optional
        }
        body = record.build() if isinstance(record, RecordBuilder) else record

        resp = self._client.session.put(
            url,
            params=params,
            headers=headers,
            json=body,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
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
        url = (
            f"{self._client.base_url}/entity/Default/"
            f"{api_version}/{entity}"
        )

        params = options.to_params() if options else None
        headers = {
            "If-Match": "*",            # ← asterisk enforces create-only
            "Accept": "application/json",    # good practice, though optional
        }
        body = record.build() if isinstance(record, RecordBuilder) else record

        resp = self._client.session.put(
            url,
            params=params,
            headers=headers,
            json=body,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
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

        # ensure no filter was provided
        if options and options.filter:
            raise ValueError(
                "QueryOptions.filter must be None otherwise the endpoint will not function as intended. "
                "If you mean to retrieve records based on a $filter please use the get_records_by_filter() function"
            )
        params = options.to_params() if options else None

        headers = {
            "Accept": "application/json",    # specify JSON response
        }

        url = (
            f"{self._client.base_url}/entity/Default/"
            f"{api_version}/{entity}/{key}/{value}"
        )

        resp = self._client.session.get(
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
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
        if not options.filter:
            raise ValueError("QueryOptions.filter must be set to an OData filter.")

        params = options.to_params()
        headers: Dict[str, str] = {"Accept": "application/json"}
        if show_archived:
            headers["PX-ApiArchive"] = "SHOW"

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity}"

        resp = self._client.session.get(
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
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

        # ensure no filter was provided
        if options and options.filter:
            raise ValueError(
                "QueryOptions.filter must be None otherwise the endpoint will not function as intended. "
                "If you mean to retrieve records based on a $filter please use the get_records_by_filter() function"
            )
        params = options.to_params() if options else None

        headers = {
            "Accept": "application/json",    # specify JSON response
        }

        url = (
            f"{self._client.base_url}/entity/Default/"
            f"{api_version}/{entity}/{id}"
        )

        resp = self._client.session.get(
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
        return resp.json()
