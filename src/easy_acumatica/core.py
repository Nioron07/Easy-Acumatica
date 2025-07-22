# src/easy_acumatica/core.py

from __future__ import annotations

from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import requests

from .helpers import _raise_with_detail
from .odata import QueryOptions

if TYPE_CHECKING:
    from .client import AcumaticaClient

class BaseDataClassModel:
    """
    A base for all Acumatica data models, providing a method to
    convert a dataclass into the required API payload format.
    """
    def to_acumatica_payload(self) -> Dict[str, Any]:
        """
        Converts the dataclass instance into the JSON format required
        by the Acumatica API.
        """
        if not is_dataclass(self):
            raise TypeError("to_acumatica_payload can only be called on a dataclass instance.")

        payload = {}
        for f in fields(self):
            value = getattr(self, f.name)
            if value is None:
                continue

            if isinstance(value, list):
                payload[f.name] = [
                    item.to_acumatica_payload() if isinstance(item, BaseDataClassModel) else item
                    for item in value
                ]
            elif isinstance(value, BaseDataClassModel):
                payload[f.name] = value.to_acumatica_payload()
            elif isinstance(value, dict):
                payload[f.name] = value
            else:
                payload[f.name] = {"value": value}

        return payload

    def build(self) -> Dict[str, Any]:
        """Alias for to_acumatica_payload for backward compatibility."""
        return self.to_acumatica_payload()


class BaseService:
    """
    A base service that handles common API request logic, including
    authentication, URL construction, and response handling.
    """
    def __init__(self, client: AcumaticaClient, entity_name: str, endpoint_name: str = "Default"):
        self._client = client
        self.entity_name = entity_name
        self.endpoint_name = endpoint_name

    def _get_url(self, api_version: Optional[str] = None) -> str:
        """Constructs the base URL for the service's entity."""
        version = api_version or self._client.endpoints[self.endpoint_name]['version']
        if not version:
            raise ValueError(f"API version for endpoint '{self.endpoint_name}' is not available.")
        return f"{self._client.base_url}/entity/{self.endpoint_name}/{version}/{self.entity_name}"

    def _get_schema(self, api_version: Optional[str] = None) -> Any:
        """
        Gets the $adHocSchema of the current service
        """
        url = f"{self._get_url(api_version)}/$adHocSchema"
        return self._request("get", url, verify=self._client.verify_ssl)

    def _request(self, method: str, url: str, **kwargs) -> Any:
        """
        Makes an API request, handling the login/logout lifecycle if needed.
        """
        if not self._client.persistent_login:
            self._client.login()

        # Add a default timeout to all requests to prevent freezing
        kwargs.setdefault('timeout', 60)

        resp = self._client._request(method, url, **kwargs)
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        if resp.status_code == 204:
            return None

        # Safely handle responses that may not have a JSON body
        if resp.text:
            try:
                return resp.json()
            except Exception:
                return resp.text
        return None

    def _get(
        self,
        entity_id: str | None = None,
        options: QueryOptions | None = None,
        api_version: Optional[str] = None
    ) -> Any:
        """Performs a GET request."""
        url = self._get_url(api_version)

        if entity_id:
            keys = ",".join(map(str, entity_id)) if isinstance(entity_id, list) else entity_id
            url = f"{url}/{keys}"

        params = options.to_params() if options else None

        return self._request("get", url, params=params)

    def _put(
        self,
        data: Any,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """Performs a PUT request."""
        url = self._get_url(api_version)
        params = options.to_params() if options else None
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        if isinstance(data, BaseDataClassModel):
            json_data = data.to_acumatica_payload()
        else:
            json_data = data

        return self._request("put", url, params=params, json=json_data, headers=headers, verify=self._client.verify_ssl)

    def _post_action(
        self,
        action_name: str,
        entity_payload: Dict[str, Any],
        api_version: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
    ) -> Any:
        """Performs a POST request for a specific action."""
        url = f"{self._get_url(api_version)}/{action_name}"

        body = {"entity": entity_payload}
        if parameters:
            body["parameters"] = {key: {"value": value} for key, value in parameters.items()}

        headers = {"Accept": "application/json", "Content-Type": "application/json"}
        return self._request("post", url, json=body, headers=headers, verify=self._client.verify_ssl)

    def _delete(self, entity_id: str, api_version: Optional[str] = None) -> None:
        """
        Performs a DELETE request for a specific entity ID.
        """
        url = f"{self._get_url(api_version)}/{entity_id}"
        self._request("delete", url, verify=self._client.verify_ssl)

    def _put_file(
        self,
        entity_id: str,
        filename: str,
        data: bytes,
        api_version: Optional[str] = None,
        comment: Optional[str] = None
    ) -> None:
        """Performs a PUT request to attach a file."""
        # First, get the record to find the file attachment URL
        record = self._get(entity_id=entity_id, api_version=api_version)

        # Extract the file upload URL from the _links section
        try:
            upload_url_template = record['_links']['files:put']
        except KeyError:
            raise ValueError("Could not find file upload URL in the record's _links. Make sure the entity supports file attachments.")

        # The full URL for the request, replacing the {filename} placeholder
        upload_url = f"{self._client.base_url}{upload_url_template.replace('{filename}', filename)}"

        headers = {"Accept": "application/json", "Content-Type": "application/octet-stream"}
        if comment:
            headers["PX-CbFileComment"] = comment

        self._request("put", upload_url, headers=headers, data=data, verify=self._client.verify_ssl)

    def _get_files(
        self,
        entity_id: str,
        api_version: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieves files attached to a specific entity."""
        options = QueryOptions(expand=["files"], select=["files"])

        record = self._get(entity_id=entity_id, options=options, api_version=api_version)
        return record.get("files", [])
    
    def _get_inquiry(self, inquiry_name: str, options: QueryOptions | None = None) -> Any:
        """
        A generic method in BaseService to fetch data for any given inquiry.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/{inquiry_name}"
        params = options.to_params() if options else None
        
        response = requests.get(url=url, auth=(self._client.username, self._client._password), params=params)
        
        response.raise_for_status() # Or your custom error handling

        if not self._client.persistent_login:
            self._client.logout()

        return response.json()
