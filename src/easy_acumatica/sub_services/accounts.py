from __future__ import annotations
from typing import TYPE_CHECKING, Any, Optional

from ..models.query_builder import QueryOptions
from ..helpers import _raise_with_detail

if TYPE_CHECKING:
    from ..client import AcumaticaClient

__all__ = ["AccountService"]


class AccountService:
    """
    A sub-service for managing GL Accounts and Account Groups in Acumatica.

    This service provides methods to retrieve accounts, create and manage
    account groups, and assign accounts to those groups.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        """Initializes the AccountService with an active client session."""
        self._client = client

    def add_account_to_group(
        self,
        api_version: str,
        accountCD: str,
        groupID: str
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
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Account"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "AccountCD": {"value": accountCD},
            "AccountGroup": {"value": groupID}
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

    def get_accounts(
            self,
            api_version: str,
            options: Optional[QueryOptions] = None,
        ) -> Any:
        """
        Retrieve a list of GL Accounts, optionally filtered.

        This method supports the full range of OData query parameters through
        the QueryOptions object, allowing for powerful and specific queries.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            options: An optional QueryOptions object to filter, select, expand,
                     or paginate the results.

        Returns:
            A list of dictionaries, where each dictionary is an Account record.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Account"
        params = options.to_params() if options else None

        resp = self._client._request("get", url, params=params, verify=self._client.verify_ssl)
        _raise_with_detail(resp)

        if not self._client.persistent_login:
            self._client.logout()
        return resp.json()
    
    def remove_account_from_group(
        self,
        api_version: str,
        accountCD: str
    ) -> dict:
        """
        Removes a GL Account from its currently assigned Account Group.

        This is achieved by updating the account's AccountGroup property to null.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            accountCD: The identifier of the account to be removed from its group.

        Returns:
            The JSON representation of the updated Account record.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/Account"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "AccountCD": {"value": accountCD},
            "AccountGroup": {"value": None}
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

    def create_account_group(
        self,
        api_version: str,
        group_id: str,
        description: str
    ) -> dict:
        """
        Creates a new account group.

        Sends a PUT request to the AccountGroup endpoint.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            group_id: The unique identifier for the new account group.
            description: The description for the new account group.

        Returns:
            The JSON representation of the newly created account group.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/AccountGroup"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "AccountGroupID": {"value": group_id},
            "Description": {"value": description}
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

    def set_default_account_for_group(
        self,
        api_version: str,
        group_id: str,
        account_id: str
    ) -> dict:
        """
        Specifies the default account for a given account group.

        Sends a PUT request to the AccountGroup endpoint.

        Args:
            api_version: The contract API version, e.g., "24.200.001".
            group_id: The identifier of the account group to modify.
            account_id: The account ID to set as the default for the group.

        Returns:
            The JSON representation of the updated account group.
        """
        if not self._client.persistent_login:
            self._client.login()

        url = f"{self._client.base_url}/entity/Default/{api_version}/AccountGroup"
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        payload = {
            "AccountGroupID": {"value": group_id},
            "DefaultAccountID": {"value": account_id}
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
