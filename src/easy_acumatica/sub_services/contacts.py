"""easy_acumatica.sub_services.contacts
========================

Typed wrapper around Acumatica's *contract‑based* REST endpoint for
**contacts** (``/entity/Default/[version]/Contact``).

The public :class:`ContactsService` exposes two helpers:

* :meth:`get_contacts` – list/search contacts with optional
  :class:`~easy_acumatica.filters.QueryOptions` (``$filter``, ``$expand`` …).
* :meth:`create_contact` – create a new contact using a
  :class:`~easy_acumatica.models.contact.ContactBuilder` payload.

Typical usage
-------------
>>> from easy_acumatica import AcumaticaClient, QueryOptions, Filter
>>> from easy_acumatica.models.contact import ContactBuilder
>>> client = AcumaticaClient(...credentials...)
>>> opts = QueryOptions(filter=Filter().eq("ContactID", 100073))
>>> contacts = client.contacts.get_contacts("24.200.001", options=opts)
>>> contacts[0]["DisplayName"]
'John Smith'
>>> # build & push a new lead
>>> draft = (ContactBuilder()
...          .first_name("Brent")
...          .last_name("Edds")
...          .email("brent.edds@example.com")
...          .contact_class("ENDCUST")
...          .add_attribute("INTEREST", "Jam,Maint"))
>>> created = client.contacts.create_contact("24.200.001", draft)
>>> created["ContactID"]["value"]
104000
"""
from __future__ import annotations

import requests
from typing import TYPE_CHECKING, Any, Optional, Union

from ..models.filters import QueryOptions, Filter
from ..models.contact_builder import ContactBuilder  # payload builder

if TYPE_CHECKING:  # pragma: no cover – import‑time hint only
    from ..client import AcumaticaClient

__all__ = ["ContactsService"]


auth_error_msg = (
    "Acumatica API error {code}: {detail}"
)  # module‑level template keeps the f‑string in one place


def _raise_with_detail(resp: requests.Response) -> None:
    """Shared helper to raise a *RuntimeError* with parsed details."""
    try:
        resp.raise_for_status()
    except requests.HTTPError as exc:
        try:
            err_json = resp.json()
            detail = (
                err_json.get("exceptionMessage")
                or err_json.get("message")
                or err_json
            )
        except ValueError:
            detail = resp.text or resp.status_code

        msg = auth_error_msg.format(code=resp.status_code, detail=detail)
        print(msg)
        raise RuntimeError(msg) from exc


class ContactsService:  # pylint: disable=too-few-public-methods
    """High‑level helper for **Contact** resources.

    Instances are created by :class:`easy_acumatica.client.AcumaticaClient`
    and share its authenticated :pyclass:`requests.Session`.
    """

    def __init__(self, client: "AcumaticaClient") -> None:
        self._client = client

    # ------------------------------------------------------------------
    def get_contacts(
        self,
        api_version: str,
        options: Optional[QueryOptions] = None,
    ) -> Any:
        """Retrieve contacts, optionally filtered/expanded/selected."""
        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        params = options.to_params() if options else None

        resp = self._client.session.get(url, params=params, verify=self._client.verify_ssl)
        _raise_with_detail(resp)
        return resp.json()

    # ------------------------------------------------------------------
    def create_contact(
        self,
        api_version: str,
        draft: ContactBuilder,
    ) -> Any:
        """Create a new contact (lead) in Acumatica.

        Parameters
        ----------
        api_version : str
            Target endpoint version, e.g. ``"24.200.001"``.
        draft : ContactBuilder
            Fluent payload builder.  Call :pymeth:`ContactBuilder.build` to
            see the raw JSON that will be sent.

        Returns
        -------
        Any
            JSON representation of the newly‑created record.
        """
        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        resp = self._client.session.put(
            url,
            json=draft.build(),
            verify=self._client.verify_ssl,
        )
        _raise_with_detail(resp)
        return resp.json()
    # ------------------------------------------------------------------
    def deactivate_contact(
        self,
        api_version: str,
        filter_: Union[Filter, str, QueryOptions],
        *,
        active: bool = False,
    ) -> Any:
        """Activate or deactivate contacts via `$filter`.

        Parameters
        ----------
        api_version : str
            Target endpoint version, e.g. ``"24.200.001"``.
        filter_ : Filter | str | QueryOptions
            OData filter selecting the contacts to update.  If a
            :class:`Filter` or plain string is supplied, it is converted
            into a minimal :class:`QueryOptions` holding only ``$filter``.
            Passing a full :class:`QueryOptions` lets you combine `$top`
            etc. but the server will still update all hits.
        active : bool, keyword‑only, default ``False``
            ``False`` → deactivate (set *Active* field to **false**).  
            ``True``  → activate again.

        Returns
        -------
        Any
            JSON payload returned by Acumatica (usually the updated
            records).
        """
        # Build params ---------------------------------------------------
        if isinstance(filter_, QueryOptions):
            params = filter_.to_params()
        else:
            flt = filter_.build() if isinstance(filter_, Filter) else str(filter_)
            params = {"$filter": flt}

        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        payload = {"Active": {"value": bool(active)}}

        resp = self._client.session.put(
            url, params=params, json=payload, verify=self._client.verify_ssl
        )
        _raise_with_detail(resp)
        return resp.json()

    # ------------------------------------------------------------------
    def update_contact(
        self,
        api_version: str,
        filter_: Union[Filter, str, QueryOptions],
        payload: Union[dict, ContactBuilder],
    ) -> Any:
        """
        Update one-or-more contacts selected by an OData ``$filter``.

        Acumatica requires ``PUT /Contact?$filter=...`` for updates.
        Any fields present in *payload* overwrite the existing values.

        Parameters
        ----------
        api_version : str
        filter_ : Filter | str | QueryOptions
            Expression that uniquely identifies the contact(s),
            e.g. ``Filter().eq("ContactID", 110596)``.
        payload : dict | ContactBuilder
            Only include the fields you want to change.

        Returns
        -------
        Any
            JSON list of the updated record(s) returned by Acumatica.
        """
        # build `$filter` -------------------------------------------------
        if isinstance(filter_, QueryOptions):
            params = filter_.to_params()
        else:
            params = {
                "$filter": filter_.build() if isinstance(filter_, Filter) else str(filter_)
            }

        body = payload.build() if isinstance(payload, ContactBuilder) else payload
        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"

        resp = self._client.session.put(url, params=params, json=body,
                                        verify=self._client.verify_ssl)
        _raise_with_detail(resp)
        return resp.json()


    # ------------------------------------------------------------------
    def delete_contact(self, api_version: str, note_id: str) -> None:
        """
        Permanently delete a contact.

        Parameters
        ----------
        api_version : str
            Endpoint version (``"24.200.001"`` …).
        note_id : str
            The GUID from the contact’s ``NoteID`` field.

        Notes
        -----
        * The contract-based API returns **HTTP 204 No Content** on success.
        * Deletion cannot be undone; consider using
        :meth:`deactivate_contact` if soft-delete semantics are preferred.
        """
        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact/{note_id}"
        resp = self._client.session.delete(url, verify=self._client.verify_ssl)
        _raise_with_detail(resp)
        return None