from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..core import BaseService
from ..odata import QueryOptions

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["AccountService"]


class AccountService(BaseService):
    """
    A sub-service for managing GL Accounts in Acumatica.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the AccountService with an active client session."""
        super().__init__(client, "Account")

    def get_schema(self, api_version: Optional[str] = None) -> Any:
        """
        Retrieves the swagger schema for the Account endpoint.
        """
        return self._get_schema(api_version=api_version)

    def add_account_to_group(
        self,
        accountCD: str,
        groupID: str,
        api_version: Optional[str] = None
    ) -> dict:
        """
        Assigns an existing GL Account to a specific Account Group.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            accountCD: The identifier of the account to be assigned (e.g., "170100").
            groupID: The identifier of the group to assign the account to.

        Returns:
            The JSON representation of the updated Account record.
        """
        payload = {
            "AccountCD": {"value": accountCD},
            "AccountGroup": {"value": groupID}
        }
        return self._put(payload, api_version)

    def get_accounts(
            self,
            api_version: Optional[str] = None,
            options: Optional[QueryOptions] = None,
        ) -> Any:
        """
        Retrieve a list of GL Accounts, optionally filtered.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            options: An optional QueryOptions object to filter, select, expand,
                     or paginate the results.

        Returns:
            A list of dictionaries, where each dictionary is an Account record.
        """
        return self._get(api_version, options=options)

    def remove_account_from_group(
        self,
        accountCD: str,
        api_version: Optional[str] = None
    ) -> dict:
        """
        Removes a GL Account from its currently assigned Account Group.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            accountCD: The identifier of the account to be removed from its group.

        Returns:
            The JSON representation of the updated Account record.
        """
        payload = {
            "AccountCD": {"value": accountCD},
            "AccountGroup": {"value": None}
        }
        return self._put(payload, api_version)