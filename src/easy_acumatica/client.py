import requests
from .contacts import ContactsService

class AcumaticaClient:
    def __init__(self, base_url, username, password,
                 tenant, branch, locale=None,
                 verify_ssl=True):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        self.verify_ssl = verify_ssl
        self.login_payload = {
            "name":     username,
            "password": password,
            "tenant":   tenant,
            "branch":   branch,
        }
        if locale:
            self.login_payload["locale"] = locale
        
        self.contacts = ContactsService(self)

    def login(self):
        url = f"{self.base_url}/entity/auth/login"
        resp = self.session.post(
            url,
            json=self.login_payload,
            verify=self.verify_ssl
        )
        resp.raise_for_status()
        return resp.status_code

    def logout(self):
        url = f"{self.base_url}/entity/auth/logout"
        resp = self.session.post(url, verify=self.verify_ssl)
        resp.raise_for_status()
        self.session.cookies.clear()
        return resp.status_code
