# services/records_service.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, Union

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


    # inside RecordsService
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
