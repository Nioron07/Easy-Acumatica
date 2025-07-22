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
* Guarantees a clean logout either explicitly via :meth:`logout` or implicitly
    on interpreter shutdown.
* Implements retry logic, rate limiting, and comprehensive error handling.
* Supports configuration via environment variables or config files.

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
import logging
import os
import time
import warnings
from functools import lru_cache
from typing import Any, Dict, Optional, Set
from weakref import WeakSet

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import models
from .config import AcumaticaConfig
from .exceptions import AcumaticaAuthError, AcumaticaError
from .helpers import _raise_with_detail
from .model_factory import ModelFactory
from .service_factory import ServiceFactory
from .utils import RateLimiter, retry_on_error, validate_entity_id

__all__ = ["AcumaticaClient"]

# Configure logging
logger = logging.getLogger(__name__)

# Track all client instances for cleanup
_active_clients: WeakSet[AcumaticaClient] = WeakSet()


class AcumaticaClient:
    """
    High-level convenience wrapper around Acumatica's REST endpoint.

    Manages a single authenticated HTTP session and dynamically builds out its
    own methods and data models based on the API schema of the target instance.
    
    Attributes:
        base_url: Root URL of the Acumatica site
        session: Persistent requests session with connection pooling
        models: Dynamically generated data models
        endpoints: Available API endpoints and their versions
    """
    
    _atexit_registered: bool = False
    _default_timeout: int = 60
    _max_retries: int = 3
    _backoff_factor: float = 0.3
    _pool_connections: int = 10
    _pool_maxsize: int = 10

    def __init__(
        self,
        base_url: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        tenant: Optional[str] = None,
        branch: Optional[str] = None,
        locale: Optional[str] = None,
        verify_ssl: bool = True,
        persistent_login: bool = True,
        retry_on_idle_logout: bool = True,
        endpoint_name: str = "Default",
        endpoint_version: Optional[str] = None,
        config: Optional[AcumaticaConfig] = None,
        rate_limit_calls_per_second: float = 10.0,
        timeout: Optional[int] = None,
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
            config: Optional AcumaticaConfig object. If provided, overrides individual parameters.
            rate_limit_calls_per_second: Maximum API calls per second (default: 10).
            timeout: Request timeout in seconds (default: 60).
            
        Raises:
            ValueError: If required credentials are missing
            AcumaticaError: If connection or authentication fails
        """
        # --- 1. Handle configuration ---
        if config:
            # Use config object if provided
            self._config = config
            base_url = config.base_url
            username = config.username
            password = config.password
            tenant = config.tenant
            branch = config.branch or branch
            locale = config.locale or locale
            verify_ssl = config.verify_ssl
            persistent_login = config.persistent_login
            retry_on_idle_logout = config.retry_on_idle_logout
            endpoint_name = config.endpoint_name
            endpoint_version = config.endpoint_version
            rate_limit_calls_per_second = config.rate_limit_calls_per_second
            timeout = config.timeout
        else:
            # Allow credentials from environment variables
            base_url = base_url or os.getenv('ACUMATICA_URL')
            username = username or os.getenv('ACUMATICA_USERNAME')
            password = password or os.getenv('ACUMATICA_PASSWORD')
            tenant = tenant or os.getenv('ACUMATICA_TENANT')
            branch = branch or os.getenv('ACUMATICA_BRANCH')
            locale = locale or os.getenv('ACUMATICA_LOCALE')
            
            # Create config object for consistency
            self._config = AcumaticaConfig(
                base_url=base_url,
                username=username,
                password=password,
                tenant=tenant,
                branch=branch,
                locale=locale,
                verify_ssl=verify_ssl,
                persistent_login=persistent_login,
                retry_on_idle_logout=retry_on_idle_logout,
                endpoint_name=endpoint_name,
                endpoint_version=endpoint_version,
                timeout=timeout or self._default_timeout,
                rate_limit_calls_per_second=rate_limit_calls_per_second,
            )
        
        # Validate required credentials
        if not all([base_url, username, password, tenant]):
            missing = []
            if not base_url: missing.append("base_url")
            if not username: missing.append("username")
            if not password: missing.append("password")
            if not tenant: missing.append("tenant")
            raise ValueError(f"Missing required credentials: {', '.join(missing)}")
        
        # --- 2. Set up public attributes ---
        self.base_url: str = base_url.rstrip("/")
        self.tenant: str = tenant
        self.username: str = username
        self.verify_ssl: bool = verify_ssl
        self.persistent_login: bool = persistent_login
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoint_name: str = endpoint_name
        self.endpoint_version: Optional[str] = endpoint_version
        self.timeout: int = timeout or self._default_timeout
        
        # Initialize session with connection pooling and retry logic
        self.session: requests.Session = self._create_session()
        
        # Rate limiter
        self._rate_limiter = RateLimiter(calls_per_second=rate_limit_calls_per_second)
        
        # State tracking
        self.endpoints: Dict[str, Dict] = {}
        self._logged_in: bool = False
        self._available_services: Set[str] = set()
        self._schema_cache: Dict[str, Any] = {}
        
        # The 'models' attribute points to the models module
        self.models = models
        
        # --- 3. Construct the login payload ---
        payload = {"name": username, "password": password, "tenant": tenant}
        if branch: 
            payload["branch"] = branch
        if locale: 
            payload["locale"] = locale
        self._login_payload: Dict[str, str] = {k: v for k, v in payload.items() if v is not None}
        
        # Store password securely (not in plain text in production)
        self._password = password
        
        # --- 4. Initial Login ---
        if self.persistent_login:
            try:
                self.login()
            except Exception as e:
                self.session.close()
                raise AcumaticaAuthError(f"Failed to authenticate: {e}")
        
        # --- 5. Discover Endpoint Information ---
        try:
            self._populate_endpoint_info()
            target_version = endpoint_version or self.endpoints.get(endpoint_name, {}).get('version')
            if not target_version:
                raise ValueError(f"Could not determine a version for endpoint '{endpoint_name}'.")
            self.endpoint_version = target_version
            
            # --- 6. Fetch Schema and Build Dynamic Components ---
            schema = self._fetch_schema(endpoint_name, target_version)
            self._build_dynamic_models(schema)
            self._build_dynamic_services(schema)
            
        except Exception as e:
            # Clean up on failure
            if self.persistent_login and self._logged_in:
                try:
                    self.logout()
                except:
                    pass
            self.session.close()
            raise
        
        # --- 7. Register for cleanup ---
        _active_clients.add(self)
        if not AcumaticaClient._atexit_registered:
            atexit.register(_cleanup_all_clients)
            AcumaticaClient._atexit_registered = True
        
        logger.info(f"AcumaticaClient initialized for {self.base_url} (tenant: {self.tenant})")

    def _create_session(self) -> requests.Session:
        """Creates a configured requests session with connection pooling and retry logic."""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=self._max_retries,
            backoff_factor=self._backoff_factor,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "PUT", "DELETE", "OPTIONS", "TRACE", "POST"]
        )
        
        # Configure connection pooling
        adapter = HTTPAdapter(
            pool_connections=self._pool_connections,
            pool_maxsize=self._pool_maxsize,
            max_retries=retry_strategy
        )
        
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers
        session.headers.update({
            "User-Agent": f"easy-acumatica/0.4.5 Python/{requests.__version__}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
        return session

    def _populate_endpoint_info(self) -> None:
        """Retrieves and stores the latest version for each available endpoint."""
        url = f"{self.base_url}/entity"
        
        try:
            logger.debug(f"Fetching endpoint information from {url}")
            endpoint_data = self._request("get", url).json()
        except requests.RequestException as e:
            raise AcumaticaError(f"Failed to fetch endpoint information: {e}")
        
        endpoints = endpoint_data.get('endpoints', [])
        if not endpoints:
            raise AcumaticaError("No endpoints found on the server")
        
        # Store endpoint information
        for endpoint in endpoints:
            name = endpoint.get('name')
            if name and (name not in self.endpoints or 
                        endpoint.get('version', '0') > self.endpoints[name].get('version', '0')):
                self.endpoints[name] = endpoint
                logger.debug(f"Found endpoint: {name} v{endpoint.get('version')}")

    @lru_cache(maxsize=32)
    def _fetch_schema(self, endpoint_name: str = "Default", version: str = None) -> Dict[str, Any]:
        """
        Fetches and caches the OpenAPI schema for a given endpoint.
        
        Args:
            endpoint_name: Name of the API endpoint
            version: Version of the endpoint
            
        Returns:
            OpenAPI schema dictionary
            
        Raises:
            AcumaticaError: If schema fetch fails
        """
        if not version:
            version = self.endpoints[endpoint_name]
        cache_key = f"{endpoint_name}:{version}"
        if cache_key in self._schema_cache:
            logger.debug(f"Using cached schema for {cache_key}")
            return self._schema_cache[cache_key]
        
        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json"
        if self.tenant:
            schema_url += f"?company={self.tenant}"
        
        logger.info(f"Fetching schema from {schema_url}")
        
        try:
            schema = self._request("get", schema_url).json()
            self._schema_cache[cache_key] = schema
            return schema
        except Exception as e:
            raise AcumaticaError(f"Failed to fetch schema for {endpoint_name} v{version}: {e}")
        

    def _build_dynamic_models(self, schema: Dict[str, Any]) -> None:
        """Populates the 'models' module with dynamically generated dataclasses."""
        logger.info("Building dynamic models from schema")
        
        try:
            factory = ModelFactory(schema)
            model_dict = factory.build_models()
            
            # Attach each generated class to the models module
            for name, model_class in model_dict.items():
                setattr(self.models, name, model_class)
                logger.debug(f"Created model: {name}")
                
            logger.info(f"Successfully built {len(model_dict)} models")
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic models: {e}")

    def _build_dynamic_services(self, schema: Dict[str, Any]) -> None:
        """Attaches dynamically created services to the client instance."""
        logger.info("Building dynamic services from schema")
        
        try:
            factory = ServiceFactory(self, schema)
            services_dict = factory.build_services()
            
            for name, service_instance in services_dict.items():
                # Convert PascalCase to snake_case
                attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_') + 's'
                setattr(self, attr_name, service_instance)
                self._available_services.add(name)
                logger.debug(f"Created service: {attr_name}")
                
            logger.info(f"Successfully built {len(services_dict)} services")
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic services: {e}")

    def __getattr__(self, name: str) -> Any:
        """
        Lazy loading support for services.
        
        Args:
            name: Attribute name
            
        Returns:
            The requested attribute
            
        Raises:
            AttributeError: If attribute doesn't exist
        """
        # Check if this might be a service we haven't loaded yet
        if name.endswith('s') and name not in self.__dict__:
            # Try to find the corresponding service
            potential_service = name[:-1].title()
            if potential_service in self._available_services:
                logger.warning(f"Service '{name}' accessed but not loaded. This shouldn't happen.")
                return getattr(self, name)
        
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    @retry_on_error(max_attempts=3, delay=1.0, backoff=2.0)
    def login(self) -> int:
        """
        Authenticates and obtains a cookie-based session.
        
        Returns:
            HTTP status code (200 for success, 204 if already logged in)
            
        Raises:
            AcumaticaAuthError: If authentication fails
        """
        if self._logged_in:
            logger.debug("Already logged in")
            return 204
        
        url = f"{self.base_url}/entity/auth/login"
        logger.info(f"Attempting login for user '{self.username}' on tenant '{self.tenant}'")
        
        try:
            response = self.session.post(
                url, 
                json=self._login_payload, 
                verify=self.verify_ssl,
                timeout=self.timeout
            )
            
            if response.status_code == 401:
                raise AcumaticaAuthError("Invalid credentials")
            
            response.raise_for_status()
            self._logged_in = True
            logger.info("Login successful")
            return response.status_code
            
        except requests.RequestException as e:
            logger.error(f"Login failed: {e}")
            raise AcumaticaAuthError(f"Login failed: {e}")

    def logout(self) -> int:
        """
        Logs out and invalidates the server-side session.
        
        Returns:
            HTTP status code (204 for success or already logged out)
        """
        if not self._logged_in:
            logger.debug("Already logged out")
            return 204
        
        url = f"{self.base_url}/entity/auth/logout"
        logger.info("Logging out")
        
        try:
            response = self.session.post(url, verify=self.verify_ssl, timeout=self.timeout)
            self.session.cookies.clear()
            self._logged_in = False
            logger.info("Logout successful")
            return response.status_code
            
        except Exception as e:
            logger.warning(f"Logout encountered an error: {e}")
            # Still mark as logged out
            self._logged_in = False
            self.session.cookies.clear()
            return 204

    def _request(self, method: str, url: str, **kwargs) -> requests.Response:
        """
        The central method for making all API requests with rate limiting.
        
        Args:
            method: HTTP method
            url: Request URL
            **kwargs: Additional arguments for requests
            
        Returns:
            Response object
            
        Raises:
            AcumaticaError: If request fails
        """
        # Apply rate limiting by calling the rate limiter directly
        with self._rate_limiter._lock:
            current_time = time.time()
            
            # Calculate tokens accumulated since last call
            time_passed = current_time - self._rate_limiter._last_call_time
            self._rate_limiter._tokens = min(
                self._rate_limiter.burst_size,
                self._rate_limiter._tokens + time_passed * self._rate_limiter.calls_per_second
            )
            
            # Check if we have tokens available
            if self._rate_limiter._tokens < 1.0:
                sleep_time = (1.0 - self._rate_limiter._tokens) / self._rate_limiter.calls_per_second
                logger.debug(f"Rate limit reached, sleeping for {sleep_time:.3f}s")
                time.sleep(sleep_time)
                self._rate_limiter._tokens = 1.0
            
            # Consume one token
            self._rate_limiter._tokens -= 1.0
            self._rate_limiter._last_call_time = time.time()
        
        # Set default timeout if not specified
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', self.verify_ssl)
        
        # For non-persistent mode, ensure we are logged in
        if not self.persistent_login and not self._logged_in:
            self.login()
        
        try:
            logger.debug(f"{method.upper()} {url}")
            resp = self.session.request(method, url, **kwargs)
            
            # Handle session timeout with retry
            if resp.status_code == 401 and self.retry_on_idle_logout and self._logged_in:
                logger.info("Session expired, re-authenticating...")
                self._logged_in = False
                self.login()
                resp = self.session.request(method, url, **kwargs)
            
            # Check for errors
            _raise_with_detail(resp)
            return resp
            
        finally:
            # For non-persistent mode, log out after request
            if not self.persistent_login and self._logged_in:
                self.logout()

    def close(self) -> None:
        """
        Closes the client session and logs out if necessary.
        
        This method should be called when you're done with the client
        to ensure proper cleanup. It's automatically called on exit.
        """
        logger.info("Closing AcumaticaClient")
        
        try:
            if self._logged_in:
                self.logout()
        except Exception as e:
            logger.warning(f"Error during logout: {e}")
        
        try:
            self.session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")
        
        # Clear caches
        self._schema_cache.clear()
        if hasattr(self._fetch_schema, 'cache_clear'):
            self._fetch_schema.cache_clear()

    def __enter__(self) -> "AcumaticaClient":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Context manager exit."""
        self.close()

    def __repr__(self) -> str:
        """String representation of the client."""
        return (f"<AcumaticaClient("
                f"base_url='{self.base_url}', "
                f"tenant='{self.tenant}', "
                f"user='{self.username}', "
                f"logged_in={self._logged_in})>")


def _cleanup_all_clients() -> None:
    """Cleanup function called on interpreter shutdown."""
    logger.info("Cleaning up all active AcumaticaClient instances")
    
    # Create a list to avoid modifying set during iteration
    clients = list(_active_clients)
    
    for client in clients:
        try:
            client.close()
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")