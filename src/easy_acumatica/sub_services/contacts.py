# src/easy_acumatica/sub_services/contacts.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union

from ..core import BaseService
from ..odata import QueryOptions, F, Filter

if TYPE_CHECKING:
    from ..client import AcumaticaClient
    # For type hinting, we can still refer to the base model
    from ..core import BaseDataClassModel 

__all__ = ["ContactsService"]

class ContactsService(BaseService):
    """
    High-level helper for Contact resources, built on the BaseService.
    This service now works with dynamically generated Contact models.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the service with the 'Contact' entity."""
        super().__init__(client, "Contact")

    def get_schema(self, api_version: Optional[str] = None) -> Any:
        """Retrieves the swagger schema for the Contact endpoint."""
        return self._get_schema(api_version=api_version)

    def get_contacts(
        self,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """Retrieves a list of contacts using the base _get method."""
        return self._get(api_version, options=options)

    def create_contact(
        self,
        # The 'draft' is now expected to be an instance of the dynamic model
        draft: "BaseDataClassModel",
        api_version: Optional[str] = None
    ) -> Any:
        """Creates a new contact using the base _put method."""
        # The draft's .build() method is handled by _put in BaseService
        return self._put(draft, api_version)

    def update_contact(
        self,
        filter_: Union[Filter, str, QueryOptions],
        # The payload can be a dict or a dynamic model instance
        payload: Union[dict, "BaseDataClassModel"],
        api_version: Optional[str] = None
    ) -> Any:
        """Updates one or more contacts selected by a filter."""
        if isinstance(filter_, QueryOptions):
            options = filter_
        else:
            flt = str(filter_)
            options = QueryOptions(filter=flt)

        return self._put(payload, api_version, options=options)

    def deactivate_contact(
        self,
        filter_: Union[Filter, str, QueryOptions],
        api_version: Optional[str] = None,
        *,
        active: bool = False,
    ) -> Any:
        """Activates or deactivates contacts by updating the 'Active' flag."""
        payload = {"Active": {"value": bool(active)}}
        return self.update_contact(filter_, payload, api_version)

    def delete_contact(self, note_id: str, api_version: Optional[str] = None) -> None:
        """
        Permanently deletes a contact by its NoteID (GUID).
        """
        # This now uses the _delete method from the BaseService
        self._delete(note_id, api_version)

    def link_contact_to_customer(
        self,
        contact_id: int,
        business_account: str,
        api_version: Optional[str] = None,
    ) -> Any:
        """
        Links an existing contact to a customer (business account) by updating it.
        """
        # Create an instance of the dynamic Contact model
        # The user's IDE won't autocomplete this, but it will work at runtime.
        contact_payload = self._client.models.Contact(
            ContactID=contact_id,
            BusinessAccount=business_account
        )
        
        # Use the contact's ID to create the filter for the update
        update_filter = F.ContactID == contact_id
        return self.update_contact(update_filter, contact_payload, api_version)