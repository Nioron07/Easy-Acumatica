# src/easy_acumatica/client.py

import requests
import atexit

# Sub-Services
from .contacts import ContactsService

class AcumaticaClient:
    _atexit_registered = False
    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        tenant: str,
        branch: str,
        locale: str = None,
        verify_ssl: bool = True
    ):
        self.base_url = base_url.rstrip("/")
        self.session = requests.Session()
        self.verify_ssl = verify_ssl

        # build login payload, dropping any None values
        payload = {
            "name": username,
            "password": password,
            "tenant": tenant,
            "branch": branch,
            **({"locale": locale} if locale else {}),
        }
        self.login_payload = {k: v for k, v in payload.items() if v is not None}

        self._logged_in = False
        # auto-login
        self.login()

        # register the atexit logout once
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True
        self.contacts = ContactsService(self)

    def login(self) -> int:
        if not self._logged_in:
            url = f"{self.base_url}/entity/auth/login"
            resp = self.session.post(
                url,
                json=self.login_payload,
                verify=self.verify_ssl
            )
            resp.raise_for_status()
            self._logged_in = True
            return resp.status_code
        return 204  # already logged in

    def logout(self) -> int:
        print("Logging out")
        if self._logged_in:
            url = f"{self.base_url}/entity/auth/logout"
            resp = self.session.post(url, verify=self.verify_ssl)
            resp.raise_for_status()
            self.session.cookies.clear()
            self._logged_in = False
            return resp.status_code
        return 204  # already logged out

    # Context-manager support:
    def __enter__(self):
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # always try to logout even on exceptions
        try:
            self.logout()
        except Exception:
            pass

    def _atexit_logout(self):
        # this runs on normal interpreter shutdown
        try:
            self.logout()
        except Exception:
            pass