"""easy_acumatica.client
======================

A lightweight wrapper around the **contract-based REST API** of
Acumatica ERP.  The :class:`AcumaticaClient` class handles the entire
session lifecycle:

* opens a persistent :class:`requests.Session`;
* logs in automatically when the object is created;
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
>>> contact = client.contacts.get_contacts("24.200.001")
>>> client.logout()  # optional - will also run automatically
"""
from __future__ import annotations

import atexit
from typing import Optional

import requests

# Sub‑services -------------------------------------------------------------
from .sub_services.records import RecordsService
from .sub_services.contacts import ContactsService
from .sub_services.inquiries import InquiriesService
from .sub_services.customers import CustomersService
from .sub_services.codes import CodesService
from .sub_services.files import FilesService
from .sub_services.accounts import AccountService
from .sub_services.transactions import TransactionsService
from .sub_services.actions import ActionsService
from .sub_services.activities import ActivitiesService
from .sub_services.payments import PaymentsService
from .sub_services.invoices import InvoicesService
from .sub_services.employees import EmployeesService
from .sub_services.leads import LeadsService
from .sub_services.tax_categories import TaxCategoryService
from .sub_services.ledgers import LedgersService
from .sub_services.cases import CasesService
from .sub_services.companies import CompaniesService
from .sub_services.manufacturing import ManufacturingService
from .sub_services.inventory import InventoryService
from .sub_services.sales_orders import SalesOrdersService
from .sub_services.shipments import ShipmentsService
from .sub_services.stock_items import StockItemsService
from .sub_services.service_orders import ServiceOrdersService
from .sub_services.purchase_orders import PurchaseOrdersService
from .sub_services.purchase_receipts import PurchaseReceiptsService
from .sub_services.time_entries import TimeEntriesService
from .sub_services.work_calendars import WorkCalendarsService
from .sub_services.work_locations import WorkLocationsService
from .sub_services.bills import BillsService
from .sub_services.boms import BomsService
from .sub_services.business_accounts import BusinessAccountsService
from .helpers import _raise_with_detail

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
    persistent_login : bool, default ``True``
        Whether to login once on client creation and only logout at program exit. 
        If false, client will login and logout before and after every function call.
    retry_on_idle_logout : bool, default ``True``
        Whether to retry function call if it recieves a 401 (Unathorized) error.
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
        persistent_login: bool = True,
        retry_on_idle_logout: bool = True,
    ) -> None:
        # --- public attributes --------------------------------------
        self.base_url: str = base_url.rstrip("/")
        self.session: requests.Session = requests.Session()
        self.verify_ssl: bool = verify_ssl
        self.tenant: str = tenant
        self.username: str = username
        self.password: str = password
        self.persistent_login: bool = persistent_login
        self.retry_on_idle_logout: bool = retry_on_idle_logout

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
        if persistent_login:
            self.login()

        # Ensure we always log out exactly once on normal interpreter exit
        if not AcumaticaClient._atexit_registered:
            atexit.register(self._atexit_logout)
            AcumaticaClient._atexit_registered = True

        # Service proxies --------------------------------------------------
        self.contacts: ContactsService = ContactsService(self)
        self.records: RecordsService = RecordsService(self)
        self.inquiries: InquiriesService = InquiriesService(self)
        self.customers: CustomersService = CustomersService(self)
        self.codes: CodesService = CodesService(self)
        self.files: FilesService = FilesService(self)
        self.accounts: AccountService = AccountService(self)
        self.transactions: TransactionsService = TransactionsService(self)
        self.actions: ActionsService = ActionsService(self)
        self.activities: ActivitiesService = ActivitiesService(self)
        self.payments: PaymentsService = PaymentsService(self)
        self.invoices: InvoicesService = InvoicesService(self)
        self.employees: EmployeesService = EmployeesService(self)
        self.leads: LeadsService = LeadsService(self)
        self.tax_categories: TaxCategoryService = TaxCategoryService(self)
        self.ledgers: LedgersService = LedgersService(self)
        self.cases: CasesService = CasesService(self)
        self.companies: CompaniesService = CompaniesService(self)
        self.manufacturing: ManufacturingService = ManufacturingService(self)
        self.inventory: InventoryService = InventoryService(self)
        self.sales_orders: SalesOrdersService = SalesOrdersService(self)
        self.shipments: ShipmentsService = ShipmentsService(self)
        self.stock_items: StockItemsService = StockItemsService(self)
        self.service_orders: ServiceOrdersService = ServiceOrdersService(self)
        self.purchase_orders: PurchaseOrdersService = PurchaseOrdersService(self)
        self.purchase_receipts: PurchaseReceiptsService = PurchaseReceiptsService(self)
        self.time_entries: TimeEntriesService = TimeEntriesService(self)
        self.work_calendars: WorkCalendarsService = WorkCalendarsService(self)
        self.work_locations: WorkLocationsService = WorkLocationsService(self)
        self.bills: BillsService = BillsService(self)
        self.boms: BomsService = BomsService(self)
        self.business_accounts: BusinessAccountsService = BusinessAccountsService(self)

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
        """Log out and invalidate the server-side session.

        This method is **idempotent**: calling it more than once is safe
        and will simply return HTTP 204 after the first successful call.

        Returns
        -------
        int
            HTTP status code (200 on success, 204 if no active session).
        """
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
        except Exception:
            # Avoid noisy tracebacks at interpreter shutdown
            pass

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        Perform a session request, raise on error, but if we get a 401
        and retry_on_idle_logout is True, automatically re-login and retry once.
        """
        # first attempt
        resp = getattr(self.session, method)(url, **kwargs)
        try:
            _raise_with_detail(resp)
            return resp
        except RuntimeError as exc:
            # only retry on 401 if enabled
            if resp.status_code == 401 and self.retry_on_idle_logout:
                # force a fresh login
                self._logged_in = False
                self.login()
                # retry exactly once
                resp = getattr(self.session, method)(url, **kwargs)
                _raise_with_detail(resp)
                return resp
            # re-raise any other error
            raise
    def get_endpoint_info(self):
        """
        Retrieves the Acumatica build version and a list of all endpoints
        and endpoint versions

        Args:
            None

        Returns:
            A dictionary where "version" contains Acumatica build information
            and "endpoints" which is a list of dictionaries, where each dictionary is an endpoint.
        """
        if not self.persistent_login:
            self.login()

        url = f"{self.base_url}/entity"

        resp = self._request("get", url, verify=self.verify_ssl)
        _raise_with_detail(resp)

        if not self.persistent_login:
            self.logout()

        return resp.json()

#-- Test Commit 1 --#