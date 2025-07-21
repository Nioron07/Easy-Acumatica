"""easy_acumatica.client
======================

A lightweight wrapper around the **contract-based REST API** of
Acumatica ERP. The :class:`AcumaticaClient` class handles the entire
session lifecycle.

Its key features include:
* Opens a persistent :class:`requests.Session` for efficient communication.
* Handles login and logout automatically.
* Dynamically generates data models (e.g., `Contact`, `Bill`) from the live
    endpoint schema, ensuring they are always up-to-date and include custom fields.
* Dynamically generates service layers (e.g., `client.contacts`, `client.bills`)
    with methods that directly correspond to available API operations.
* Guarantees a clean logout either explicitly via :pymeth:`logout` or implicitly
    on interpreter shutdown.

Usage example
-------------
>>> from easy_acumatica import AcumaticaClient
>>> # Initialization connects to the API and builds all models and services
>>> client = AcumaticaClient(
...     base_url="https://demo.acumatica.com",
...     username="admin",
...     password="Pa$$w0rd",
...     tenant="Company")
>>>
>>> # Use a dynamically generated model to create a new record
>>> new_bill = client.models.Bill(Vendor="MYVENDOR01", Type="Bill")
>>>
>>> # Use a dynamically generated service method to send the request
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
from .service_factory import ServiceFactory
from .helpers import _raise_with_detail

__all__ = ["AcumaticaClient"]

class AcumaticaClient:
    """
    High-level convenience wrapper around Acumatica's REST endpoint.

    Manages a single authenticated HTTP session and dynamically builds out its
    own methods and data models based on the API schema of the target instance.
    """

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
        """
        Initializes the client, logs in, and builds the dynamic services.

        Args:
            base_url: Root URL of the Acumatica site (e.g., `https://example.acumatica.com`).
            username: User name recognized by Acumatica.
            password: Corresponding password.
            tenant: Target tenant (company) code.
            branch: Branch code within the tenant (optional).
            locale: UI locale, such as "en-US" (optional).
            verify_ssl: Whether to validate TLS certificates.
            persistent_login: If True, logs in once on creation and logs out at exit.
                              If False, logs in and out for every single request.
            retry_on_idle_logout: If True, automatically re-login and retry a request once
                                  if it fails with a 401 Unauthorized error.
            endpoint_name: The name of the API endpoint to use (e.g., "Default").
            endpoint_version: A specific version of the endpoint to use (e.g., "24.200.001").
                              If not provided, the latest version will be used.
        """
        # --- 1. Set up public attributes ---
        self.base_url: str = base_url.rstrip("/")
        self.session: requests.Session = requests.Session()
        self.verify_ssl: bool = verify_ssl
        self.tenant: str = tenant
        self.username: str = username
        self.password: str = password
        self.persistent_login: bool = persistent_login
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoints: Dict[str, Dict] = {}
        # The 'models' attribute points to the models module, which will be
        # populated with dynamic dataclasses.
        self.models = models

        # --- 2. Construct the login payload ---
        payload = {"name": username, "password": password, "tenant": tenant}
        if branch: payload["branch"] = branch
        if locale: payload["locale"] = locale
        self._login_payload: dict[str, str] = {k: v for k, v in payload.items() if v is not None}
        self._logged_in: bool = False

        # --- 3. Initial Login ---
        # For persistent sessions, log in immediately. For non-persistent sessions,
        # the _request wrapper will handle login/logout for each call.
        if self.persistent_login:
            self.login()

        # --- 4. Discover Endpoint Information ---
        # Fetch all available endpoints and their latest versions.
        self._populate_endpoint_info()
        target_version = endpoint_version or self.endpoints.get(endpoint_name, {}).get('version')
        if not target_version:
            raise ValueError(f"Could not determine a version for endpoint '{endpoint_name}'.")

        # --- 5. Fetch Schema and Build Dynamic Components ---
        # This is the core of the dynamic architecture.
        schema = self._fetch_schema(endpoint_name, target_version)
        self._build_dynamic_models(schema)
        self._build_dynamic_services(schema)

        # --- 6. Register atexit hook for clean logout ---
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True

    def _populate_endpoint_info(self):
        """Retrieves and stores the latest version for each available endpoint."""
        url = f"{self.base_url}/entity"
        # Use the internal _request method to handle auth and errors.
        endpoint_data = self._request("get", url).json()
        
        for endpoint in endpoint_data.get('endpoints', []):
            name = endpoint.get('name')
            # Store the endpoint only if it's new or a higher version than what we have.
            if name and (name not in self.endpoints or endpoint.get('version', '0') > self.endpoints[name].get('version', '0')):
                self.endpoints[name] = endpoint

    def _fetch_schema(self, endpoint_name: str, version: str) -> Dict[str, Any]:
        """Fetches the OpenAPI schema for a given endpoint."""
        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json?company={self.tenant}"
        return self._request("get", schema_url).json()

    def _build_dynamic_models(self, schema: Dict[str, Any]):
        """Populates the 'models' module with dynamically generated dataclasses."""
        factory = ModelFactory(schema)
        model_dict = factory.build_models()
        # Attach each generated class (e.g., Contact, Address) to the models module.
        for name, model_class in model_dict.items():
            setattr(self.models, name, model_class)

    def _build_dynamic_services(self, schema: Dict[str, Any]):
        """Attaches dynamically created services to the client instance."""
        factory = ServiceFactory(self, schema)
        services_dict = factory.build_services()
        for name, service_instance in services_dict.items():
            # Convert PascalCase (e.g., SalesOrder) to snake_case (e.g., sales_orders)
            # to use as the Python attribute name.
            attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_') + 's'
            setattr(self, attr_name, service_instance)

    def login(self) -> int:
        """Authenticates and obtains a cookie-based session."""
        if not self._logged_in:
            url = f"{self.base_url}/entity/auth/login"
            response = self.session.post(url, json=self._login_payload, verify=self.verify_ssl)
            response.raise_for_status()
            self._logged_in = True
            return response.status_code
        return 204 # Already logged in

    def logout(self) -> int:
        """Logs out and invalidates the server-side session."""
        if self._logged_in:
            url = f"{self.base_url}/entity/auth/logout"
            response = self.session.post(url, verify=self.verify_ssl)
            self.session.cookies.clear()
            self._logged_in = False
            return response.status_code
        return 204 # Already logged out

    def _atexit_logout(self) -> None:
        """Internal helper attached to `atexit` to guarantee a clean logout."""
        try:
            self.logout()
        except Exception:
            # Swallow exceptions during shutdown to avoid noisy tracebacks.
            pass

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        The central method for making all API requests.
        
        Handles the session lifecycle (login/logout) for non-persistent
        connections and provides automatic re-authentication on session timeout.
        """
        # For non-persistent mode, ensure we are logged in before the request.
        if not self.persistent_login:
            self.login()

        try:
            # Make the actual HTTP request using the session object.
            resp = self.session.request(method, url, **kwargs)
            
            # If we get a 401 Unauthorized, the session likely expired.
            if resp.status_code == 401 and self.retry_on_idle_logout:
                self._logged_in = False
                self.login() # Re-authenticate
                resp = self.session.request(method, url, **kwargs) # Retry the request once
            
            # Check the final response for any other errors.
            _raise_with_detail(resp)
            return resp
        finally:
            # For non-persistent mode, log out after the request is complete.
            if not self.persistent_login:
                self.logout()