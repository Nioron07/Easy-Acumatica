from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict, Union
import time

from ..models.record_builder import RecordBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ActionsService"]


class ActionsService:
    """
    A sub-service for executing standard and custom actions on Acumatica entities.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the ActionsService with an active client session."""
        self._client = client

    def execute_action(
        self,
        api_version: str,
        entity_name: str,
        action_name: str,
        entity: Union[dict, RecordBuilder],
        parameters: Optional[Dict[str, Any]] = None,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Executes a standard action on a specific entity record.

        This method handles the asynchronous workflow by polling for completion
        if the server returns a 202 Accepted status.

        Args:
            api_version: The contract API version (e.g., "24.200.001").
            entity_name: The name of the top-level entity (e.g., "SalesOrder").
            action_name: The name of the action to execute (e.g., "ReopenSalesOrder").
            entity: A dict or RecordBuilder identifying the record for the action.
            parameters: An optional dictionary of simple parameters for the action.
            polling_interval_sec: Seconds to wait between polling attempts. Defaults to 2.
            timeout_sec: Maximum seconds to wait for the action to complete. Defaults to 120.

        Raises:
            RuntimeError: If the action fails or times out.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity_name}/{action_name}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        # Format the entity and parameters into the required request body structure
        entity_payload = entity.build() if isinstance(entity, RecordBuilder) else entity
        params_payload = {key: {"value": value} for key, value in (parameters or {}).items()}
        
        body = {
            "entity": entity_payload,
            "parameters": params_payload
        }

        self._execute_and_poll(url, headers, body, action_name, polling_interval_sec, timeout_sec)

    def execute_custom_action(
        self,
        api_version: str,
        entity_name: str,
        action_name: str,
        entity: Union[dict, RecordBuilder],
        custom_parameters: Dict[str, Any],
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Executes a custom action that requires complex, nested parameters.

        This is used for actions that open a dialog box in the UI.

        Args:
            api_version: The contract API version.
            entity_name: The name of the top-level entity (e.g., "Case").
            action_name: The name of the custom action to execute (e.g., "Close").
            entity: A dict or RecordBuilder identifying the record.
            custom_parameters: A dictionary representing the nested custom parameters,
                             including the view and field names.
            polling_interval_sec: Seconds to wait between polling attempts.
            timeout_sec: Maximum seconds to wait for completion.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/{entity_name}/{action_name}"
        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        entity_payload = entity.build() if isinstance(entity, RecordBuilder) else entity
        
        # Build the specific nested structure for custom action parameters
        body = {
            "entity": entity_payload,
            "parameters": {
                "custom": custom_parameters
            }
        }

        self._execute_and_poll(url, headers, body, action_name, polling_interval_sec, timeout_sec)

    def _execute_and_poll(
        self,
        url: str,
        headers: Dict[str, str],
        body: Dict[str, Any],
        action_name: str,
        polling_interval_sec: int,
        timeout_sec: int,
    ) -> None:
        """Internal helper to perform the POST and poll for completion."""
        
        # 1. Initial POST to start the action
        initial_resp = self._client._request(
            "post",
            url,
            json=body,
            headers=headers,
            verify=self._client.verify_ssl,
        )

        # If 204, the action was synchronous and is already complete
        if initial_resp.status_code == 204:
            if not self._client.persistent_login:
                self._client.logout()
            return

        # If 202, the action is asynchronous, and we need to poll
        if initial_resp.status_code == 202:
            location_url = initial_resp.headers.get("Location")
            if not location_url:
                raise RuntimeError("Acumatica did not return a Location header for the action.")

            if location_url.startswith("/"):
                location_url = self._client.base_url + location_url

            # 2. Poll the Location URL until the action is complete
            start_time = time.time()
            while time.time() - start_time < timeout_sec:
                poll_resp = self._client._request(
                    "get",
                    location_url,
                    headers=headers,
                    verify=self._client.verify_ssl
                )

                if poll_resp.status_code == 204: # Action is complete
                    if not self._client.persistent_login:
                        self._client.logout()
                    return

                if poll_resp.status_code != 202:
                    _raise_with_detail(poll_resp)

                time.sleep(polling_interval_sec)
            
            raise RuntimeError(f"Action '{action_name}' timed out after {timeout_sec} seconds.")

        # Handle any other unexpected status codes
        _raise_with_detail(initial_resp)
