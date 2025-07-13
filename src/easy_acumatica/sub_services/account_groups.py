from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..core import BaseService
from ..odata import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["AccountGroupsService"]


class AccountGroupsService(BaseService):
    """
    A sub-service for managing Account Groups in Acumatica.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the AccountGroupsService with an active client session."""
        super().__init__(client, "AccountGroup")

    def get_schema(self, api_version: Optional[str] = None) -> Any:
        """
        Retrieves the swagger schema for the AccountGroup endpoint.
        """
        return self._get_schema(api_version=api_version)

    def get_account_groups(self, api_version: Optional[str] = None, options: Optional[QueryOptions] = None) -> Any:
        """
        Retrieve a list of Account Groups, optionally filtered.
        
        Args:
            api_version: The contract API version, e.g., "24.200.001".
            options: An optional QueryOptions object to filter, select, expand,
                     or paginate the results.

        Returns:
            A list of dictionaries, where each dictionary is an Account Group record.
        """
        return self._get(api_version, options=options)

    def create_account_group(
        self,
        group_id: str,
        description: str,
        api_version: Optional[str] = None
    ) -> dict:
        """
        Creates a new account group.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            group_id: The unique identifier for the new account group.
            description: The description for the new account group.

        Returns:
            The JSON representation of the newly created account group.
        """
        payload = {
            "AccountGroupID": {"value": group_id},
            "Description": {"value": description}
        }
        return self._put(payload, api_version)

    def set_default_account_for_group(
        self,
        group_id: str,
        account_id: str,
        api_version: Optional[str] = None
    ) -> dict:
        """
        Specifies the default account for a given account group.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            group_id: The identifier of the account group to modify.
            account_id: The account ID to set as the default for the group.

        Returns:
            The JSON representation of the updated account group.
        """
        payload = {
            "AccountGroupID": {"value": group_id},
            "DefaultAccountID": {"value": account_id}
        }
        return self._put(payload, api_version)