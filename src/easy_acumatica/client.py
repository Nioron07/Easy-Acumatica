"""easy_acumatica.client
======================

A lightweight wrapper around the **contract-based REST API** of
Acumatica ERP. The :class:`AcumaticaClient` class handles the entire
session lifecycle and dynamically generates its data models and service
layers from the live endpoint schema.

Usage example
-------------
>>> from easy_acumatica import AcumaticaClient
>>> client = AcumaticaClient(
...     base_url="https://demo.acumatica.com",
...     username="admin",
...     password="Pa$$w0rd",
...     tenant="Company")
>>>
>>> # Create a new Bill using a dynamically generated model and service
>>> new_bill = client.models.Bill(Vendor="MYVENDOR01", Type="Bill")
>>> created_bill = client.bills.put_entity(new_bill)
>>>
>>> client.logout()
"""
from __future__ import annotations
import atexit
from typing import Optional, Dict, Any
import requests

from . import models
from .model_factory import ModelFactory
from .service_factory import ServiceFactory # Import the new ServiceFactory
from .helpers import _raise_with_detail
from .core import BaseService

__all__ = ["AcumaticaClient"]

class AcumaticaClient:
    """High-level convenience wrapper around Acumatica's REST endpoint."""

    _atexit_registered: bool = False

    def __init__(
        self,
        base_url: str,
        username: str,
        password: str,
        tenant: str,
        branch: Optional[str] = None,
        locale: Optional[str] = None,
        verify_ssl: bool = True,
        persistent_login: bool = True,
        retry_on_idle_logout: bool = True,
        endpoint_name: str = "Default",
        endpoint_version: Optional[str] = None
    ) -> None:
        # --- Public attributes ---
        self.base_url: str = base_url.rstrip("/")
        self.session: requests.Session = requests.Session()
        self.verify_ssl: bool = verify_ssl
        self.tenant: str = tenant
        self.username: str = username
        self.password: str = password
        self.persistent_login: bool = persistent_login
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoints: Dict[str, Dict] = {}
        self.models = models # The placeholder module for our dynamic models

        # --- Login payload construction ---
        payload = {"name": username, "password": password, "tenant": tenant}
        if branch: payload["branch"] = branch
        if locale: payload["locale"] = locale
        self._login_payload: dict[str, str] = {k: v for k, v in payload.items() if v is not None}
        self._logged_in: bool = False

        # --- Login and Schema Generation ---
        if self.persistent_login:
            self.login()

        self._populate_endpoint_info()
        target_version = endpoint_version or self.endpoints.get(endpoint_name, {}).get('version')
        if not target_version:
            raise ValueError(f"Could not determine a version for endpoint '{endpoint_name}'.")

        schema = self._fetch_schema(endpoint_name, target_version)
        
        # --- DYNAMIC MODEL AND SERVICE GENERATION ---
        self._build_dynamic_models(schema)
        self._build_dynamic_services(schema)

        # --- Exit Hook ---
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True

    def _populate_endpoint_info(self):
        """Retrieves and stores the latest version for each available endpoint."""
        url = f"{self.base_url}/entity"
        endpoint_data = self._request("get", url).json()
        
        for endpoint in endpoint_data.get('endpoints', []):
            name = endpoint.get('name')
            if name and (name not in self.endpoints or endpoint.get('version', '0') > self.endpoints[name].get('version', '0')):
                self.endpoints[name] = endpoint

    def _fetch_schema(self, endpoint_name: str, version: str) -> Dict[str, Any]:
        """Fetches the OpenAPI schema for a given endpoint."""
        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json"
        return self._request("get", schema_url).json()

    def _build_dynamic_models(self, schema: Dict[str, Any]):
        """Populates the 'models' module with dynamically generated dataclasses."""
        factory = ModelFactory(schema)
        model_dict = factory.build_models()
        for name, model_class in model_dict.items():
            setattr(self.models, name, model_class)

    def _build_dynamic_services(self, schema: Dict[str, Any]):
        """Attaches dynamically created services to the client instance."""
        factory = ServiceFactory(self, schema)
        services_dict = factory.build_services()
        for name, service_instance in services_dict.items():
            # Convert PascalCase (e.g., SalesOrder) to snake_case (e.g., sales_orders)
            attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_') + 's'
            setattr(self, attr_name, service_instance)

    def login(self) -> int:
        """Authenticate and obtain a cookie-based session."""
        if not self._logged_in:
            url = f"{self.base_url}/entity/auth/login"
            response = self.session.post(url, json=self._login_payload, verify=self.verify_ssl)
            response.raise_for_status()
            self._logged_in = True
            return response.status_code
        return 204

    def logout(self) -> int:
        """Log out and invalidate the server-side session."""
        if self._logged_in:
            url = f"{self.base_url}/entity/auth/logout"
            response = self.session.post(url, verify=self.verify_ssl)
            self.session.cookies.clear()
            self._logged_in = False
            return response.status_code
        return 204

    def _atexit_logout(self) -> None:
        """Internal helper attached to :pymod:`atexit`."""
        try:
            self.logout()
        except Exception:
            pass

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """Perform a session request, with automatic re-login on 401 Unauthorized."""
        if not self.persistent_login:
            self.login()

        try:
            resp = self.session.request(method, url, **kwargs)
            if resp.status_code == 401 and self.retry_on_idle_logout:
                self._logged_in = False
                self.login()
                resp = self.session.request(method, url, **kwargs)
            _raise_with_detail(resp)
            return resp
        finally:
            if not self.persistent_login:
                self.logout()