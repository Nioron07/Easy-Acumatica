"""easy_acumatica.client
======================

A lightweight wrapper around the **contract-based REST API** of
Acumatica ERP. The :class:`AcumaticaClient` class handles the entire
session lifecycle:

* opens a persistent :class:`requests.Session`;
* logs in automatically when the object is created;
* dynamically generates data models from the live endpoint schema;
* exposes typed *sub-services* (for example, :pyattr:`contacts`);
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
>>> # Create a new Bill using a dynamically generated model
>>> new_bill = client.models.Bill(Vendor="MYVENDOR01", Type="Bill")
>>> client.bills.create_bill(new_bill)
>>> client.logout()  # optional - will also run automatically
"""
from __future__ import annotations

import atexit
from typing import Optional, Dict
import requests
from . import builders
from .model_factory import ModelFactory
from .helpers import _raise_with_detail

# Sub-services
from .sub_services import *


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
        branch: str,
        locale: Optional[str] = None,
        verify_ssl: bool = True,
        persistent_login: bool = True,
        retry_on_idle_logout: bool = True,
        endpoint_name: str = "Default",
        endpoint_version: Optional[str] = None
    ) -> None:
        # --- public attributes ---
        self.base_url: str = base_url.rstrip("/")
        self.session: requests.Session = requests.Session()
        self.verify_ssl: bool = verify_ssl
        self.tenant: str = tenant
        self.username: str = username
        self.password: str = password
        self.persistent_login: bool = persistent_login
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoints: Dict[str, Dict] = {}

        # --- payload construction ---
        payload = {
            "name": username, "password": password, "tenant": tenant,
            "branch": branch, **({"locale": locale} if locale else {}),
        }
        self._login_payload = {k: v for k, v in payload.items() if v is not None}
        self._logged_in: bool = False

        # --- Login and Schema Generation ---
        if self.persistent_login:
            self.login()

        # Fetch all available endpoints and their versions
        self._populate_endpoint_info()

        # Determine the target version and generate models
        target_version = endpoint_version or self.endpoints.get(endpoint_name, {}).get('version')
        if not target_version:
            raise ValueError(f"Could not determine a version for endpoint '{endpoint_name}'.")

        self._fetch_and_populate_models_module(endpoint_name, target_version)
        self.models = builders # Attach the module to the client instance

        # --- Service Proxies ---
        self._initialize_services()

        # --- Exit Hook ---
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True

    def _initialize_services(self):
        """Initializes all the sub-service attributes."""
        self.records = RecordsService(self)
        self.contacts = ContactsService(self)
        self.inquiries = InquiriesService(self)
        self.customers = CustomersService(self)
        self.codes = CodesService(self)
        self.files = FilesService(self)
        self.accounts = AccountService(self)
        self.account_groups = AccountGroupsService(self)
        self.transactions = TransactionsService(self)
        self.actions = ActionsService(self)
        self.activities = ActivitiesService(self)
        self.payments = PaymentsService(self)
        self.invoices = InvoicesService(self)
        self.employees = EmployeesService(self)
        self.leads = LeadsService(self)
        self.tax_categories = TaxCategoryService(self)
        self.ledgers = LedgersService(self)
        self.cases = CasesService(self)
        self.companies = CompaniesService(self)
        self.manufacturing = ManufacturingService(self)
        self.inventory = InventoryService(self)
        self.sales_orders = SalesOrdersService(self)
        self.shipments = ShipmentsService(self)
        self.stock_items = StockItemsService(self)
        self.service_orders = ServiceOrdersService(self)
        self.purchase_orders = PurchaseOrdersService(self)
        self.purchase_receipts = PurchaseReceiptsService(self)
        self.time_entries = TimeEntriesService(self)
        self.work_calendars = WorkCalendarsService(self)
        self.work_locations = WorkLocationsService(self)
        self.bills = BillsService(self)
        self.boms = BomsService(self)
        self.business_accounts = BusinessAccountsService(self)
        self.employee_payroll = EmployeePayrollService(self)

    def _populate_endpoint_info(self):
        """Retrieves and stores the latest version for each available endpoint."""
        url = f"{self.base_url}/entity"
        endpoint_data = self._request("get", url).json()
        
        for endpoint in endpoint_data.get('endpoints', []):
            name = endpoint.get('name')
            if name and (name not in self.endpoints or endpoint.get('version', '0') > self.endpoints[name].get('version', '0')):
                self.endpoints[name] = endpoint

    def _fetch_and_populate_models_module(self, endpoint_name: str, version: str) -> None:
        """
        Fetches the OpenAPI schema and populates the 'models' module
        with dynamically generated dataclasses.
        """
        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json"
        schema = self._request("get", schema_url).json()

        factory = ModelFactory(schema)
        model_dict = factory.build_models()
        
        # Attach each generated class to the models module
        for name, model_class in model_dict.items():
            setattr(builders, name, model_class)

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
            # Don't raise for status on logout, as session might already be expired
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
        """
        Perform a session request, with automatic re-login on 401 Unauthorized.
        """
        # Ensure we are logged in for non-persistent sessions
        if not self.persistent_login:
            self.login()

        try:
            resp = self.session.request(method, url, **kwargs)
            
            # If we get a 401, our session likely timed out.
            if resp.status_code == 401 and self.retry_on_idle_logout:
                self._logged_in = False
                self.login() # Re-authenticate
                resp = self.session.request(method, url, **kwargs) # Retry the request

            _raise_with_detail(resp)
            return resp
        finally:
            # Logout after each request for non-persistent sessions
            if not self.persistent_login:
                self.logout()