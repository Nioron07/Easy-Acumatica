"""easy_acumatica.client
======================

A lightweight wrapper around the **contract‑based REST API** of
Acumatica ERP.  The :class:`AcumaticaClient` class handles the entire
session lifecycle:

* opens a persistent :class:`requests.Session`;
* logs in automatically when the object is created;
* exposes typed *sub‑services* (for example, :pyattr:`contacts`);
* guarantees a clean logout either explicitly via
  :pymeth:`logout` or implicitly on interpreter shutdown.

Usage example
-------------
>>> from easy_acumatica import AcumaticaClient
>>> client = AcumaticaClient(
...     base_url="https://demo.acumatica.com",
...     username="admin",
...     password="Pa$$w0rd",
...     tenant="Company",
...     branch="HQ")
>>> contact = client.contacts.get_contacts("24.200.001")
>>> client.logout()  # optional – will also run automatically
"""
from __future__ import annotations

import atexit
from typing import Optional

import requests

# Sub‑services -------------------------------------------------------------
from .sub_services.contacts import ContactsService

__all__ = ["AcumaticaClient"]


class AcumaticaClient:  # pylint: disable=too-few-public-methods
    """High‑level convenience wrapper around Acumatica's REST endpoint.

    The client manages a single authenticated HTTP session.  A successful
    instantiation performs an immediate **login** call; conversely a
    **logout** is registered with :pymod:`atexit` so that resources are
    freed even if the caller forgets to do so.

    Parameters
    ----------
    base_url : str
        Root URL of the Acumatica site, e.g. ``https://example.acumatica.com``.
    username : str
        User name recognised by Acumatica.
    password : str
        Corresponding password.
    tenant : str
        Target tenant (company) code.
    branch : str
        Branch code within the tenant.
    locale : str | None, optional
        UI locale, such as ``"en-US"``.  When *None* the server default is
        used (``en-US`` on most installations).
    verify_ssl : bool, default ``True``
        Whether to validate TLS certificates when talking to the server.
    """

    # ──────────────────────────────────────────────────────────────────
    _atexit_registered: bool = False  # class‑level guard

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        tenant: str,
        branch: str,
        locale: Optional[str] = None,
        verify_ssl: bool = True,
    ) -> None:
        # --- public attributes --------------------------------------
        self.base_url: str = base_url.rstrip("/")
        self.session: requests.Session = requests.Session()
        self.verify_ssl: bool = verify_ssl

        # --- payload construction -----------------------------------
        payload = {
            "name": username,
            "password": password,
            "tenant": tenant,
            "branch": branch,
            **({"locale": locale} if locale else {}),
        }
        # Drop any *None* values so we don't send them in the JSON body
        self._login_payload: dict[str, str] = {
            k: v for k, v in payload.items() if v is not None
        }

        self._logged_in: bool = False

        # Perform an immediate login; will raise for HTTP errors
        self.login()

        # Ensure we always log out exactly once on normal interpreter exit
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True

        # Service proxies --------------------------------------------------
        self.contacts: ContactsService = ContactsService(self)

    # ──────────────────────────────────────────────────────────────────
    # Session control helpers
    # ──────────────────────────────────────────────────────────────────
    def login(self) -> int:
        """Authenticate and obtain a cookie‑based session.

        Returns
        -------
        int
            HTTP status code (200 for the first login, 204 if we were
            already logged in).
        """
        if not self._logged_in:
            url = f"{self.base_url}/entity/auth/login"
            response = self.session.post(
                url, json=self._login_payload, verify=self.verify_ssl
            )
            response.raise_for_status()
            self._logged_in = True
            return response.status_code
        return 204  # NO CONTENT – session already active

    # ------------------------------------------------------------------
    def logout(self) -> int:
        """Log out and invalidate the server‑side session.

        This method is **idempotent**: calling it more than once is safe
        and will simply return HTTP 204 after the first successful call.

        Returns
        -------
        int
            HTTP status code (200 on success, 204 if no active session).
        """
        print("Logging out")  # optional diagnostic; remove if too chatty
        if self._logged_in:
            url = f"{self.base_url}/entity/auth/logout"
            response = self.session.post(url, verify=self.verify_ssl)
            response.raise_for_status()
            self.session.cookies.clear()  # client‑side cleanup
            self._logged_in = False
            return response.status_code
        return 204  # NO CONTENT – nothing to do

    # ------------------------------------------------------------------
    def _atexit_logout(self) -> None:
        """Internal helper attached to :pymod:`atexit`.

        Guaranteed to run exactly once per Python process to release the
        server session.  All exceptions are swallowed because the Python
        interpreter is already shutting down.
        """
        try:
            self.logout()
        except Exception:  # pylint: disable=broad-except
            # Avoid noisy tracebacks at interpreter shutdown
            pass
