# src/easy_acumatica/core.py

from __future__ import annotations

import logging
from dataclasses import fields, is_dataclass
from typing import TYPE_CHECKING, Any, Dict, List, Optional
import requests

from .helpers import _raise_with_detail
from .exceptions import AcumaticaValidationError, AcumaticaSchemaError, AcumaticaError
from .odata import QueryOptions

logger = logging.getLogger(__name__)

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
            raise AcumaticaValidationError(
                "to_acumatica_payload can only be called on a dataclass instance.",
                suggestions=["Ensure this method is called on a dataclass model instance"]
            )

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


class BatchMethodWrapper:
    """
    Wrapper that adds batch calling capability to service methods.
    
    This allows methods to be called normally or used in batch operations
    by accessing the .batch property.
    """
    
    def __init__(self, method, service_instance):
        self.method = method
        self.service_instance = service_instance
        self.__name__ = getattr(method, '__name__', 'unknown')
        self.__doc__ = getattr(method, '__doc__', None)
    
    def __call__(self, *args, **kwargs):
        """Normal method call - execute immediately."""
        return self.method(*args, **kwargs)
    
    @property
    def batch(self):
        """Return a callable that creates a CallableWrapper for batch execution."""
        def create_wrapper(*args, **kwargs):
            from .batch import CallableWrapper
            return CallableWrapper(self.method, *args, **kwargs)
        return create_wrapper
    
    def __get__(self, instance, owner):
        if instance is None:
            return self
        # Return a bound version of this wrapper
        bound_method = self.method.__get__(instance, owner)
        return BatchMethodWrapper(bound_method, instance)


class BaseService:
    """
    A base service that handles common API request logic, including
    authentication, URL construction, and response handling.
    
    All public methods automatically support batch calling via the .batch property.
    """
    def __init__(self, client: AcumaticaClient, entity_name: str, endpoint_name: Optional[str] = None):
        self._client = client
        self.entity_name = entity_name
        # Use the provided endpoint_name, or fall back to the client's configured endpoint
        self.endpoint_name = endpoint_name or client.endpoint_name

    def _get_url(self, api_version: Optional[str] = None) -> str:
        """Constructs the base URL for the service's entity."""
        version = api_version or self._client.endpoint_version or self._client.endpoints[self.endpoint_name]['version']
        if not version:
            raise AcumaticaSchemaError(
                f"API version for endpoint '{self.endpoint_name}' is not available.",
                endpoint=self.endpoint_name,
                suggestions=[
                    "Check if the endpoint name is correct",
                    "Verify the API version is set",
                    "Ensure the endpoint exists in your Acumatica instance"
                ]
            )
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

        try:
            resp = self._client._request(method, url, **kwargs)
            _raise_with_detail(
                resp,
                operation=f"{method}_{self.entity_name}",
                entity=self.entity_name,
                request_data=kwargs.get('json'),
            )
        finally:
            # Always log out non-persistent sessions, even when the request
            # failed. Without this, error paths leak an authenticated
            # session for the lifetime of the client.
            if not self._client.persistent_login:
                try:
                    self._client.logout()
                except Exception as logout_err:
                    logger.debug(f"logout after error failed: {logout_err}")

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
    
    def _get_by_keys(
        self,
        key_fields: Dict[str, Any],
        options: QueryOptions | None = None,
        api_version: Optional[str] = None
    ) -> Any:
        """
        Performs a GET request using key field values in the URL path.
        According to Acumatica REST API docs, key values should be in the URL path:
        http://<base>/<entity>/<key1>/<key2>/...
        """
        url = self._get_url(api_version)
        
        # Build URL with key values in path
        # Convert key field values to URL path segments
        key_values = []
        for key, value in key_fields.items():
            # Convert value to string, handling None values
            if value is None:
                raise AcumaticaValidationError(
                    f"Key field '{key}' cannot be None",
                    field_errors={key: "Value cannot be None"},
                    entity=self.entity_name
                )
            key_values.append(str(value))
        
        # Append key values to URL as path segments
        if key_values:
            key_path = "/".join(key_values)
            url = f"{url}/{key_path}"
        
        params = options.to_params() if options else None
        return self._request("get", url, params=params)

    def _put_custom_endpoint(
        self,
        data: dict,
        options: QueryOptions | None = None,
        api_version: Optional[str] = None
    ) -> Any:
        """
        Performs a PUT request for custom endpoints (Generic Inquiries).

        Custom endpoints require a PUT request with an empty body and $expand=Results
        to retrieve the inquiry data.
        """
        url = self._get_url(api_version)
        params = options.to_params() if options else None

        return self._request("put", url, params=params, json=data)
    
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
            raise AcumaticaError(
                "Could not find file upload URL in the record's _links. Make sure the entity supports file attachments.",
                entity=self.entity_name,
                entity_id=entity_id,
                suggestions=[
                    "Verify this entity type supports file attachments",
                    "Ensure the record exists and is accessible",
                    "Check that you have permission to attach files"
                ]
            )

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
        from .exceptions import (
            AcumaticaConnectionError,
            AcumaticaError,
            AcumaticaTimeoutError,
        )

        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/t/{self._client.tenant}/api/odata/gi/{inquiry_name}"
        params = options.to_params() if options else None

        try:
            try:
                response = requests.get(
                    url=url,
                    auth=(self._client.username, self._client._password),
                    params=params,
                    timeout=self._client.timeout,
                    verify=self._client.verify_ssl,
                )
            except requests.exceptions.Timeout as e:
                raise AcumaticaTimeoutError(
                    f"Timed out fetching inquiry '{inquiry_name}': {e}",
                    operation="get_inquiry",
                    entity=inquiry_name,
                ) from e
            except requests.exceptions.ConnectionError as e:
                raise AcumaticaConnectionError(
                    f"Connection error fetching inquiry '{inquiry_name}': {e}",
                    operation="get_inquiry",
                    entity=inquiry_name,
                ) from e
            except requests.exceptions.RequestException as e:
                raise AcumaticaConnectionError(
                    f"Request failed for inquiry '{inquiry_name}': {e}",
                    operation="get_inquiry",
                    entity=inquiry_name,
                ) from e
        finally:
            if not self._client.persistent_login:
                # Best-effort logout even if the request raised before we
                # could process the response.
                try:
                    self._client.logout()
                except Exception:
                    pass

        # 403 on this endpoint almost always means the inquiry exists in the
        # tenant's metadata but does not have "Expose via OData" checked on
        # the Generic Inquiry form (SM208000). The metadata document still
        # lists it, so it shows up in client.list_inquiries(), but calling it
        # is rejected. Surface a targeted explanation rather than a bare
        # HTTP 403 traceback.
        if response.status_code == 403:
            raise AcumaticaError(
                (
                    f"Generic Inquiry '{inquiry_name}' is not exposed via OData. "
                    f"Acumatica returned 403 Forbidden for {url}."
                ),
                status_code=403,
                operation="get_inquiry",
                entity=inquiry_name,
                suggestions=[
                    "Open the inquiry in Acumatica (form SM208000), tick "
                    "'Expose via OData' on the results grid header, and save.",
                    "If you only need the data programmatically, the inquiry "
                    "can also be invoked via the contract-based REST endpoint.",
                    "Confirm the signed-in user has the role/access rights "
                    "required to run this inquiry.",
                ],
            )

        if response.status_code == 404:
            raise AcumaticaError(
                (
                    f"Generic Inquiry '{inquiry_name}' was not found at {url}. "
                    "It may have been renamed or removed since the metadata "
                    "cache was last refreshed."
                ),
                status_code=404,
                operation="get_inquiry",
                entity=inquiry_name,
                suggestions=[
                    "Run client.refresh_schema() to rebuild the inquiry list.",
                    "Verify the inquiry name on the Generic Inquiry form (SM208000).",
                ],
            )

        # All other non-2xx responses go through the shared error path so
        # they get parsed into a typed AcumaticaError with body details.
        if not response.ok:
            _raise_with_detail(
                response,
                operation="get_inquiry",
                entity=inquiry_name,
            )

        return response.json()