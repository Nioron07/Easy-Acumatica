from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict, Union
import time

from ..core import BaseService
from ..builders import RecordBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ActionsService"]


class ActionsService(BaseService):
    """
    A sub-service for executing standard and custom actions on Acumatica entities.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the ActionsService with an active client session."""
        # This service is entity-agnostic, so we pass an empty entity_name
        super().__init__(client, entity_name="")

    def get_schema(self, entity_name: str, api_version: Optional[str] = None) -> Any:
        """
        Retrieves the swagger schema for a given entity endpoint.
        
        Since ActionsService can operate on any entity, you must specify which
        entity's schema you want to retrieve.
        """
        # Temporarily set entity_name to get the schema for the correct entity
        original_entity = self.entity_name
        self.entity_name = entity_name
        try:
            # The actual request is handled by the base class method
            return self._get_schema(api_version=api_version)
        finally:
            # Restore the original entity name
            self.entity_name = original_entity

    def execute_action(
        self,
        entity_name: str,
        action_name: str,
        entity: Union[dict, RecordBuilder],
        api_version: Optional[str] = None,
        parameters: Optional[Dict[str, Any]] = None,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Executes a standard action on a specific entity record.
        """
        entity_payload = entity.build() if isinstance(entity, RecordBuilder) else entity
        params_payload = {key: {"value": value} for key, value in (parameters or {}).items()}

        body = {
            "entity": entity_payload,
            "parameters": params_payload
        }

        self._execute_and_poll(entity_name, action_name, body, api_version, polling_interval_sec, timeout_sec)

    def execute_custom_action(
        self,
        entity_name: str,
        action_name: str,
        entity: Union[dict, RecordBuilder],
        custom_parameters: Dict[str, Any],
        api_version: Optional[str] = None,
        polling_interval_sec: int = 2,
        timeout_sec: int = 120,
    ) -> None:
        """
        Executes a custom action that requires complex, nested parameters.
        """
        entity_payload = entity.build() if isinstance(entity, RecordBuilder) else entity

        body = {
            "entity": entity_payload,
            "parameters": {
                "custom": custom_parameters
            }
        }

        self._execute_and_poll(entity_name, action_name, body, api_version, polling_interval_sec, timeout_sec)

    def _execute_and_poll(
        self,
        entity_name: str,
        action_name: str,
        body: Dict[str, Any],
        api_version: Optional[str],
        polling_interval_sec: int,
        timeout_sec: int,
    ) -> None:
        """Internal helper to perform the POST and poll for completion."""
        if not self._client.persistent_login:
            self._client.login()

        # Temporarily set entity_name for URL construction in the base class
        original_entity = self.entity_name
        self.entity_name = entity_name
        try:
            url = f"{self._get_url(api_version)}/{action_name}"
        finally:
            self.entity_name = original_entity

        headers = {"Accept": "application/json", "Content-Type": "application/json"}

        try:
            # 1. Initial POST to start the action
            # We use the raw _request from the client to avoid repeated login/logout during polling
            initial_resp = self._client._request(
                "post",
                url,
                json=body,
                headers=headers,
                verify=self._client.verify_ssl,
            )

            if initial_resp.status_code == 204:
                return

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

                    if poll_resp.status_code == 204:
                        return

                    if poll_resp.status_code != 202:
                        _raise_with_detail(poll_resp)

                    time.sleep(polling_interval_sec)

                raise RuntimeError(f"Action '{action_name}' timed out after {timeout_sec} seconds.")

            _raise_with_detail(initial_resp)

        finally:
            # Ensure logout happens if we're not using persistent sessions
            if not self._client.persistent_login:
                self._client.logout()