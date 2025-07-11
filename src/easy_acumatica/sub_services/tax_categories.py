# src/easy_acumatica/sub_services/tax_category.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.tax_category_builder import TaxCategoryBuilder
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["TaxCategoryService"]


class TaxCategoryService:
    """Sub-service for managing Tax Categories."""

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def update_tax_category(
        self,
        api_version: str,
        builder: TaxCategoryBuilder,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Create a new tax category.

        Sends a PUT request to the /TaxCategory endpoint.

        Parameters
        ----------
        api_version : str
            The API version segment (e.g., '24.200.001').
        builder : TaxCategoryBuilder
            A fluent builder instance containing the tax category details.

        Returns
        -------
        Any
            The parsed JSON body of the response from Acumatica.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/TaxCategory"
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
