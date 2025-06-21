# services/inquiries.py
from __future__ import annotations

from typing import TYPE_CHECKING, Any, Optional, List, Dict

from ..models.inquiry_builder import InquiryBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:                                       # pragma: no cover
    from ..client import AcumaticaClient


class InquiriesService:

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_data_from_inquiry_form(
        self,
        api_version: str,
        inquiry: str,
        opts: InquiryBuilder
    ) -> List[Dict[str, Any]]:
        """
        Execute a generic inquiry via PUT and return its Results.

        Constructs and sends a PUT request to:
            {base_url}/entity/Default/{api_version}/{inquiry}?{query_params}

        The request body is the JSON parameters built by InquiryBuilder.

        Args:
            api_version (str): Contract-based endpoint version (e.g. '24.200.001').
            inquiry (str): Name of the inquiry endpoint (e.g. 'InventorySummaryInquiry').
            opts (InquiryBuilder): Builder containing parameters and expand clauses.

        Returns:
            List[Dict[str, Any]]: The array under the 'Results' key, or the full body if absent.

        Raises:
            AcumaticaError: On non-200 HTTP status (_raise_with_detail raises).

        Example:
            >>> opts = (
            ...     InquiryBuilder()
            ...     .param('InventoryID', 'SIMCARD')
            ...     .param('WarehouseID', 'YOGI')
            ...     .expand('Results')
            ... )
            >>> rows = client.inquiries.get_inquiry_results(
            ...     '24.200.001',
            ...     'InventorySummaryInquiry',
            ...     opts
            ... )
            >>> for r in rows:
            ...     print(r['InventoryID'], r['AvailableQty'])
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{inquiry}"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        resp = self._client._request(
            "put",
            url,
            params=opts.to_query_params(),
            json=opts.to_body(),
            headers=headers,
            verify=self._client.verify_ssl,
        )

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def execute_generic_inquiry(
        self,
        inquiry_title: str,
        opts: Optional[QueryOptions] = None
    ) -> Any:
        """
        Execute an OData Generic Inquiry via the OData endpoint using QueryOptions.

        Sends a GET request to:
            {base_url}/t/{tenant}/api/odata/gi/{inquiry_title}?{params}

        Args:
            inquiry_title (str): Name of the generic inquiry (case-sensitive).
            opts (QueryOptions, optional): Fluent query options. If provided,
                its `to_params()` dict will be used as the OData query parameters.

        Returns:
            Any: The parsed JSON response from the OData inquiry.

        Raises:
            AcumaticaError: On non-200 HTTP status (_raise_with_detail raises).

        Example:
            >>> qopts = QueryOptions(filter="Status eq 'Active'", top=10)
            >>> data = client.inquiries.execute_generic_inquiry(
            ...     "PEAllParts", qopts
            ... )
            >>> for item in data.get("value", []):
            ...     print(item["InventoryID"])
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/{inquiry_title}"
        headers = {"Accept": "application/json"}
        params = opts.to_params() if opts else None

        resp = self._client._request(
            "get",
            url,
            params=params,
            headers=headers,
            verify=self._client.verify_ssl,
            auth=(self._client.username, self._client.password),
        )

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()