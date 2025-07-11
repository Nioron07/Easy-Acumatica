# src/easy_acumatica/sub_services/business_accounts.py

from __future__ import annotations
from typing import TYPE_CHECKING, Optional, Any
from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient


class BusinessAccountsService:
    """Sub-service for retrieving Business Accounts
    
    Reminder: there is currently no param to filter in a business id and return a specific business, if you need to do so please
    use the QueryOptions and filter based upon BusinessAccountID
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    def get_business_accounts(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieves the list of business accounts using the BusinessAccount endpoint.

        Reminder: there is currently no param to filter in a business id and return a specific business, if you need to do so please
        use the QueryOptions and filter based upon BusinessAccountID
        """

        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/BusinessAccount"
        params = options.to_params() if options else None
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

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
