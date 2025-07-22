from __future__ import annotations

from typing import Any, Optional

import requests

from easy_acumatica.client import AcumaticaClient
from easy_acumatica.helpers import _raise_with_detail
from easy_acumatica.odata import QueryOptions


class GenericInquiries:
    """Custom Sub-service for managing generic inquiries"""

    def __init__(self, client: AcumaticaClient) -> None:
        self._client = client

    def _get(
        self,
        inquiry_name: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/{inquiry_name}"
        self._client.login()
        params = options.to_params() if options else None

        response = requests.get(url=url, auth=(self._client.username, self._client._password), params=params)
        _raise_with_detail(response)

        if not self._client.persistent_login:
            self._client.logout()

        return response.json()

