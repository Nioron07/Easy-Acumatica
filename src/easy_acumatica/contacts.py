# src/easy_acumatica/contacts.py
from typing import Any, TYPE_CHECKING
from .filters import QueryOptions

if TYPE_CHECKING:
    from .client import AcumaticaClient

class ContactsService:
    def __init__(self, client: "AcumaticaClient"):
        self._client = client

    def get_contacts(
        self,
        api_version: str,
        options: QueryOptions = None
    ) -> Any:

        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        params = options.to_params() if options else None

        resp = self._client.session.get(
            url, params=params, verify=self._client.verify_ssl
        )
        resp.raise_for_status()
        return resp.json()
