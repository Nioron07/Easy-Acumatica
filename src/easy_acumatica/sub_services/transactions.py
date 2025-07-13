from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional
from datetime import datetime
from ..odata import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["TransactionsService"]


class TransactionsService:
    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client
    
    def get_ledger_transactions(
            self,
            start_date: datetime,
            end_date: datetime,
            api_version: Optional[str] = None,
            options: Optional[QueryOptions] = None,
            ):
        if not self._client.persistent_login:
            self._client.login()

        if api_version == None:
            url = f"{self._client.base_url}/entity/Default/{self._client.endpoints["Default"]['version']}/AccountDetailsForPeriodInquiry"
        else:
            url = f"{self._client.base_url}/entity/Default/{api_version}/AccountDetailsForPeriodInquiry"

        dates = {
            "FromPeriod": { "value": f"{start_date.month:02d}{start_date.year}" },
            "ToPeriod": { "value": f"{end_date.month:02d}{end_date.year}" }
        }
        print(dates)
        params = options.to_params() if options else {}
        
        # Corrected method from "get" to "put"
        resp = self._client._request("put", url, json=dates, params=params, verify=self._client.verify_ssl)
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()

