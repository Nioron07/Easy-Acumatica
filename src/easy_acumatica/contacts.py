"""easy_acumatica.contacts
========================

Typed wrapper around Acumatica's *contract‑based* REST endpoint for
**contacts** (``/entity/Default/[version]/Contact``).

The public :class:`ContactsService` exposes a single helper
:meth:`get_contacts`, which accepts an optional
:class:`~easy_acumatica.filters.QueryOptions` object to craft
``$filter``, ``$expand``, ``$select``, ``$top`` and ``$skip`` query
options in a type‑safe manner.

Typical usage
-------------
>>> from easy_acumatica import AcumaticaClient, QueryOptions, Filter
>>> client = AcumaticaClient(...credentials...)
>>> opts = QueryOptions(filter=Filter().eq("ContactID", 100073))
>>> contacts = client.contacts.get_contacts("24.200.001", options=opts)
>>> contacts[0]["DisplayName"]
'John Smith'
"""
from __future__ import annotations

import requests
from typing import TYPE_CHECKING, Any, Optional

from .filters import QueryOptions

if TYPE_CHECKING:  # pragma: no cover – import‑time hint only
    from .client import AcumaticaClient

__all__ = ["ContactsService"]


auth_error_msg = (
    "Acumatica API error {code}: {detail}"
)  # module‑level template keeps the f‑string in one place


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
        """Retrieve contacts, optionally filtered/expanded/selected.

        Parameters
        ----------
        api_version : str
            Semantic version of the endpoint, e.g. ``"24.200.001"``.
        options : QueryOptions | None, optional
            Encapsulates ``$filter``, ``$expand``, ``$select``, ``$top``,
            and ``$skip``.  If *None*, all contacts are returned (subject
            to the server's default limit).

        Returns
        -------
        Any
            JSON‑decoded response from the server – typically a list of
            contact dictionaries.

        Raises
        ------
        RuntimeError
            If Acumatica responds with a non‑2xx status code.  The
            *exceptionMessage* or *message* field (when present) is
            surfaced for easier debugging.
        """
        # Build endpoint --------------------------------------------------
        url = f"{self._client.base_url}/entity/Default/{api_version}/Contact"
        params = options.to_params() if options else None

        # Perform request --------------------------------------------------
        resp = self._client.session.get(url, params=params, verify=self._client.verify_ssl)

        # Error handling ---------------------------------------------------
        try:
            resp.raise_for_status()
        except requests.HTTPError as exc:
            # Attempt to extract detailed error info
            detail: str | int
            try:
                err_json = resp.json()
                detail = (
                    err_json.get("exceptionMessage")
                    or err_json.get("message")
                    or err_json
                )
            except ValueError:  # non‑JSON payload (e.g. HTML error page)
                detail = resp.text or resp.status_code

            msg = auth_error_msg.format(code=resp.status_code, detail=detail)
            print(msg)  # keep a breadcrumb in stdout/stderr
            raise RuntimeError(msg) from exc

        # Success – return the JSON payload -------------------------------
        return resp.json()
