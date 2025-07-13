# src/easy_acumatica/sub_services/contacts.py

from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional, Union

from ..core import BaseService # Import the base class
from ..models import (
    Contact,
    QueryOptions,
    F,
    Filter
)

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["ContactsService"]

class ContactsService(BaseService):
    """
    High-level helper for Contact resources, built on the BaseService.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the service with the 'Contact' entity."""
        super().__init__(client, "Contact")

    def get_schema(self, api_version: Optional[str] = None) -> Any:
        """
        Retrieves the swagger schema for the endpoint. This method contains
        custom logic that does not fit the standard service methods.
        """
        return self._get_schema(self.entity_name)

    def get_contacts(
        self,
        api_version: Optional[str] = None,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """Retrieves a list of contacts using the base _get method."""
        return self._get(api_version, options=options)

    def create_contact(
        self,
        draft: Contact,
        api_version: Optional[str] = None
    ) -> Any:
        """Creates a new contact using the base _put method."""
        return self._put(draft, api_version)

    def update_contact(
        self,
        filter_: Union[Filter, str, QueryOptions],
        payload: Union[dict, Contact],
        api_version: Optional[str] = None
    ) -> Any:
        """Updates one or more contacts selected by a filter."""
        if isinstance(filter_, QueryOptions):
            options = filter_
        else:
            # Create a QueryOptions object from the filter string or Filter object
            flt = filter_.build() if isinstance(filter_, Filter) else str(filter_)
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
        Note: This requires a _delete method to be added to the BaseService.
        """
        # Assuming BaseService has a _delete method similar to _get and _put.
        # It would look like: self._delete(api_version, entity_id=note_id)
        url = f"{self._get_url(api_version)}/{note_id}"
        self._request("delete", url, verify=self._client.verify_ssl)

    def link_contact_to_customer(
        self,
        contact_id: int,
        business_account: str,
        api_version: Optional[str] = None,
        payload: Optional[Union[dict, Contact]] = None
    ) -> Any:
        """Links an existing contact to a customer (business account)."""
        
        if payload is None:
            # If no payload, create a new builder. Otherwise, use the provided one.
            body_builder = Contact()
        elif isinstance(payload, Contact):
            body_builder = payload
        else:
            # If a dict is passed, convert it to a builder to maintain a
            # consistent object type for modification.
            body_builder = Contact()
            body_builder._data = payload

        # Add the linking fields to the builder
        body_builder.set("BusinessAccount", business_account)
        body_builder.set("ContactID", contact_id)
        
        # Use the contact's ID to create the filter and call the update method
        update_filter = F.ContactID == contact_id
        return self.update_contact(update_filter, body_builder, api_version)