# src/easy_acumatica/contacts.py
from typing import Any, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .client import AcumaticaClient

class ContactsService:
    def __init__(self, client: "AcumaticaClient"):
        self._client = client

    def get_contacts(self, api_version: str, params: Optional[Dict[str, Any]] = None) -> Any:
        # 1) This will now raise if login fails
        self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        resp = self._client.session.get(
            url,
            params=params,
            verify=self._client.verify_ssl
        )
        # this will raise if the GET is 4xx/5xx
        resp.raise_for_status()

        self._client.logout()
        return resp.json()
