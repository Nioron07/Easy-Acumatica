from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Dict

from ..core import BaseService
from ..odata import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ActivitiesService"]


class ActivitiesService(BaseService):
    """
    A sub-service for creating and managing activities, such as notes,
    tasks, and events, and linking them to other Acumatica entities.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the ActivitiesService with an active client session."""
        super().__init__(client, "Activity")

    def get_schema(self, api_version: Optional[str] = None) -> Any:
        """
        Retrieves the swagger schema for the Activity endpoint.
        """
        return self._get_schema(api_version=api_version)
        
    def get_activities(
        self,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """
        Retrieve a list of Activities, optionally filtered.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            options: An optional QueryOptions object to filter, select, expand,
                     or paginate the results.

        Returns:
            A list of dictionaries, where each dictionary is an Activity record.
        """
        return self._get(api_version, options=options)

    def _create_linked_activity(
        self,
        related_entity_note_id: str,
        related_entity_type: str,
        summary: str,
        details: str,
        activity_type: str = "M",
        api_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """Internal helper to create an activity linked to any entity."""
        payload = {
            "Summary": {"value": summary},
            "Type": {"value": activity_type},
            "ActivityDetails": {"value": details},
            "RelatedEntityNoteID": {"value": related_entity_note_id},
            "RelatedEntityType": {"value": related_entity_type},
        }
        return self._put(payload, api_version)

    def create_activity_linked_to_case(
        self,
        case_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M",
        api_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific case.
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
        customer_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M",
        api_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific customer.
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
        lead_note_id: str,
        summary: str,
        details: str,
        activity_type: str = "M",
        api_version: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Creates a new activity and links it to a specific lead.
        """
        return self._create_linked_activity(
            api_version=api_version,
            related_entity_note_id=lead_note_id,
            related_entity_type="PX.Objects.CR.CRLead",
            summary=summary,
            details=details,
            activity_type=activity_type,
        )