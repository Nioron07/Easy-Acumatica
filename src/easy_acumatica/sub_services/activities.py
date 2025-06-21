from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict, Union

from ..models.record_builder import RecordBuilder
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ActivitiesService"]


class ActivitiesService:
    """
    A sub-service for creating and managing activities, such as notes,
    tasks, and events, and linking them to other Acumatica entities.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the ActivitiesService with an active client session."""
        self._client = client

    def _create_linked_activity(
        self,
        api_version: str,
        related_entity_note_id: str,
        related_entity_type: str,
        summary: str,
        details: str,
        activity_type: str = "M"
    ) -> Dict[str, Any]:
        """Internal helper to create an activity linked to any entity."""
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Activity"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Construct the specific payload required to link the activity
        payload = {
            "Summary": {"value": summary},
            "Type": {"value": activity_type},
            "ActivityDetails": {"value": details},
            "RelatedEntityNoteID": {"value": related_entity_note_id},
            "RelatedEntityType": {"value": related_entity_type},
        }

        resp = self._client._request(
            "put",
            url,
            headers=headers,
            json=payload,
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()

        return resp.json()

    def create_activity_linked_to_case(
        self,
        api_version: str,
        case_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M"
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific case.

        Args:
            api_version: The contract API version (e.g., "24.200.001").
            case_note_id: The NoteID (GUID) of the case to link the activity to.
            summary: A brief summary of the activity.
            details: The main content or body of the activity.
            activity_type: The type of activity. Defaults to "M" (Note).

        Returns:
            A dictionary representing the newly created Activity record.
        """
        return self._create_linked_activity(
            api_version=api_version,
            related_entity_note_id=case_note_id,
            related_entity_type="PX.Objects.CR.CRCase",
            summary=summary,
            details=details,
            activity_type=activity_type,
        )

    def create_activity_linked_to_customer(
        self,
        api_version: str,
        customer_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M"
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific customer.

        Args:
            api_version: The contract API version (e.g., "24.200.001").
            customer_note_id: The NoteID (GUID) of the customer to link the activity to.
            summary: A brief summary of the activity.
            details: The main content or body of the activity.
            activity_type: The type of activity. Defaults to "M" (Note).

        Returns:
            A dictionary representing the newly created Activity record.
        """
        return self._create_linked_activity(
            api_version=api_version,
            related_entity_note_id=customer_note_id,
            related_entity_type="PX.Objects.AR.Customer",
            summary=summary,
            details=details,
            activity_type=activity_type,
        )

    def create_activity_linked_to_lead(
        self,
        api_version: str,
        lead_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M"
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific lead.

        Args:
            api_version: The contract API version (e.g., "24.200.001").
            lead_note_id: The NoteID (GUID) of the lead to link the activity to.
            summary: A brief summary of the activity.
            details: The main content or body of the activity.
            activity_type: The type of activity. Defaults to "M" (Note).

        Returns:
            A dictionary representing the newly created Activity record.
        """
        return self._create_linked_activity(
            api_version=api_version,
            related_entity_note_id=lead_note_id,
            related_entity_type="PX.Objects.CR.CRLead",
            summary=summary,
            details=details,
            activity_type=activity_type,
        )
