"""easy_acumatica.client
======================

A lightweight wrapper around the **contract-based REST API** of
Acumatica ERP. The :class:`AcumaticaClient` class handles the entire
session lifecycle with enhanced caching and automatic .env file loading.

Its key features include:
* Opens a persistent :class:`requests.Session` for efficient communication.
* Handles login and logout automatically.
* Automatically loads credentials from .env files when no parameters provided.
* Dynamically generates data models (e.g., `Contact`, `Bill`) from the live
    endpoint schema, ensuring they are always up-to-date and include custom fields.
* Dynamically generates service layers (e.g., `client.contacts`, `client.bills`)
    with methods that directly correspond to available API operations.
* Intelligent caching system for schemas and generated methods to improve startup time.
* Comprehensive utility methods for introspection and debugging.
* Guarantees a clean logout either explicitly via :meth:`logout` or implicitly
    on interpreter shutdown.
* Implements retry logic, rate limiting, and comprehensive error handling.
* Supports configuration via environment variables or config files.

Usage example
-------------
>>> from easy_acumatica import AcumaticaClient
>>> 
>>> # Method 1: No arguments - automatically loads from .env file
>>> client = AcumaticaClient()  # Searches for .env in current directory
>>> 
>>> # Method 2: Specify .env file location
>>> client = AcumaticaClient(env_file="path/to/.env")
>>> 
>>> # Method 3: Traditional explicit parameters
>>> client = AcumaticaClient(
...     base_url="https://demo.acumatica.com",
...     username="admin",
...     password="Pa$$w0rd",
...     tenant="Company",
...     cache_methods=True)  # Enable caching for faster subsequent startups
>>>
>>> # Use utility methods to explore the API
>>> print(f"Available models: {len(client.list_models())}")
>>> print(f"Available services: {len(client.list_services())}")
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
import contextlib
import gzip
import hashlib
import inspect
import json
import logging
import os
import pickle
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from weakref import WeakSet
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter

from . import models
from .config import AcumaticaConfig
from .exceptions import AcumaticaAuthError, AcumaticaError, AcumaticaConnectionError
from .helpers import _raise_with_detail
from .model_factory import ModelFactory
from .service_factory import ServiceFactory, to_snake_case
from .core import BatchMethodWrapper
from .utils import RateLimiter
from .core import BaseDataClassModel, BaseService
from .scheduler import TaskScheduler

__all__ = ["AcumaticaClient"]

# Logger instance (not used directly, available for external use)
logger = logging.getLogger(__name__)

# Track all client instances for cleanup
_active_clients: WeakSet[AcumaticaClient] = WeakSet()


# Built-in BaseService methods that should be excluded when introspecting
# inquiry methods on the dynamically-built ``Inquiries`` service. Any other
# public, callable attribute on that service is treated as a generated
# inquiry endpoint.
_BASE_SERVICE_METHODS = frozenset({
    '_get', '_put', '_post_action', '_delete', '_get_files',
    '_get_schema', '_get_inquiry', '_request', '_get_url',
    '_get_by_keys',
})


def load_env_file(env_file_path: Path) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file_path: Path to the .env file
        
    Returns:
        Dictionary of environment variables
    """
    env_vars = {}
    
    if not env_file_path.exists():
        return env_vars
    
    try:
        with open(env_file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Split on first = only
                if '=' not in line:
                    continue
                
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # Remove quotes if present
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                elif value.startswith("'") and value.endswith("'"):
                    value = value[1:-1]
                
                env_vars[key] = value
                
    except Exception as e:
        logger.warning(f"Could not load .env file at {env_file_path}: {e}")

    return env_vars


def find_env_file(start_path: Optional[Path] = None) -> Optional[Path]:
    """
    Search for .env file starting from the given path and walking up directories.
    
    Args:
        start_path: Starting directory to search from. If None, uses caller's file directory.
        
    Returns:
        Path to .env file if found, None otherwise
    """
    if start_path is None:
        # Get the directory of the file that called AcumaticaClient
        frame = inspect.currentframe()
        try:
            # Walk up the stack to find the caller outside this module
            caller_frame = frame
            while caller_frame:
                caller_frame = caller_frame.f_back
                if caller_frame and caller_frame.f_code.co_filename != __file__:
                    start_path = Path(caller_frame.f_code.co_filename).parent
                    break
            
            if start_path is None:
                start_path = Path.cwd()
                
        finally:
            del frame
    
    # Search for .env file in current directory and parent directories
    current_path = Path(start_path).resolve()
    
    for path in [current_path] + list(current_path.parents):
        env_file = path / '.env'
        if env_file.exists():
            return env_file

    return None


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
        cache_enabled: Whether method caching is enabled
        cache_dir: Directory for storing cached data
    """
    
    _atexit_registered: bool = False
    _default_timeout: int = 60
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
        cache_methods: bool = False,
        cache_ttl_hours: int = 24,
        schema_cache_ttl_hours: int = 1,
        cache_dir: Optional[Path] = None,
        force_rebuild: bool = False,
        env_file: Optional[Union[str, Path]] = None,
        auto_load_env: bool = True,
    ) -> None:
        """
        Initializes the client, logs in, and builds the dynamic services.

        Args:
            base_url: Root URL of the Acumatica site. If None and auto_load_env=True, 
                     loads from ACUMATICA_URL in .env file or environment.
            username: Username for authentication. If None and auto_load_env=True,
                     loads from ACUMATICA_USERNAME in .env file or environment.
            password: Password for authentication. If None and auto_load_env=True,
                     loads from ACUMATICA_PASSWORD in .env file or environment.
            tenant: Tenant/company code. If None and auto_load_env=True,
                   loads from ACUMATICA_TENANT in .env file or environment.
            branch: Branch code within the tenant (optional).
            locale: UI locale, such as "en-US" (optional).
            verify_ssl: Whether to validate TLS certificates.
            persistent_login: If True, logs in once on creation and logs out at exit.
            retry_on_idle_logout: If True, automatically re-login and retry on 401 errors.
            endpoint_name: The name of the API endpoint to use (default: "Default").
            endpoint_version: A specific version of the endpoint to use.
            config: Optional AcumaticaConfig object. Overrides individual parameters.
            rate_limit_calls_per_second: Maximum API calls per second (default: 10).
            timeout: Request timeout in seconds (default: 60).
            cache_methods: Enable caching of generated models and services for faster startup.
            cache_ttl_hours: Time-to-live for cached data in hours (default: 24).
            schema_cache_ttl_hours: TTL for the on-disk raw OpenAPI schema cache (default: 1).
                Shorter than cache_ttl_hours since schema freshness matters more when admins
                deploy customization packages. Call :meth:`refresh_schema` for explicit invalidation.
                Must be <= cache_ttl_hours.
            cache_dir: Directory for storing cache files. Defaults to ~/.easy_acumatica_cache
            force_rebuild: Force rebuilding of models and services, ignoring cache.
            env_file: Path to .env file to load. If None and auto_load_env=True, searches automatically.
            auto_load_env: If True, automatically searches for and loads .env files when no credentials provided.
            
        Raises:
            ValueError: If required credentials are missing and cannot be loaded from environment
            AcumaticaError: If connection or authentication fails
            
        Example:
            >>> # Automatically load from .env file in current directory
            >>> client = AcumaticaClient()
            >>> 
            >>> # Load from specific .env file  
            >>> client = AcumaticaClient(env_file="config/.env")
            >>>
            >>> # Traditional explicit parameters
            >>> client = AcumaticaClient(
            ...     base_url="https://demo.acumatica.com",
            ...     username="admin",
            ...     password="password",
            ...     tenant="Company",
            ...     cache_methods=True
            ... )
        """
        # --- 1. Handle automatic environment loading ---
        env_vars_loaded = {}

        # Disable auto-loading if all credentials are provided
        if base_url and username and password and tenant:
            auto_load_env = False

        if auto_load_env and not config:
            # Check if we need to load environment variables
            missing_credentials = not all([base_url, username, password, tenant])

            if missing_credentials:
                # Load from specified .env file or search for one
                if env_file:
                    env_file_path = Path(env_file)
                    if env_file_path.exists():
                        env_vars_loaded = load_env_file(env_file_path)
                    else:
                        pass  # Specified .env file not found
                else:
                    # Search for .env file automatically
                    found_env_file = find_env_file()
                    if found_env_file:
                        env_vars_loaded = load_env_file(found_env_file)
                
                # Apply loaded environment variables to os.environ temporarily
                # so they can be picked up by the config loading logic
                original_env = {}
                for key, value in env_vars_loaded.items():
                    if key not in os.environ:  # Don't override existing env vars
                        original_env[key] = os.environ.get(key)
                        os.environ[key] = value
                
                # Clean up function to restore original environment
                def restore_env():
                    for key, original_value in original_env.items():
                        if original_value is None:
                            os.environ.pop(key, None)
                        else:
                            os.environ[key] = original_value
        
        # --- 2. Handle configuration ---
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
            cache_methods = getattr(config, 'cache_methods', cache_methods)
            cache_ttl_hours = getattr(config, 'cache_ttl_hours', cache_ttl_hours)
            schema_cache_ttl_hours = getattr(config, 'schema_cache_ttl_hours', schema_cache_ttl_hours)
            cache_dir = getattr(config, 'cache_dir', cache_dir)
            force_rebuild = getattr(config, 'force_rebuild', force_rebuild)
        else:
            # Load from environment variables (including those from .env file)
            base_url = base_url or os.getenv('ACUMATICA_URL')
            username = username or os.getenv('ACUMATICA_USERNAME')
            password = password or os.getenv('ACUMATICA_PASSWORD')
            tenant = tenant or os.getenv('ACUMATICA_TENANT')
            branch = branch or os.getenv('ACUMATICA_BRANCH')
            locale = locale or os.getenv('ACUMATICA_LOCALE')
            
            # Load additional options from environment
            if os.getenv('ACUMATICA_CACHE_METHODS', '').lower() in ('true', '1', 'yes', 'on'):
                cache_methods = True
            if os.getenv('ACUMATICA_CACHE_TTL_HOURS'):
                try:
                    cache_ttl_hours = int(os.getenv('ACUMATICA_CACHE_TTL_HOURS'))
                except ValueError:
                    pass
            if os.getenv('ACUMATICA_SCHEMA_CACHE_TTL_HOURS'):
                try:
                    schema_cache_ttl_hours = int(os.getenv('ACUMATICA_SCHEMA_CACHE_TTL_HOURS'))
                except ValueError:
                    pass
            
            # Create config object for consistency
            self._config = AcumaticaConfig(
                base_url=base_url or "",  # Temporary, will validate below
                username=username or "",
                password=password or "",
                tenant=tenant or "",
                branch=branch,
                locale=locale,
                verify_ssl=verify_ssl,
                persistent_login=persistent_login,
                retry_on_idle_logout=retry_on_idle_logout,
                endpoint_name=endpoint_name,
                endpoint_version=endpoint_version,
                timeout=timeout or self._default_timeout,
                rate_limit_calls_per_second=rate_limit_calls_per_second,
                cache_methods=cache_methods,
                cache_ttl_hours=cache_ttl_hours,
                schema_cache_ttl_hours=schema_cache_ttl_hours,
                cache_dir=cache_dir,
                force_rebuild=force_rebuild,
            )
        
        # Clean up environment variables if we loaded them
        if env_vars_loaded and 'original_env' in locals():
            restore_env()
        
        # Validate required credentials
        if not all([base_url, username, password, tenant]):
            missing = []
            if not base_url: missing.append("base_url (ACUMATICA_URL)")
            if not username: missing.append("username (ACUMATICA_USERNAME)")
            if not password: missing.append("password (ACUMATICA_PASSWORD)")
            if not tenant: missing.append("tenant (ACUMATICA_TENANT)")

            error_msg = f"Missing required credentials: {', '.join(missing)}"

            if auto_load_env and not env_file and not find_env_file():
                error_msg += "\n\nNo .env file found. Create a .env file with your credentials:"
                error_msg += "\nACUMATICA_URL=https://your-instance.acumatica.com"
                error_msg += "\nACUMATICA_USERNAME=your-username"
                error_msg += "\nACUMATICA_PASSWORD=your-password"
                error_msg += "\nACUMATICA_TENANT=your-tenant"
                error_msg += "\nACUMATICA_CACHE_METHODS=true"
            elif auto_load_env:
                error_msg += f"\n\nCheck your .env file contains the required variables."

            raise ValueError(error_msg)
        
        # --- 3. Set up public attributes ---
        self.base_url: str = base_url.rstrip("/")
        self.tenant: str = tenant
        self.username: str = username
        self.verify_ssl: bool = verify_ssl
        self.persistent_login: bool = persistent_login

        # Scheduler instance (created on demand)
        self._scheduler: Optional[TaskScheduler] = None
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoint_name: str = endpoint_name
        self.endpoint_version: Optional[str] = endpoint_version
        self.timeout: int = timeout or self._default_timeout
        
        # Cache configuration
        self.cache_enabled: bool = cache_methods
        self.cache_ttl_hours: int = cache_ttl_hours
        self.schema_cache_ttl_hours: int = schema_cache_ttl_hours
        self.force_rebuild: bool = force_rebuild
        self.cache_dir: Path = cache_dir or Path.home() / ".easy_acumatica_cache"
        self._cache_dir_overridden: bool = cache_dir is not None
        # Serializes concurrent disk-cache reads and writes within one process.
        # Cross-process safety is provided by atomic temp-file + os.replace.
        self._cache_lock: threading.RLock = threading.RLock()
        
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session with connection pooling and retry logic.
        # Stored on the underlying _session attr so the public ``session``
        # property can layer in a thread-local override (used by BatchCall
        # to give each worker thread its own authenticated session without
        # racing other threads).
        self._session: requests.Session = self._create_session()
        # Thread-local holder for `session` / `_logged_in` overrides set by
        # ``with self._use_thread_session(session):``.
        self._thread_local = threading.local()

        # Rate limiter
        self._rate_limiter = RateLimiter(calls_per_second=rate_limit_calls_per_second)

        # State tracking
        self.endpoints: Dict[str, Dict] = {}
        self._logged_in_default: bool = False
        self._available_services: Set[str] = set()
        self._schema_cache: Dict[str, Any] = {}
        self._model_classes: Dict[str, Type[BaseDataClassModel]] = {}
        self._service_instances: Dict[str, BaseService] = {}
        # Per-service ``$adHocSchema`` responses keyed by entity tag.
        # Populated by ``_discover_custom_fields``; persisted alongside
        # the differential cache so repeated connects don't re-fetch.
        self._ad_hoc_schemas: Dict[str, Dict[str, Any]] = {}
        
        # Performance metrics
        self._startup_time: Optional[float] = None
        self._cache_hits: int = 0
        self._cache_misses: int = 0
        
        # The 'models' attribute points to the models module
        self.models = models
        
        # --- 4. Construct the login payload ---
        payload = {"name": username, "password": password, "tenant": tenant}
        if branch: 
            payload["branch"] = branch
        if locale: 
            payload["locale"] = locale
        self._login_payload: Dict[str, str] = {k: v for k, v in payload.items() if v is not None}
        
        # Store password securely (not in plain text in production)
        self._password = password
        
        # --- 5. Initial Setup with Performance Tracking ---
        startup_start = time.time()
        
        try:
            # Initial Login
            if self.persistent_login:
                self.login()
            
            # Discover Endpoint Information
            self._populate_endpoint_info()
            target_version = endpoint_version or self.endpoints.get(endpoint_name, {}).get('version')
            if not target_version:
                raise ValueError(f"Could not determine a version for endpoint '{endpoint_name}'.")
            self.endpoint_version = target_version
            
            # Build Dynamic Components with Caching
            self._build_components()
            
        except Exception as e:
            # Clean up on failure
            if self.persistent_login and self._logged_in:
                try:
                    self.logout()
                except Exception as logout_err:
                    logger.debug(f"Logout during init cleanup failed: {logout_err}")
            self.session.close()
            raise
        
        # Record startup performance
        self._startup_time = time.time() - startup_start
        
        # --- 6. Register for cleanup ---
        _active_clients.add(self)
        if not AcumaticaClient._atexit_registered:
            atexit.register(_cleanup_all_clients)
            AcumaticaClient._atexit_registered = True
        
        # Track initialization stats
        self._init_stats = {
            'startup_time': self._startup_time,
            'cache_enabled': self.cache_enabled,
            'models_loaded': len(self._model_classes),
            'services_loaded': len(self._service_instances)
        }

    # --- Thread-local session override -------------------------------------
    #
    # ``session`` and ``_logged_in`` are exposed as properties so that batch
    # workers can temporarily redirect them on a per-thread basis without
    # mutating shared state. Without this, two BatchCall workers would race
    # on ``client.session = ...`` and clobber each other (and any foreground
    # caller using the same client mid-batch).

    @property
    def session(self) -> requests.Session:
        override = getattr(self._thread_local, 'session', None)
        return override if override is not None else self._session

    @session.setter
    def session(self, value: requests.Session) -> None:
        # Plain assignment goes to the shared default; thread overrides
        # are managed exclusively through _use_thread_session().
        self._session = value

    @property
    def _logged_in(self) -> bool:
        override = getattr(self._thread_local, 'logged_in', None)
        return override if override is not None else self._logged_in_default

    @_logged_in.setter
    def _logged_in(self, value: bool) -> None:
        # When a thread override is active, write to the override so the
        # owning thread keeps a coherent view; otherwise write through to
        # the shared default.
        if getattr(self._thread_local, 'session', None) is not None:
            self._thread_local.logged_in = value
        else:
            self._logged_in_default = value

    @contextlib.contextmanager
    def _use_thread_session(self, session: requests.Session, logged_in: bool = True):
        """Scope a thread-local session override. Used by BatchCall to give
        each worker its own authenticated session without racing other
        workers or any foreground call on the same client.
        """
        prev_session = getattr(self._thread_local, 'session', None)
        prev_logged_in = getattr(self._thread_local, 'logged_in', None)
        self._thread_local.session = session
        self._thread_local.logged_in = logged_in
        try:
            yield
        finally:
            if prev_session is None:
                # Clean removal so the next call sees no override.
                if hasattr(self._thread_local, 'session'):
                    del self._thread_local.session
                if hasattr(self._thread_local, 'logged_in'):
                    del self._thread_local.logged_in
            else:
                self._thread_local.session = prev_session
                self._thread_local.logged_in = prev_logged_in

    def _create_session(self) -> requests.Session:
        """
        Creates a configured requests session with connection pooling.

        No automatic HTTP retry. Server errors (5xx, 429) are surfaced
        immediately via ``_raise_with_detail`` so the caller sees the actual
        response body instead of a generic "too many 500 error responses"
        wrapper. If you need retries, add them at the call site.
        """
        session = requests.Session()

        adapter = HTTPAdapter(
            pool_connections=self._pool_connections,
            pool_maxsize=self._pool_maxsize,
            max_retries=0,
        )

        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Set default headers. Pull our version from package metadata so
        # the User-Agent doesn't drift away from setup config on releases.
        try:
            from importlib.metadata import PackageNotFoundError, version as _pkg_version
            try:
                _ea_version = _pkg_version("easy_acumatica")
            except PackageNotFoundError:
                _ea_version = "unknown"
        except ImportError:  # pragma: no cover
            _ea_version = "unknown"
        session.headers.update({
            "User-Agent": f"easy-acumatica/{_ea_version} Python/{requests.__version__}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        })
        
        return session

    def _populate_endpoint_info(self) -> None:
        """Retrieves and stores the latest version for each available endpoint."""
        url = f"{self.base_url}/entity"
        
        try:
            response = self._request("get", url)
            endpoint_data = response.json()
        except requests.RequestException as e:
            raise AcumaticaConnectionError(f"Failed to fetch endpoint information: {e}")
        except json.JSONDecodeError:
            raise AcumaticaConnectionError("Failed to decode endpoint JSON. The URL may be incorrect or the server may be down.")

        endpoints = endpoint_data.get('endpoints', [])
        if not endpoints:
            raise AcumaticaConnectionError("No endpoints found on the server. Please check the base_url.")
        
        # Store endpoint information. Compare versions component-wise
        # ("24.200.001" vs "9.1") rather than lexicographically, which
        # would otherwise treat "9.1" as greater than "24.200.001".
        def _version_tuple(v: str) -> tuple:
            try:
                return tuple(int(p) for p in (v or '0').split('.'))
            except (ValueError, AttributeError):
                return (0,)

        for endpoint in endpoints:
            name = endpoint.get('name')
            if name and (
                name not in self.endpoints
                or _version_tuple(endpoint.get('version', '0'))
                > _version_tuple(self.endpoints[name].get('version', '0'))
            ):
                self.endpoints[name] = endpoint

    def _build_components(self) -> None:
        """Build models and services with differential caching support."""
        if not self.cache_enabled:
            # No caching - build everything from scratch
            schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
            self._build_dynamic_models(schema)
            self._build_dynamic_services(schema)
            self._discover_custom_fields()
            return

        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Always fetch current schema and inquiries to compare
        current_schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
        current_inquiries_xml = None
        
        try:
            current_inquiries_xml = self._fetch_gi_xml()
        except Exception as e:
            # GI XML is optional - some tenants don't expose it - but
            # silently dropping the error here used to mask real
            # connectivity / auth bugs because the outer caller also
            # swallowed exceptions. Log it so users can see what failed.
            logger.warning(f"Could not fetch Generic Inquiries XML: {e}")
        
        if self.force_rebuild or not cache_file.exists():
            # Fresh build
            self._build_dynamic_models(current_schema)
            self._build_dynamic_services(current_schema)
            if current_inquiries_xml:
                self._build_inquiries_service(current_inquiries_xml)
            self._discover_custom_fields()
            self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)
            self._cache_misses += 1
            return

        # Load existing cache for differential comparison
        try:
            cached_data = self._load_differential_cache(cache_file)
            if cached_data is None:
                # Cache invalid, rebuild everything
                self._build_dynamic_models(current_schema)
                self._build_dynamic_services(current_schema)
                if current_inquiries_xml:
                    self._build_inquiries_service(current_inquiries_xml)
                self._discover_custom_fields()
                self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)
                self._cache_misses += 1
                return

            # Perform differential update. If the OpenAPI schema hash
            # is unchanged we can also reuse the cached $adHocSchema
            # responses (custom fields don't move on their own without
            # a customization redeploy, which usually bumps the schema
            # too). Otherwise fall through to a fresh sweep.
            self._perform_differential_update(cached_data, current_schema, current_inquiries_xml)
            current_schema_hash = self._calculate_schema_hash(current_schema)
            cached_schema_hash = cached_data.get('schema_hash')
            cached_ad_hoc = cached_data.get('ad_hoc_schemas') if isinstance(cached_data, dict) else None
            if (
                cached_schema_hash == current_schema_hash
                and isinstance(cached_ad_hoc, dict)
                and cached_ad_hoc
            ):
                self._discover_custom_fields(cached_schemas=cached_ad_hoc)
            else:
                self._discover_custom_fields()
            self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)

        except Exception as e:
            # Differential caching failed, rebuild from scratch
            self._build_dynamic_models(current_schema)
            self._build_dynamic_services(current_schema)
            if current_inquiries_xml:
                self._build_inquiries_service(current_inquiries_xml)
            self._discover_custom_fields()
            self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)
            self._cache_misses += 1

    def _save_differential_cache(self, cache_file: Path, schema: Dict[str, Any], inquiries_xml_path: str = None) -> None:
        """Save cache with differential tracking information."""
        try:
            # Calculate hashes for each component
            model_hashes = self._calculate_model_hashes(schema)
            service_hashes = self._calculate_service_hashes(schema)
            inquiry_hashes = self._calculate_inquiry_hashes(inquiries_xml_path) if inquiries_xml_path else {}
            
            cache_data = {
                'version': '1.2',  # Cache format version (added ad_hoc_schemas)
                'timestamp': time.time(),
                'schema_hash': self._calculate_schema_hash(schema),
                'inquiries_hash': self._calculate_inquiries_xml_hash(inquiries_xml_path) if inquiries_xml_path else None,
                'model_hashes': model_hashes,
                'service_hashes': service_hashes,
                'inquiry_hashes': inquiry_hashes,
                'models': self._model_classes.copy(),
                'service_definitions': self._extract_service_definitions(schema),
                'inquiry_definitions': self._extract_inquiry_definitions(inquiries_xml_path) if inquiries_xml_path else {},
                # Per-tag ``$adHocSchema`` responses captured during the
                # last custom-field discovery sweep. Reused on the next
                # connect when the OpenAPI schema hash is unchanged so
                # we avoid N HTTP round-trips on every startup.
                'ad_hoc_schemas': dict(self._ad_hoc_schemas),
                'endpoint_info': {
                    'name': self.endpoint_name,
                    'version': self.endpoint_version,
                    'base_url': self.base_url,
                    'tenant': self.tenant
                }
            }
            
            # Save to a thread/PID-unique temp file first to avoid concurrent
            # writers clobbering a shared temp path, then os.replace atomically.
            temp_file = cache_file.with_suffix(
                f'.tmp.{os.getpid()}.{threading.get_ident()}'
            )
            with self._cache_lock:
                with open(temp_file, 'wb') as f:
                    pickle.dump(cache_data, f)
                os.replace(temp_file, cache_file)

        except Exception as e:
            logger.warning(f"Failed to save differential cache: {e}")

    def _load_differential_cache(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """
        Load and validate the differential cache pickle.

        Returns None on miss, expired TTL, version mismatch, endpoint mismatch,
        or any read/deserialize error. TTL is checked against the file's mtime
        rather than the embedded ``timestamp`` so a backwards system-clock jump
        can never make stale caches look fresh.
        """
        with self._cache_lock:
            try:
                cache_age = time.time() - cache_file.stat().st_mtime
            except OSError:
                return None
            if cache_age > (self.cache_ttl_hours * 3600):
                return None

            try:
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
            except (OSError, pickle.UnpicklingError, EOFError, AttributeError):
                return None

            if cached_data.get('version') not in ('1.0', '1.1', '1.2'):
                return None

            endpoint_info = cached_data.get('endpoint_info', {})
            if (endpoint_info.get('name') != self.endpoint_name or
                endpoint_info.get('version') != self.endpoint_version or
                endpoint_info.get('base_url') != self.base_url or
                endpoint_info.get('tenant') != self.tenant):
                return None

            return cached_data

    def _perform_differential_update(self, cached_data: Dict[str, Any], current_schema: Dict[str, Any], inquiries_xml_path: str = None) -> None:
        """Perform differential update of models, services, and inquiries."""
        # Perform differential cache update
        
        # Calculate current hashes
        current_model_hashes = self._calculate_model_hashes(current_schema)
        current_service_hashes = self._calculate_service_hashes(current_schema)
        current_inquiry_hashes = self._calculate_inquiry_hashes(inquiries_xml_path) if inquiries_xml_path else {}
        
        cached_model_hashes = cached_data.get('model_hashes', {})
        cached_service_hashes = cached_data.get('service_hashes', {})
        cached_inquiry_hashes = cached_data.get('inquiry_hashes', {})
        
        # Track changes
        models_changed = 0
        models_added = 0
        models_removed = 0
        services_changed = 0
        inquiries_changed = 0
        inquiries_added = 0
        inquiries_removed = 0
        cache_hits = 0
        
        # === UPDATE MODELS ===
        
        # Find models to remove (in cache but not in current schema)
        models_to_remove = set(cached_model_hashes.keys()) - set(current_model_hashes.keys())
        for model_name in models_to_remove:
            self._remove_model(model_name)
            models_removed += 1
        
        # Find models to add or update
        models_to_build = []
        for model_name, current_hash in current_model_hashes.items():
            cached_hash = cached_model_hashes.get(model_name)
            
            if cached_hash is None:
                # New model
                models_to_build.append(model_name)
                models_added += 1
            elif cached_hash != current_hash:
                # Changed model
                models_to_build.append(model_name)
                models_changed += 1
            else:
                # Unchanged model - restore from cache
                cached_models = cached_data.get('models', {})
                if model_name in cached_models:
                    model_class = cached_models[model_name]
                    setattr(self.models, model_name, model_class)
                    self._model_classes[model_name] = model_class
                    cache_hits += 1
                else:
                    # Cache missing model data, rebuild
                    models_to_build.append(model_name)
                    models_changed += 1
        
        # Build new/changed models
        if models_to_build:
            self._build_specific_models(current_schema, models_to_build)
        
        # === UPDATE SERVICES ===
        
        # Find services to remove
        services_to_remove = set(cached_service_hashes.keys()) - set(current_service_hashes.keys())
        for service_name in services_to_remove:
            self._remove_service(service_name)
        
        # Find services to rebuild (new, changed, or dependent on changed models)
        services_to_rebuild = set()
        
        for service_name, current_hash in current_service_hashes.items():
            cached_hash = cached_service_hashes.get(service_name)
            
            if cached_hash is None:
                services_to_rebuild.add(service_name)
            elif cached_hash != current_hash:
                services_to_rebuild.add(service_name)
                services_changed += 1
        
        # Also rebuild services that depend on changed models
        changed_models = set(models_to_build)
        if changed_models:
            dependent_services = self._find_services_dependent_on_models(current_schema, changed_models)
            services_to_rebuild.update(dependent_services)
        
        # Build services (excluding inquiries service which is handled separately)
        if services_to_rebuild:
            regular_services = {name for name in services_to_rebuild if name != "Inquiries"}
            if regular_services:
                self._build_specific_services(current_schema, regular_services)
        else:
            # No services need rebuilding, but we still need to ensure they exist
            self._restore_services_from_cache(cached_data, current_schema)
        
        # === UPDATE INQUIRIES ===
        
        if inquiries_xml_path:
            # Find inquiries to remove
            inquiries_to_remove = set(cached_inquiry_hashes.keys()) - set(current_inquiry_hashes.keys())
            
            # Find inquiries to add or update
            inquiries_to_build = []
            inquiries_service_needs_update = False
            
            for inquiry_name, current_hash in current_inquiry_hashes.items():
                cached_hash = cached_inquiry_hashes.get(inquiry_name)
                
                if cached_hash is None:
                    inquiries_to_build.append(inquiry_name)
                    inquiries_added += 1
                    inquiries_service_needs_update = True
                elif cached_hash != current_hash:
                    inquiries_to_build.append(inquiry_name)
                    inquiries_changed += 1
                    inquiries_service_needs_update = True
            
            # If any inquiries changed or we have removals, rebuild the entire inquiries service
            if inquiries_to_remove or inquiries_service_needs_update:
                # Rebuild inquiries service due to changes
                self._build_inquiries_service(inquiries_xml_path)
                inquiries_removed = len(inquiries_to_remove)
            elif "Inquiries" not in self._service_instances:
                # Inquiries service doesn't exist, build it
                self._build_inquiries_service(inquiries_xml_path)
            else:
                # No changes to inquiries, keep existing service
                pass
        
        # Update counters
        self._cache_hits += cache_hits
        total_changes = (models_changed + models_added + services_changed + 
                        inquiries_changed + inquiries_added)
        if total_changes > 0:
            self._cache_misses += 1  # Partial miss
        else:
            self._cache_hits += 1  # Complete hit
        
        # Track differential update stats
        self._last_differential_update = {
            'models': {'added': models_added, 'changed': models_changed, 'removed': models_removed},
            'services': {'changed': services_changed},
            'inquiries': {'added': inquiries_added, 'changed': inquiries_changed, 'removed': inquiries_removed},
            'cache_hits': cache_hits
        }

    def _calculate_inquiry_hashes(self, xml_file_path: str) -> Dict[str, str]:
        """Calculate hash for each inquiry definition in the XML."""
        inquiry_hashes = {}
        
        if not xml_file_path or not Path(xml_file_path).exists():
            return inquiry_hashes
        
        try:
            namespaces = {
                'edmx': 'http://docs.oasis-open.org/odata/ns/edmx', 
                'edm': 'http://docs.oasis-open.org/odata/ns/edm'
            }
            tree = ET.parse(xml_file_path)
            container = tree.find('.//edm:EntityContainer[@Name="Default"]', namespaces)
            
            if container is not None:
                for entity_set in container.findall('edm:EntitySet', namespaces):
                    original_name = entity_set.get('Name')
                    entity_type = entity_set.get('EntityType')
                    
                    if original_name and entity_type:
                        # Get the actual entity type definition for more detailed hashing
                        entity_type_name = entity_type.split('.', 1)[-1]
                        entity_type_elem = tree.find(f'.//edm:EntityType[@Name="{entity_type_name}"]', namespaces)
                        
                        # Create normalized representation for hashing
                        normalized_inquiry = {
                            'name': original_name,
                            'entity_type': entity_type,
                            'properties': []
                        }
                        
                        if entity_type_elem is not None:
                            properties = entity_type_elem.findall('edm:Property', namespaces)
                            for prop in properties:
                                prop_info = {
                                    'name': prop.get('Name'),
                                    'type': prop.get('Type'),
                                    'nullable': prop.get('Nullable', 'true')
                                }
                                normalized_inquiry['properties'].append(prop_info)
                            
                            # Sort properties for consistent hashing
                            normalized_inquiry['properties'].sort(key=lambda x: x['name'])
                        
                        hash_input = json.dumps(normalized_inquiry, sort_keys=True)
                        inquiry_hashes[original_name] = hashlib.md5(hash_input.encode()).hexdigest()

        except Exception as e:
            logger.warning(f"Error calculating inquiry hashes: {e}")
        
        return inquiry_hashes

    def _calculate_inquiries_xml_hash(self, xml_file_path: str) -> str:
        """Calculate overall hash of the inquiries XML file."""
        if not xml_file_path or not Path(xml_file_path).exists():
            return ""
        
        try:
            with open(xml_file_path, 'rb') as f:
                content = f.read()
            return hashlib.md5(content).hexdigest()
        except Exception:
            return ""

    def _extract_inquiry_definitions(self, xml_file_path: str) -> Dict[str, Any]:
        """Extract inquiry definitions for caching metadata."""
        if not xml_file_path or not Path(xml_file_path).exists():
            return {}
        
        inquiry_defs = {}
        
        try:
            namespaces = {
                'edmx': 'http://docs.oasis-open.org/odata/ns/edmx', 
                'edm': 'http://docs.oasis-open.org/odata/ns/edm'
            }
            tree = ET.parse(xml_file_path)
            container = tree.find('.//edm:EntityContainer[@Name="Default"]', namespaces)
            
            if container is not None:
                for entity_set in container.findall('edm:EntitySet', namespaces):
                    original_name = entity_set.get('Name')
                    entity_type = entity_set.get('EntityType')
                    
                    if original_name and entity_type:
                        inquiry_defs[original_name] = {
                            'entity_type': entity_type,
                            'method_name': self._generate_inquiry_method_name(original_name)
                        }

        except Exception as e:
            logger.warning(f"Error extracting inquiry definitions: {e}")
        
        return inquiry_defs

    def _generate_inquiry_method_name(self, inquiry_name: str) -> str:
        """Generate method name from inquiry name."""
        import re
        return re.sub(r"[-\s]+", "_", inquiry_name)

    def _build_inquiries_service(self, xml_file_path: str) -> None:
        """Build the inquiries service from XML file."""
        try:
            # Create the inquiries service if it doesn't exist
            if "Inquiries" not in self._service_instances:
                from .core import BaseService
                service_class = type("InquiriesService", (BaseService,), {
                    "__init__": lambda s, client, entity_name="Inquiries": BaseService.__init__(s, client, entity_name)
                })
                inquiries_service = service_class(self)
                self._service_instances["Inquiries"] = inquiries_service
                self._available_services.add("Inquiries")
                # Mirror the convention used by _build_dynamic_services so
                # callers can do client.inquiries.<method>(...) directly.
                # Without this attr the live code preview in the TUI emits
                # snippets that don't run when copy-pasted.
                setattr(self, "inquiries", inquiries_service)
            else:
                inquiries_service = self._service_instances["Inquiries"]
            
            # Parse XML and add methods
            namespaces = {
                'edmx': 'http://docs.oasis-open.org/odata/ns/edmx', 
                'edm': 'http://docs.oasis-open.org/odata/ns/edm'
            }
            tree = ET.parse(xml_file_path)
            container = tree.find('.//edm:EntityContainer[@Name="Default"]', namespaces)

            if container is not None:
                # Remove existing inquiry methods
                self._clear_inquiry_methods(inquiries_service)
                
                # Add new inquiry methods
                for entity_set in container.findall('edm:EntitySet', namespaces):
                    original_name = entity_set.get('Name')
                    entity_type = entity_set.get('EntityType')
                    if not original_name:
                        continue
                    
                    method_name = self._generate_inquiry_method_name(original_name)
                    self._add_inquiry_method_to_service(
                        inquiries_service, original_name, method_name, 
                        entity_type, xml_file_path
                    )

        except Exception as e:
            logger.warning(f"Could not build inquiries service: {e}")

    def _clear_inquiry_methods(self, service) -> None:
        """Remove existing inquiry methods from service."""
        # Get list of methods that look like inquiry methods
        methods_to_remove = []
        for attr_name in dir(service):
            if not attr_name.startswith('_') and callable(getattr(service, attr_name)):
                if attr_name not in _BASE_SERVICE_METHODS:
                    methods_to_remove.append(attr_name)
        
        # Remove the methods
        for method_name in methods_to_remove:
            try:
                delattr(service, method_name)
            except AttributeError:
                pass

    def _add_inquiry_method_to_service(self, service, inquiry_name: str, method_name: str, 
                                     entity_type: str, xml_file_path: str) -> None:
        """Add a single inquiry method to the service."""
        from functools import update_wrapper
        from .odata import QueryOptions
        
        # Create the method
        def create_inquiry_method(name_of_inquiry: str):
            def api_method(self, options: QueryOptions = None):
                return self._get_inquiry(name_of_inquiry, options=options)
            return api_method

        # Generate docstring
        docstring = self._generate_inquiry_docstring(xml_file_path, entity_type, inquiry_name)
        
        # Create and attach the method
        inquiry_method = create_inquiry_method(inquiry_name)
        inquiry_method.__doc__ = docstring
        inquiry_method.__name__ = method_name
        
        setattr(service, method_name, inquiry_method.__get__(service, service.__class__))

    def _generate_inquiry_docstring(self, xml_file_path: str, entity_type: str, inquiry_name: str) -> str:
        """Generate docstring for inquiry method."""
        try:
            namespaces = {'edm': 'http://docs.oasis-open.org/odata/ns/edm'}
            tree = ET.parse(xml_file_path)
            
            # Get the entity type name without namespace
            entity_type_name = entity_type.split('.', 1)[-1]
            entity_type_elem = tree.find(f'.//edm:EntityType[@Name="{entity_type_name}"]', namespaces)

            if entity_type_elem is None:
                return f"""Generic Inquiry for the '{inquiry_name}' endpoint

        Args:
            options (QueryOptions, optional): OData query options like $filter, $top, etc.

        Returns:
            A dictionary containing the API response with inquiry data.
        """

            # Extract properties
            properties = [prop.attrib for prop in entity_type_elem.findall('edm:Property', namespaces)]

            if properties:
                fields_str = "\n".join([
                    f"        - {prop.get('Name')} ({prop.get('Type', '').split('.', 1)[-1]})"
                    for prop in properties
                ])
            else:
                fields_str = "        (No properties found for this EntityType)"

            return f"""Generic Inquiry for the '{inquiry_name}' endpoint

        Args:
            options (QueryOptions, optional): OData query options like $filter, $top, etc.

        Returns:
            A dictionary containing the API response, typically a list of records with the following fields:
{fields_str}
        """

        except Exception as e:
            return f"""Generic Inquiry for the '{inquiry_name}' endpoint

        Args:
            options (QueryOptions, optional): OData query options like $filter, $top, etc.

        Returns:
            A dictionary containing the API response with inquiry data.
            
        Note: Error generating field documentation: {e}
        """

    def _fetch_gi_xml(self) -> str:
        """Fetch Generic Inquiries XML and return the file path."""
        metadata_url = f"{self.base_url}/t/{self.tenant}/api/odata/gi/$metadata"

        try:
            response = requests.get(
                url=metadata_url,
                auth=(self.username, self._password)
            )
            response.raise_for_status()

            # Save to metadata directory
            package_dir = os.path.dirname(os.path.abspath(__file__))
            metadata_dir = os.path.join(package_dir, ".metadata")
            if self._cache_dir_overridden:
                metadata_dir = os.path.join(str(self.cache_dir), ".metadata")
            os.makedirs(metadata_dir, exist_ok=True)

            output_path = os.path.join(metadata_dir, "odata_inquiries_schema.xml")
            with open(output_path, 'wb') as f:
                f.write(response.content)

            # Inquiries schema saved successfully
            return output_path

        except Exception as e:
            logger.debug(f"Error fetching Generic Inquiries metadata: {e}")
            raise

    # ... [Rest of the existing methods from the previous artifact] ...

    def _calculate_model_hashes(self, schema: Dict[str, Any]) -> Dict[str, str]:
        """Calculate hash for each model definition in the schema."""
        model_hashes = {}
        schemas = schema.get("components", {}).get("schemas", {})
        
        primitive_wrappers = {
            "StringValue", "DecimalValue", "BooleanValue", "DateTimeValue",
            "GuidValue", "IntValue", "ShortValue", "LongValue", "ByteValue",
            "DoubleValue"
        }
        
        for name, definition in schemas.items():
            if name not in primitive_wrappers:
                # Create a normalized representation for hashing
                normalized_def = self._normalize_model_definition(definition)
                hash_input = json.dumps(normalized_def, sort_keys=True)
                model_hashes[name] = hashlib.md5(hash_input.encode()).hexdigest()
        
        return model_hashes

    def _calculate_service_hashes(self, schema: Dict[str, Any]) -> Dict[str, str]:
        """Calculate hash for each service definition in the schema."""
        service_hashes = {}
        paths = schema.get("paths", {})
        
        # Group operations by tag (service)
        services_ops = {}
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if tag not in services_ops:
                        services_ops[tag] = []
                    services_ops[tag].append((path, http_method, details))
        
        for service_name, operations in services_ops.items():
            # Create normalized representation of all operations for this service
            normalized_ops = []
            for path, method, details in operations:
                normalized_op = {
                    'path': path,
                    'method': method,
                    'operationId': details.get('operationId'),
                    'parameters': details.get('parameters', []),
                    'requestBody': self._normalize_request_body(details.get('requestBody')),
                    'responses': self._normalize_responses(details.get('responses', {}))
                }
                normalized_ops.append(normalized_op)
            
            # Sort for consistent hashing
            normalized_ops.sort(key=lambda x: (x['path'], x['method']))
            hash_input = json.dumps(normalized_ops, sort_keys=True)
            service_hashes[service_name] = hashlib.md5(hash_input.encode()).hexdigest()
        
        return service_hashes

    def _calculate_schema_hash(self, schema: Dict[str, Any]) -> str:
        """
        Calculate an overall schema hash for quick comparison.

        Hashes the full schema JSON (sorted keys) so any content change
        produces a different digest. The earlier counts-only implementation
        collided on schemas that had the same number of paths/schemas but
        different content, which silently hid server-side changes.
        """
        hash_input = json.dumps(schema, sort_keys=True, default=str)
        return hashlib.md5(hash_input.encode()).hexdigest()

    def _normalize_model_definition(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a model definition for consistent hashing."""
        normalized = {}
        
        for key in ['type', 'required', 'properties', 'allOf', 'description']:
            if key in definition:
                if key == 'properties':
                    normalized[key] = {
                        prop_name: self._normalize_property_definition(prop_def)
                        for prop_name, prop_def in definition[key].items()
                    }
                else:
                    normalized[key] = definition[key]
        
        return normalized

    def _normalize_property_definition(self, prop_def: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize a property definition for consistent hashing."""
        normalized = {}
        
        for key in ['type', 'format', '$ref', 'items', 'description']:
            if key in prop_def:
                normalized[key] = prop_def[key]
        
        return normalized

    def _normalize_request_body(self, request_body: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize request body definition for hashing."""
        if not request_body:
            return {}
        
        normalized = {}
        if 'content' in request_body:
            content = request_body['content']
            if 'application/json' in content:
                schema = content['application/json'].get('schema', {})
                if '$ref' in schema:
                    normalized['schema_ref'] = schema['$ref']
        
        return normalized

    def _normalize_responses(self, responses: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize responses definition for hashing."""
        normalized = {}
        
        for status_code, response_def in responses.items():
            if isinstance(response_def, dict):
                norm_response = {}
                if 'content' in response_def:
                    content = response_def['content']
                    if 'application/json' in content:
                        schema = content['application/json'].get('schema', {})
                        if '$ref' in schema:
                            norm_response['schema_ref'] = schema['$ref']
                        elif schema.get('type') == 'array' and 'items' in schema:
                            if '$ref' in schema['items']:
                                norm_response['array_items_ref'] = schema['items']['$ref']
                normalized[status_code] = norm_response
        
        return normalized

    def _build_specific_models(self, schema: Dict[str, Any], model_names: List[str]) -> None:
        """Build only specific models from the schema."""
        # Build specific models from the schema
        
        factory = ModelFactory(schema)
        
        for model_name in model_names:
            try:
                model_class = factory._get_or_build_model(model_name)
                setattr(self.models, model_name, model_class)
                self._model_classes[model_name] = model_class
            except Exception as e:
                logger.warning(f"Failed to build model {model_name}: {e}")

    def _build_specific_services(self, schema: Dict[str, Any], service_names: Set[str]) -> None:
        """Build only specific services from the schema."""
        # Build specific services from the schema
        
        factory = ServiceFactory(self, schema)
        all_services = factory.build_services()
        
        for service_name in service_names:
            if service_name in all_services:
                service_instance = all_services[service_name]
                # Check if this is a custom endpoint with custom naming
                if hasattr(service_instance, '_custom_endpoint_metadata') and service_instance._custom_endpoint_metadata:
                    metadata = service_instance._custom_endpoint_metadata
                    if metadata['custom_name']:
                        attr_name = metadata['custom_name']
                    else:
                        # Fallback to default pluralization
                        attr_name = to_snake_case(service_name)
                else:
                    # Use centralized pluralization logic
                    attr_name = to_snake_case(service_name)
                setattr(self, attr_name, service_instance)
                self._available_services.add(service_name)
                self._service_instances[service_name] = service_instance
                pass  # Service built successfully

    def _restore_services_from_cache(self, cached_data: Dict[str, Any], current_schema: Dict[str, Any]) -> None:
        """Restore services when they haven't changed."""
        # Services need to be rebuilt as they contain runtime dependencies
        self._build_dynamic_services(current_schema)

    def _find_services_dependent_on_models(self, schema: Dict[str, Any], changed_models: Set[str]) -> Set[str]:
        """Find services that depend on changed models."""
        dependent_services = set()
        
        paths = schema.get("paths", {})
        for path, path_info in paths.items():
            for http_method, details in path_info.items():
                tag = details.get("tags", [None])[0]
                if tag:
                    if self._operation_references_models(details, changed_models):
                        dependent_services.add(tag)
        
        return dependent_services

    def _operation_references_models(self, operation_details: Dict[str, Any], model_names: Set[str]) -> bool:
        """Check if an operation references any of the specified models."""
        request_body = operation_details.get('requestBody', {})
        if self._references_models_in_schema(request_body, model_names):
            return True
        
        responses = operation_details.get('responses', {})
        for response in responses.values():
            if isinstance(response, dict) and self._references_models_in_schema(response, model_names):
                return True
        
        return False

    def _references_models_in_schema(self, schema_part: Dict[str, Any], model_names: Set[str]) -> bool:
        """Recursively check if a schema part references any of the specified models."""
        if not isinstance(schema_part, dict):
            return False
        
        if '$ref' in schema_part:
            ref_name = schema_part['$ref'].split('/')[-1]
            if ref_name in model_names:
                return True
        
        for value in schema_part.values():
            if isinstance(value, dict):
                if self._references_models_in_schema(value, model_names):
                    return True
            elif isinstance(value, list):
                for item in value:
                    if isinstance(item, dict) and self._references_models_in_schema(item, model_names):
                        return True
        
        return False

    def _extract_service_definitions(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Extract service definitions for caching."""
        return {}

    def _remove_model(self, model_name: str) -> None:
        """Remove a model from the client."""
        if hasattr(self.models, model_name):
            delattr(self.models, model_name)
        self._model_classes.pop(model_name, None)

    def _remove_service(self, service_name: str) -> None:
        """Remove a service from the client."""
        # Find the actual attribute name by checking if it's a custom endpoint
        service_instance = self._service_instances.get(service_name)
        if service_instance and hasattr(service_instance, '_custom_endpoint_metadata') and service_instance._custom_endpoint_metadata:
            metadata = service_instance._custom_endpoint_metadata
            if metadata['custom_name']:
                attr_name = metadata['custom_name']
            else:
                attr_name = to_snake_case(service_name)
        else:
            # Use centralized pluralization logic
            attr_name = to_snake_case(service_name)

        if hasattr(self, attr_name):
            delattr(self, attr_name)
        self._available_services.discard(service_name)
        self._service_instances.pop(service_name, None)

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        stats = self.get_performance_stats()
        
        if self.cache_enabled:
            cache_file = self.cache_dir / f"{self._get_cache_key()}.pkl"
            cache_exists = cache_file.exists()
            cache_size = cache_file.stat().st_size if cache_exists else 0
            
            stats.update({
                'cache_file_exists': cache_exists,
                'cache_file_size_bytes': cache_size,
                'cache_file_path': str(cache_file),
                'differential_caching': True
            })
        
        return stats

    def _get_cache_key(self) -> str:
        """Generate a unique cache key based on connection parameters."""
        key_parts = [
            self.base_url,
            self.tenant,
            self.endpoint_name,
            self.endpoint_version or 'latest'
        ]
        key_string = '|'.join(key_parts)
        return hashlib.md5(key_string.encode()).hexdigest()

    def _fetch_schema(self, endpoint_name: str = "Default", version: str = None) -> Dict[str, Any]:
        """
        Fetches and caches the OpenAPI schema for a given endpoint.

        Lookup order: in-memory dict -> on-disk gzip JSON -> network fetch.
        The on-disk layer saves ~3 MB of bandwidth per startup when fresh.

        ``self._schema_cache`` already provides in-memory caching, so we
        don't decorate with ``@lru_cache`` (which would also pin ``self``
        in a class-level cache).

        Args:
            endpoint_name: Name of the API endpoint
            version: Version of the endpoint

        Returns:
            OpenAPI schema dictionary

        Raises:
            AcumaticaError: If schema fetch fails
        """
        if not version:
            version = self.endpoints[endpoint_name]['version']
        cache_key = f"{endpoint_name}:{version}"
        if cache_key in self._schema_cache:
            return self._schema_cache[cache_key]

        schema = self._load_schema_from_disk()
        if schema is not None:
            self._schema_cache[cache_key] = schema
            return schema

        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json"
        if self.tenant:
            schema_url += f"?company={self.tenant}"

        try:
            schema = self._request("get", schema_url).json()
            self._schema_cache[cache_key] = schema
            self._save_schema_to_disk(schema)
            return schema
        except Exception as e:
            raise AcumaticaError(f"Failed to fetch schema for {endpoint_name} v{version}: {e}")

    def _schema_cache_path(self) -> Path:
        """Path to the on-disk gzipped schema JSON for this client's connection."""
        return self.cache_dir / f"{self._get_cache_key()}.schema.json.gz"

    def _load_schema_from_disk(self) -> Optional[Dict[str, Any]]:
        """
        Load the raw OpenAPI schema from the on-disk cache if it's present and fresh.

        Returns None on cache miss, expired TTL, corrupt file, or when disk caching
        is disabled (cache_enabled=False or force_rebuild=True).
        """
        if not self.cache_enabled or self.force_rebuild:
            return None

        schema_file = self._schema_cache_path()
        if not schema_file.exists():
            return None

        with self._cache_lock:
            try:
                age = time.time() - schema_file.stat().st_mtime
            except OSError:
                return None
            if age >= self.schema_cache_ttl_hours * 3600:
                return None

            try:
                with gzip.open(schema_file, 'rt', encoding='utf-8') as f:
                    return json.load(f)
            except (OSError, json.JSONDecodeError, EOFError, gzip.BadGzipFile):
                # Corrupt or unreadable; caller will refetch from network.
                return None

    def _save_schema_to_disk(self, schema: Dict[str, Any]) -> None:
        """
        Persist the raw OpenAPI schema to disk as gzipped JSON.

        Uses atomic write (temp file + os.replace) mirroring the pickle path.
        Silently skips on read-only filesystems so Lambda/container environments
        degrade to "fetch every time" rather than raising.
        """
        if not self.cache_enabled:
            return

        schema_file = self._schema_cache_path()
        temp_file = schema_file.with_suffix(
            f'{schema_file.suffix}.tmp.{os.getpid()}.{threading.get_ident()}'
        )
        with self._cache_lock:
            try:
                schema_file.parent.mkdir(parents=True, exist_ok=True)
                with gzip.open(temp_file, 'wt', encoding='utf-8') as f:
                    json.dump(schema, f)
                os.replace(temp_file, schema_file)
            except OSError:
                try:
                    if temp_file.exists():
                        temp_file.unlink()
                except OSError:
                    pass

    def _build_dynamic_models(self, schema: Dict[str, Any]) -> None:
        """Populates the 'models' module with dynamically generated dataclasses."""
        # Building dynamic models from schema
        
        try:
            factory = ModelFactory(schema)
            model_dict = factory.build_models()
            
            # Attach each generated class to the models module and store reference
            for name, model_class in model_dict.items():
                # Only set __module__ if it's actually a class, not a dict
                if hasattr(model_class, '__module__'):
                    model_class.__module__ = 'easy_acumatica.models'
                setattr(self.models, name, model_class)
                self._model_classes[name] = model_class
                pass  # Model created successfully
                
            # Successfully built models
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic models: {e}")

    def _build_dynamic_services(self, schema: Dict[str, Any]) -> None:
        """Attaches dynamically created services to the client instance."""
        # Building dynamic services from schema
        
        try:
            factory = ServiceFactory(self, schema)
            services_dict = factory.build_services()
            
            for name, service_instance in services_dict.items():
                # Check if this is a custom endpoint with custom naming
                if hasattr(service_instance, '_custom_endpoint_metadata') and service_instance._custom_endpoint_metadata:
                    metadata = service_instance._custom_endpoint_metadata
                    if metadata['custom_name']:
                        attr_name = metadata['custom_name']
                    else:
                        # Fallback to default pluralization
                        attr_name = to_snake_case(name)
                else:
                    # Use centralized pluralization logic
                    attr_name = to_snake_case(name)

                # Add batch support to all service methods
                self._add_batch_support_to_service(service_instance)
                
                setattr(self, attr_name, service_instance)
                self._available_services.add(name)
                self._service_instances[name] = service_instance
                pass  # Service created successfully
                
            # Successfully built services
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic services: {e}")

    # --- Custom field discovery ($adHocSchema) ---------------------------
    #
    # The OpenAPI schema does not surface custom (Usr*/Attribute*) fields,
    # so after building the base models we ask each entity for its
    # $adHocSchema and walk the response. The walker yields tuples of
    # (target_model_name, view, field, custom_type) which we apply to the
    # model registry. After augmentation, parent classes' nested
    # annotations are re-linked to the swapped-in child classes.

    def _ad_hoc_schema_url(self, entity_tag: str) -> str:
        """URL of the per-entity $adHocSchema endpoint."""
        version = self.endpoints.get(self.endpoint_name, {}).get('version', self.endpoint_version)
        return (
            f"{self.base_url}/entity/{self.endpoint_name}/{version}/"
            f"{entity_tag}/$adHocSchema"
        )

    def _fetch_one_ad_hoc_schema(self, entity_tag: str) -> Optional[Dict[str, Any]]:
        """Fetch and JSON-decode one entity's $adHocSchema. Returns None
        on per-entity failure (404/403/decode error) so a single bad
        endpoint doesn't poison the whole discovery sweep."""
        try:
            resp = self._request("get", self._ad_hoc_schema_url(entity_tag))
            if not resp.ok:
                logger.debug(
                    f"$adHocSchema for {entity_tag} returned {resp.status_code}"
                )
                return None
            return resp.json()
        except Exception as e:
            logger.debug(f"$adHocSchema fetch failed for {entity_tag}: {e}")
            return None

    def _discover_custom_fields(
        self,
        max_workers: int = 5,
        cached_schemas: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> None:
        """Augment every dynamic model with its discovered custom fields.

        Iterates every service the OpenAPI schema produced, fetches
        ``$adHocSchema`` in parallel (bounded by ``max_workers``), walks
        each response with :func:`walk_custom_fields`, and applies the
        resulting augmentations to ``self._model_classes``. Re-links
        nested annotations and updates ``self.models`` so callers see the
        augmented classes everywhere.

        When ``cached_schemas`` is provided (tag -> $adHocSchema response),
        the network sweep is skipped entirely - we walk the cached
        responses and augment from them. The differential cache passes
        this in whenever the OpenAPI schema hash hasn't changed, which
        avoids re-fetching N schemas on every connect.

        Per-entity failures are logged and skipped - a tenant with an
        endpoint that 500s on $adHocSchema still gets the rest of its
        models augmented.
        """
        from .model_factory import (
            apply_custom_field_discoveries,
            re_link_dataclass_annotations,
            walk_custom_fields,
        )

        if not self._service_instances:
            return

        # Map service-tag -> dataclass name. In real Acumatica the tag
        # and the schema name match (``SalesOrder`` <-> ``SalesOrder``)
        # but in mocks and some custom endpoints they can differ
        # (``Test`` -> ``TestModel``). Try a few common variations and
        # skip services we can't resolve.
        targets: Dict[str, str] = {}  # tag -> dataclass_name
        for tag, svc in self._service_instances.items():
            if tag == "Inquiries":
                continue
            entity_name = getattr(svc, "entity_name", None)
            if not entity_name:
                continue
            for candidate in (entity_name, f"{entity_name}Model", entity_name.rstrip("s")):
                if candidate in self._model_classes:
                    targets[tag] = candidate
                    break

        if not targets:
            return

        # Parallel fetch via the existing batch infrastructure. Each
        # worker shares the client's auth state through the same
        # thread-local override BatchCall already uses.
        from .batch import BatchCall, CallableWrapper

        tags = list(targets.keys())

        if cached_schemas is not None:
            # Cache hit: no network round-trip. Use only the entries
            # whose tag is still in the current target set so dropped
            # services don't sneak in.
            self._ad_hoc_schemas = {t: s for t, s in cached_schemas.items() if t in targets}
            schemas_by_tag = self._ad_hoc_schemas
            logger.debug(
                f"Custom-field discovery: using cached $adHocSchema for "
                f"{len(schemas_by_tag)} entity tag(s)"
            )
        else:
            calls = [
                CallableWrapper(self._fetch_one_ad_hoc_schema, tag)
                for tag in tags
            ]
            if not calls:
                return

            logger.info(
                f"Discovering custom fields across {len(calls)} entity schemas"
                f" (max_workers={max_workers})..."
            )
            results = BatchCall(
                *calls,
                max_concurrent=max_workers,
                return_exceptions=True,
            ).execute()
            schemas_by_tag = {
                tag: ad_hoc
                for tag, ad_hoc in zip(tags, results)
                if isinstance(ad_hoc, dict)
            }
            # Cache for the next save_differential_cache call.
            self._ad_hoc_schemas = schemas_by_tag

        # Walk every response, accumulate discoveries against the
        # resolved dataclass name for each tag.
        all_discoveries: List[Tuple[str, str, str, str]] = []
        for tag, ad_hoc in schemas_by_tag.items():
            dataclass_name = targets.get(tag)
            if not dataclass_name:
                continue
            all_discoveries.extend(
                walk_custom_fields(ad_hoc, self._model_classes, dataclass_name)
            )

        if not all_discoveries:
            logger.info("Custom-field discovery: no fields found.")
            return

        apply_custom_field_discoveries(self._model_classes, all_discoveries)
        re_link_dataclass_annotations(self._model_classes)

        # Mirror the augmented classes back onto client.models so users
        # who reference client.models.SalesOrder see the augmented copy.
        for model_name, cls in self._model_classes.items():
            setattr(self.models, model_name, cls)

        logger.info(
            f"Custom-field discovery: applied {len(all_discoveries)} field(s)"
            f" across {len({d[0] for d in all_discoveries})} model(s)."
        )

    def _add_batch_support_to_service(self, service_instance) -> None:
        """
        Add batch calling support to all public methods of a service instance.
        
        Args:
            service_instance: The service instance to enhance with batch support
        """
        # Get all method names that should have batch support
        method_names = [name for name in dir(service_instance) 
                    if not name.startswith('_') and 
                    callable(getattr(service_instance, name, None)) and
                    name not in ['entity_name', 'endpoint_name']]  # Skip attributes
        
        # Wrap each method with batch support
        for method_name in method_names:
            original_method = getattr(service_instance, method_name)
            if callable(original_method):
                wrapper = BatchMethodWrapper(original_method, service_instance)
                setattr(service_instance, method_name, wrapper)
        
        # Added batch support to service methods
    # --- Utility Methods ---

    def list_models(self) -> List[str]:
        """
        Get a list of all available data model names.
        
        Returns:
            List of model class names
            
        Example:
            >>> client = AcumaticaClient()
            >>> models = client.list_models()
            >>> print(f"Available models: {', '.join(models)}")
        """
        return sorted([name for name in self._model_classes.keys()])

    def list_services(self) -> List[str]:
        """
        Get a list of all available service names.
        
        Returns:
            List of service names (in PascalCase)
            
        Example:
            >>> client = AcumaticaClient()
            >>> services = client.list_services()
            >>> print(f"Available services: {', '.join(services)}")
        """
        return sorted(list(self._available_services))

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific model.
        
        Args:
            model_name: Name of the model class
            
        Returns:
            Dictionary with model information
            
        Raises:
            ValueError: If model doesn't exist
            
        Example:
            >>> info = client.get_model_info('Contact')
            >>> print(f"Fields: {info['fields']}")
        """
        if model_name not in self._model_classes:
            available = ', '.join(self.list_models())
            raise ValueError(f"Model '{model_name}' not found. Available models: {available}")
        
        model_class = self._model_classes[model_name]
        
        # Get field information
        fields = {}
        if hasattr(model_class, '__annotations__'):
            for field_name, field_type in model_class.__annotations__.items():
                fields[field_name] = {
                    'type': str(field_type),
                    'required': not str(field_type).startswith('typing.Optional')
                }
        
        return {
            'name': model_name,
            'class': model_class.__name__,
            'docstring': model_class.__doc__,
            'fields': fields,
            'field_count': len(fields),
            'base_classes': [base.__name__ for base in model_class.__bases__]
        }

    def get_service_info(self, service_name: str) -> Dict[str, Any]:
        """
        Get detailed information about a specific service.
        
        Args:
            service_name: Name of the service (PascalCase)
            
        Returns:
            Dictionary with service information
            
        Raises:
            ValueError: If service doesn't exist
            
        Example:
            >>> info = client.get_service_info('Contact')
            >>> print(f"Methods: {info['methods']}")
        """
        if service_name not in self._service_instances:
            available = ', '.join(self.list_services())
            raise ValueError(f"Service '{service_name}' not found. Available services: {available}")
        
        service = self._service_instances[service_name]
        
        # Get method information
        methods = []
        for attr_name in dir(service):
            if not attr_name.startswith('_') and callable(getattr(service, attr_name)):
                method = getattr(service, attr_name)
                methods.append({
                    'name': attr_name,
                    'docstring': method.__doc__,
                    'signature': str(getattr(method, '__annotations__', {}))
                })
        
        # Determine client attribute name (same logic as in _build_dynamic_services)
        if hasattr(service, '_custom_endpoint_metadata') and service._custom_endpoint_metadata:
            metadata = service._custom_endpoint_metadata
            if metadata['custom_name']:
                client_attribute = metadata['custom_name']
            else:
                client_attribute = to_snake_case(service_name)
        else:
            # Use centralized pluralization logic
            client_attribute = to_snake_case(service_name)

        return {
            'name': service_name,
            'entity_name': service.entity_name,
            'endpoint_name': getattr(service, 'endpoint_name', 'Default'),
            'methods': methods,
            'method_count': len(methods),
            'client_attribute': client_attribute
        }

    def list_inquiries(self) -> List[str]:
        """Return sorted method names of every Generic Inquiry attached to
        the ``Inquiries`` service.

        Returns an empty list when no Generic Inquiry metadata has been
        loaded for this client (the ``Inquiries`` service is only built
        when GI XML is fetched successfully).
        """
        service = self._service_instances.get("Inquiries")
        if service is None:
            return []
        return sorted(
            attr for attr in dir(service)
            if not attr.startswith('_')
            and attr not in _BASE_SERVICE_METHODS
            and callable(getattr(service, attr, None))
        )

    def get_inquiry_info(self, method_name: str) -> Dict[str, Any]:
        """Return introspection details for a single Generic Inquiry method.

        Raises:
            ValueError: If the inquiry method does not exist on the
                ``Inquiries`` service (or no ``Inquiries`` service exists).
        """
        service = self._service_instances.get("Inquiries")
        if service is None:
            raise ValueError(
                "No Inquiries service is registered on this client."
            )
        method = getattr(service, method_name, None)
        if method is None or not callable(method) or method_name in _BASE_SERVICE_METHODS:
            available = ', '.join(self.list_inquiries())
            raise ValueError(
                f"Inquiry '{method_name}' not found. Available inquiries: {available}"
            )
        return {
            'name': method_name,
            'method_name': getattr(method, '__name__', method_name),
            'doc': method.__doc__,
        }

    def search_models(self, pattern: str) -> List[str]:
        """
        Search for models by name pattern.

        Args:
            pattern: Search pattern (case-insensitive)

        Returns:
            List of matching model names
            
        Example:
            >>> matches = client.search_models('contact')
            >>> print(f"Contact-related models: {matches}")
        """
        pattern = pattern.lower()
        return [name for name in self.list_models() if pattern in name.lower()]

    def search_services(self, pattern: str) -> List[str]:
        """
        Search for services by name pattern.
        
        Args:
            pattern: Search pattern (case-insensitive)
            
        Returns:
            List of matching service names
            
        Example:
            >>> matches = client.search_services('invoice')
            >>> print(f"Invoice-related services: {matches}")
        """
        pattern = pattern.lower()
        return [name for name in self.list_services() if pattern in name.lower()]

    def get_performance_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics for the client.
        
        Returns:
            Dictionary with performance metrics
            
        Example:
            >>> stats = client.get_performance_stats()
            >>> print(f"Startup time: {stats['startup_time']:.2f}s")
        """
        return {
            'startup_time': self._startup_time,
            'cache_enabled': self.cache_enabled,
            'cache_hits': self._cache_hits,
            'cache_misses': self._cache_misses,
            'cache_hit_rate': self._cache_hits / max(1, self._cache_hits + self._cache_misses),
            'model_count': len(self._model_classes),
            'service_count': len(self._service_instances),
            'endpoint_count': len(self.endpoints),
            'schema_cache_size': len(self._schema_cache)
        }

    def get_connection_stats(self) -> Dict[str, Any]:
        """
        Get detailed connection and session pool statistics.

        Returns:
            Dictionary with connection pool metrics

        Example:
            >>> stats = client.get_connection_stats()
            >>> print(f"Active connections: {stats['active_connections']}")
        """
        pool_stats = {}

        # Get connection pool stats from the HTTPAdapter
        for prefix in ['http://', 'https://']:
            adapter = self.session.get_adapter(prefix)
            if hasattr(adapter, 'poolmanager') and adapter.poolmanager:
                pools = adapter.poolmanager.pools
                pool_stats[prefix] = {
                    'num_pools': len(pools),
                    # Correctly access the private attributes
                    'pool_connections': adapter._pool_connections if hasattr(adapter, '_pool_connections') else None,
                    'pool_maxsize': adapter._pool_maxsize if hasattr(adapter, '_pool_maxsize') else None,
                    'max_retries': 0  # HTTP retries disabled - no auto-retry
                }

        return {
            'session_headers': dict(self.session.headers),
            'verify_ssl': self.session.verify,
            'timeout': self.timeout,
            'connection_pools': pool_stats,
            'rate_limit': {
                'calls_per_second': self._rate_limiter.calls_per_second,
                'burst_size': self._rate_limiter.burst_size,
                'current_tokens': self._rate_limiter._tokens
            }
        }

    def get_session_info(self) -> Dict[str, Any]:
        """
        Get current session information and authentication status.

        Returns:
            Dictionary with session details

        Example:
            >>> info = client.get_session_info()
            >>> print(f"Logged in: {info['logged_in']}")
        """
        return {
            'base_url': self.base_url,
            'tenant': self.tenant,
            'username': self.username,
            'endpoint': f"{self.endpoint_name} v{self.endpoint_version}",
            'logged_in': self._logged_in,
            'persistent_login': self.persistent_login,
            'retry_on_idle_logout': self.retry_on_idle_logout,
            'session_age': time.time() - self._startup_time if self._startup_time else None,
            'initialization_stats': getattr(self, '_init_stats', {}),
            'last_differential_update': getattr(self, '_last_differential_update', None)
        }

    def get_api_usage_stats(self) -> Dict[str, Any]:
        """
        Get API usage statistics (requires request history to be enabled).

        Returns:
            Dictionary with API usage metrics

        Example:
            >>> stats = client.get_api_usage_stats()
            >>> print(f"Total requests: {stats['total_requests']}")
        """
        # This will be populated when request history is implemented
        return {
            'total_requests': getattr(self, '_total_requests', 0),
            'total_errors': getattr(self, '_total_errors', 0),
            'requests_by_method': getattr(self, '_requests_by_method', {}),
            'requests_by_endpoint': getattr(self, '_requests_by_endpoint', {}),
            'average_response_time': getattr(self, '_avg_response_time', 0),
            'last_request_time': getattr(self, '_last_request_time', None)
        }

    def get_schema_info(self) -> Dict[str, Any]:
        """
        Get information about the loaded schema and models.

        Returns:
            Dictionary with schema details

        Example:
            >>> info = client.get_schema_info()
            >>> print(f"Schema version: {info['endpoint_version']}")
        """
        schema_size = 0
        if hasattr(self, '_schema_cache'):
            # Estimate size of cached schemas
            import sys
            for key, schema in self._schema_cache.items():
                schema_size += sys.getsizeof(schema)

        return {
            'endpoint_name': self.endpoint_name,
            'endpoint_version': self.endpoint_version,
            'available_endpoints': list(self.endpoints.keys()),
            'total_models': len(self._model_classes),
            'total_services': len(self._service_instances),
            'custom_fields_count': self._count_custom_fields(),
            'schema_cache_size_bytes': schema_size,
            'cache_directory': str(self.cache_dir) if self.cache_enabled else None,
            'cache_ttl_hours': self.cache_ttl_hours
        }

    def _count_custom_fields(self) -> int:
        """Count total custom fields across all models."""
        count = 0
        for model_name, model_class in self._model_classes.items():
            if hasattr(model_class, '__annotations__'):
                for field_name in model_class.__annotations__.keys():
                    if field_name.startswith('Custom') or field_name.startswith('Usr'):
                        count += 1
        return count

    def get_last_request_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the last API request made.

        Returns:
            Dictionary with last request details or None

        Example:
            >>> info = client.get_last_request_info()
            >>> if info:
            ...     print(f"Last request: {info['method']} {info['url']}")
        """
        return getattr(self, '_last_request_info', None)

    def test_connection(self) -> Dict[str, Any]:
        """
        Test connection to Acumatica server without authentication.

        Returns:
            Dictionary with connection test results

        Example:
            >>> result = client.test_connection()
            >>> print(f"Server reachable: {result['reachable']}")
        """
        result = {
            'reachable': False,
            'response_time': None,
            'endpoints_available': False,
            'error': None
        }

        try:
            start_time = time.time()
            response = self.session.get(f"{self.base_url}/entity", timeout=5)
            result['response_time'] = time.time() - start_time

            if response.status_code == 200:
                result['reachable'] = True
                data = response.json()
                if 'endpoints' in data:
                    result['endpoints_available'] = True
                    result['endpoint_count'] = len(data['endpoints'])
        except Exception as e:
            result['error'] = str(e)

        return result

    def validate_credentials(self) -> Dict[str, bool]:
        """
        Test if current credentials are valid without affecting session.

        Returns:
            Dictionary with validation results

        Example:
            >>> result = client.validate_credentials()
            >>> print(f"Credentials valid: {result['valid']}")
        """
        # Save current login state
        was_logged_in = self._logged_in

        result = {'valid': False, 'error': None}

        try:
            # Try to login with current credentials
            if was_logged_in:
                self.logout()

            self.login()
            result['valid'] = True

            # Restore original state
            if not was_logged_in:
                self.logout()

        except Exception as e:
            result['error'] = str(e)
            self._logged_in = was_logged_in

        return result

    def enable_request_history(self, max_items: int = 100) -> None:
        """
        Enable request/response history tracking.

        Args:
            max_items: Maximum number of requests to track

        Example:
            >>> client.enable_request_history(50)
            >>> # Make requests...
            >>> history = client.get_request_history()
        """
        self._request_history_enabled = True
        self._request_history_max = max_items
        if not hasattr(self, '_request_history'):
            self._request_history = []

    def get_request_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get request history (if enabled).

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of request/response details

        Example:
            >>> history = client.get_request_history(10)
            >>> for req in history:
            ...     print(f"{req['method']} {req['endpoint']}: {req['status_code']}")
        """
        if not hasattr(self, '_request_history'):
            return []

        history = self._request_history
        if limit:
            history = history[:limit]

        return history

    def clear_request_history(self) -> None:
        """Clear request history."""
        if hasattr(self, '_request_history'):
            self._request_history.clear()

    def get_error_history(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get recent error history (requires error tracking to be enabled).

        Args:
            limit: Maximum number of errors to return

        Returns:
            List of error details

        Example:
            >>> errors = client.get_error_history(5)
            >>> for error in errors:
            ...     print(f"{error['timestamp']}: {error['message']}")
        """
        return getattr(self, '_error_history', [])[:limit]

    def get_health_status(self) -> Dict[str, Any]:
        """
        Get overall health status of the client and connection.

        Returns:
            Dictionary with health metrics

        Example:
            >>> health = client.get_health_status()
            >>> print(f"Overall status: {health['status']}")
        """
        # Test connection
        conn_test = self.test_connection()

        # Calculate error rate
        total_requests = getattr(self, '_total_requests', 0)
        total_errors = getattr(self, '_total_errors', 0)
        error_rate = (total_errors / max(1, total_requests)) * 100 if total_requests > 0 else 0

        # Determine overall status
        if not conn_test['reachable']:
            status = 'unhealthy'
        elif error_rate > 50:
            status = 'degraded'
        elif error_rate > 10:
            status = 'warning'
        else:
            status = 'healthy'

        return {
            'status': status,
            'connection_reachable': conn_test['reachable'],
            'response_time': conn_test.get('response_time'),
            'logged_in': self._logged_in,
            'error_rate_percent': round(error_rate, 2),
            'total_requests': total_requests,
            'total_errors': total_errors,
            'average_response_time': getattr(self, '_avg_response_time', 0),
            'models_loaded': len(self._model_classes),
            'services_loaded': len(self._service_instances),
            'cache_enabled': self.cache_enabled,
            'last_check': time.time()
        }

    def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Get current rate limiting status.

        Returns:
            Dictionary with rate limit information

        Example:
            >>> status = client.get_rate_limit_status()
            >>> print(f"Tokens available: {status['tokens_available']}")
        """
        with self._rate_limiter._lock:
            current_time = time.time()
            time_passed = current_time - self._rate_limiter._last_call_time
            tokens = min(
                self._rate_limiter.burst_size,
                self._rate_limiter._tokens + time_passed * self._rate_limiter.calls_per_second
            )

            return {
                'calls_per_second': self._rate_limiter.calls_per_second,
                'burst_size': self._rate_limiter.burst_size,
                'tokens_available': round(tokens, 2),
                'tokens_percent': round((tokens / self._rate_limiter.burst_size) * 100, 2),
                'wait_time_if_exhausted': round((self._rate_limiter.burst_size - tokens) / self._rate_limiter.calls_per_second, 3),
                'last_call_time': self._rate_limiter._last_call_time
            }

    def reset_statistics(self) -> None:
        """
        Reset all tracking statistics.

        Example:
            >>> client.reset_statistics()
            >>> # Stats are now reset to zero
        """
        self._total_requests = 0
        self._total_errors = 0
        self._requests_by_method = {}
        self._requests_by_endpoint = {}
        self._response_times = []
        self._avg_response_time = 0
        self._last_request_time = None
        self._last_request_info = None

        if hasattr(self, '_error_history'):
            self._error_history.clear()

        if hasattr(self, '_request_history'):
            self._request_history.clear()

    def refresh_schema(self) -> None:
        """
        Invalidate the on-disk and in-memory schema caches so the next access
        refetches from the Acumatica server.

        Call this after an administrator deploys a customization package or
        otherwise changes the OpenAPI schema - without it, a fresh-looking
        disk cache can mask new or removed endpoints for up to
        ``schema_cache_ttl_hours``.

        The differential pickle cache is left in place on purpose: its per-model
        hashes are compared against the refetched schema and used to skip
        rebuilding components that didn't actually change. If you want a full
        rebuild, use ``clear_cache()`` or init with ``force_rebuild=True``.

        Example:
            >>> # Admin deployed a new customization package
            >>> client.refresh_schema()
            >>> # Next service call / re-init will hit the network
        """
        with self._cache_lock:
            self._schema_cache.clear()
            if hasattr(self._fetch_schema, 'cache_clear'):
                self._fetch_schema.cache_clear()

            if not self.cache_enabled:
                return

            try:
                self._schema_cache_path().unlink()
            except FileNotFoundError:
                pass
            except OSError:
                pass

    def clear_cache(self) -> None:
        """
        Clear all cached data (both memory and disk).

        Example:
            >>> client.clear_cache()
            >>> print("Cache cleared")
        """
        with self._cache_lock:
            # Clear memory caches
            self._schema_cache.clear()
            if hasattr(self._fetch_schema, 'cache_clear'):
                self._fetch_schema.cache_clear()

            # Clear disk cache
            if self.cache_enabled and self.cache_dir.exists():
                try:
                    import shutil
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                except Exception as e:
                    logger.warning(f"Failed to clear disk cache at {self.cache_dir}: {e}")

            # Reset counters
            self._cache_hits = 0
            self._cache_misses = 0

    def help(self, topic: Optional[str] = None) -> None:
        """
        Display help information about the client and its capabilities.
        
        Args:
            topic: Specific topic to get help for ('models', 'services', 'cache', 'performance')
            
        Example:
            >>> client.help()  # General help
            >>> client.help('models')  # Model-specific help
        """
        if topic is None:
            print(f"""
AcumaticaClient Help
===================

Connection Info:
  Base URL: {self.base_url}
  Tenant: {self.tenant}
  Endpoint: {self.endpoint_name} v{self.endpoint_version}
  
Available Resources:
  Models: {len(self._model_classes)} (use client.list_models())
  Services: {len(self._service_instances)} (use client.list_services())
  
Utility Methods:
  client.list_models()                    - List all available models
  client.list_services()                  - List all available services
  client.get_model_info(name)            - Get detailed model information
  client.get_service_info(name)          - Get detailed service information
  client.search_models(pattern)          - Search models by pattern
  client.search_services(pattern)        - Search services by pattern
  client.get_performance_stats()         - Get performance metrics
  client.clear_cache()                   - Clear all caches
  client.help(topic)                     - Get topic-specific help

Batch Calling:
  from easy_acumatica import BatchCall
  
  # Execute multiple calls concurrently with tuple unpacking
  customer, product = BatchCall(
      client.customers.get_by_id.batch("CUST001"),
      client.products.get_by_id.batch("PROD001")
  ).execute()
  
  # All service methods have .batch property for deferred execution
  batch = BatchCall(client.service.method.batch(args))
  
  # Helper functions available:
  create_batch_from_ids(service, ids)     - Batch fetch by IDs
  create_batch_from_filters(service, filters) - Batch with filters

Performance:
  Startup time: {self._startup_time:.2f}s
  Cache: {'enabled' if self.cache_enabled else 'disabled'}
  Cache hit rate: {self._cache_hits / max(1, self._cache_hits + self._cache_misses):.1%}
  
Environment Loading:
  Automatically loads from .env files when no credentials provided
  Searches current directory and parent directories for .env file
  Use env_file parameter to specify custom .env location
  
For specific help topics, use:
  client.help('models')     - Model system help
  client.help('services')   - Service system help  
  client.help('cache')      - Caching system help
  client.help('performance') - Performance optimization help
            """)
            
        elif topic.lower() == 'models':
            print(f"""
Models Help
===========

The client dynamically generates {len(self._model_classes)} model classes from the API schema.
Each model represents an Acumatica entity (like Contact, Invoice, etc.).

Available Models: {', '.join(self.list_models()[:10])}{'...' if len(self.list_models()) > 10 else ''}

Usage Examples:
  # Create a new model instance
  contact = client.models.Contact(Email="test@example.com", DisplayName="Test User")
  
  # Use in API calls
  result = client.contacts.put_entity(contact)
  
  # Get model information
  info = client.get_model_info('Contact')
  print(info['fields'])

Search and Discovery:
  client.list_models()                   - List all models
  client.search_models('contact')        - Find models containing 'contact'
  client.get_model_info('Contact')       - Detailed model info
            """)
        elif topic.lower() == 'batch':
            print(f"""
Batch Calling Help
==================

Execute multiple API calls concurrently for better performance.

Basic Usage:
  customer, product, contact = BatchCall(
      client.customers.get_by_id.batch("CUST001"),
      client.products.get_by_id.batch("PROD001"),
      client.contacts.get_by_id.batch("CONT001")
  ).execute()

Service Method Integration:
  Every service method has a .batch property:
  - client.customers.get_by_id.batch("ID")
  - client.products.get_list.batch(options=query)
  - client.invoices.put_entity.batch(invoice_data)

Advanced Options:
  BatchCall(
      *calls,
      max_concurrent=5,              # Concurrent threads
      timeout=30,                 # Total timeout
      fail_fast=False,            # Stop on first error
      return_exceptions=True,     # Return errors as results
      progress_callback=func      # Progress tracking
  )

Helper Functions:
  # Batch fetch multiple entities by ID
  customers = create_batch_from_ids(
      client.customers, 
      ["CUST001", "CUST002", "CUST003"]
  ).execute()
  
  # Batch with different filters
  results = create_batch_from_filters(
      client.customers,
      [QueryOptions(filter=F.Status == "Active"),
       QueryOptions(filter=F.Status == "Inactive")]
  ).execute()

Performance Benefits:
  - Concurrent execution reduces total time
  - Built-in error handling and retry
  - Progress tracking and statistics
  - Thread-safe operations

Error Handling:
  batch = BatchCall(*calls, return_exceptions=True)
  results = batch.execute()
  
  # Check for errors
  successful_results = batch.get_successful_results()
  failed_calls = batch.get_failed_calls()
  batch.print_summary()
        """) 
        elif topic.lower() == 'services':
            print(f"""
Services Help
=============

The client dynamically generates {len(self._service_instances)} service classes from the API schema.
Each service provides methods for interacting with Acumatica entities.

Available Services: {', '.join(self.list_services()[:10])}{'...' if len(self.list_services()) > 10 else ''}

Common Service Methods:
  get_list()           - Get all entities
  get_by_id(id)        - Get specific entity
  put_entity(data)     - Create/update entity
  delete_by_id(id)     - Delete entity
  
Usage Examples:
  # List all contacts
  contacts = client.contacts.get_list()
  
  # Get specific contact
  contact = client.contacts.get_by_id("CONTACT001")
  
  # Create new contact
  new_contact = client.models.Contact(DisplayName="New Contact")
  result = client.contacts.put_entity(new_contact)

Search and Discovery:
  client.list_services()                 - List all services
  client.search_services('invoice')      - Find services containing 'invoice'  
  client.get_service_info('Contact')     - Detailed service info
            """)
            
        elif topic.lower() == 'cache':
            print(f"""
Caching System Help
===================

Status: {'Enabled' if self.cache_enabled else 'Disabled'}
Cache Directory: {self.cache_dir}
TTL: {self.cache_ttl_hours} hours

The caching system stores generated models to speed up subsequent client initializations.

Statistics:
  Cache Hits: {self._cache_hits}
  Cache Misses: {self._cache_misses}
  Hit Rate: {self._cache_hits / max(1, self._cache_hits + self._cache_misses):.1%}

Cache Management:
  client.clear_cache()                   - Clear all cached data
  
Initialization Options:
  AcumaticaClient(cache_methods=True)         - Enable caching
  AcumaticaClient(cache_ttl_hours=48)        - Set TTL to 48 hours
  AcumaticaClient(force_rebuild=True)        - Force rebuild ignoring cache
  AcumaticaClient(cache_dir=Path('/custom')) - Custom cache directory

Benefits:
  - Faster startup times (especially for large APIs)
  - Reduced API calls during initialization
  - Automatic cache invalidation when schema changes
  
Environment Variables:
  ACUMATICA_CACHE_METHODS=true    - Enable caching via .env
  ACUMATICA_CACHE_TTL_HOURS=48    - Set cache TTL via .env
            """)
            
        elif topic.lower() == 'performance':
            stats = self.get_performance_stats()
            print(f"""
Performance Help
================

Current Performance:
  Startup Time: {stats['startup_time']:.2f}s
  Model Count: {stats['model_count']}
  Service Count: {stats['service_count']}
  Cache Hit Rate: {stats['cache_hit_rate']:.1%}

Optimization Tips:
  1. Enable Caching: Use cache_methods=True for faster subsequent startups
  2. Use .env Files: Automatic credential loading reduces initialization overhead
  3. Adjust Cache TTL: Longer TTL = fewer schema checks = faster startup  
  4. Use Specific Endpoints: Only connect to endpoints you need
  5. Connection Pooling: Client uses connection pooling automatically
  6. Rate Limiting: Configured to respect API limits

High-Performance .env Setup:
  ACUMATICA_URL=https://your-instance.acumatica.com
  ACUMATICA_USERNAME=your-username
  ACUMATICA_PASSWORD=your-password
  ACUMATICA_TENANT=your-tenant
  ACUMATICA_CACHE_METHODS=true
  ACUMATICA_CACHE_TTL_HOURS=48
  
Then simply use: client = AcumaticaClient()

Monitoring:
  client.get_performance_stats()         - Get detailed performance metrics
            """)
        else:
            print(f"Unknown help topic: {topic}")
            print("Available topics: models, services, cache, performance, batch")  # Add 'batch' here

    def login(self) -> int:
        """
        Authenticates and obtains a cookie-based session.
        
        Returns:
            HTTP status code (204 for success, or if already logged in)
            
        Raises:
            AcumaticaAuthError: If authentication fails
        """
        if self._logged_in:
            return 204  # Already logged in
        
        url = f"{self.base_url}/entity/auth/login"
        
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
            return response.status_code
            
        except requests.RequestException as e:
            raise AcumaticaAuthError(f"Login failed: {e}")

    @property
    def scheduler(self) -> TaskScheduler:
        """Get or create the task scheduler for this client."""
        if self._scheduler is None:
            self._scheduler = TaskScheduler(client=self)
        return self._scheduler

    def logout(self) -> int:
        """
        Logs out and invalidates the server-side session.
        
        Returns:
            HTTP status code (204 for success or already logged out)
        """
        if not self._logged_in:
            return 204  # Already logged out
        
        url = f"{self.base_url}/entity/auth/logout"
        
        try:
            # Stop scheduler if running
            if self._scheduler and self._scheduler._running:
                self._scheduler.stop(wait=True, timeout=5)

            response = self.session.post(url, verify=self.verify_ssl, timeout=self.timeout)
            self.session.cookies.clear()
            self._logged_in = False
            return response.status_code

        except Exception as e:
            # Stop scheduler if running
            if self._scheduler and self._scheduler._running:
                self._scheduler.stop(wait=True, timeout=5)

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
        start_time = time.time()

        # Track request for statistics
        if not hasattr(self, '_total_requests'):
            self._total_requests = 0
            self._total_errors = 0
            self._requests_by_method = {}
            self._requests_by_endpoint = {}
            self._response_times = []

        # Apply rate limiting. The token reservation happens under the
        # limiter's lock; the actual sleep happens outside it so concurrent
        # callers don't serialize through one another's wait windows.
        sleep_time = self._rate_limiter._reserve_token()
        if sleep_time > 0:
            time.sleep(sleep_time)
        
        # Set default timeout if not specified
        kwargs.setdefault('timeout', self.timeout)
        kwargs.setdefault('verify', self.verify_ssl)
        
        try:
            # For non-persistent mode, ensure we are logged in
            if not self.persistent_login and not self._logged_in:
                self.login()
            
            resp = self.session.request(method, url, **kwargs)

            # Handle session timeout with retry
            if resp.status_code == 401 and self.retry_on_idle_logout and self._logged_in:
                self._logged_in = False
                self.login()
                resp = self.session.request(method, url, **kwargs)

            response_time = time.time() - start_time

            # Check for HTTP errors and track accordingly
            if not resp.ok:
                # Create a generic error to pass to the tracker.
                # The actual exception raised to the user will be more specific.
                error_obj = AcumaticaError(f"HTTP Error {resp.status_code}")
                self._track_request(method, url, resp.status_code, response_time, error_obj)
                
                # Now, raise the detailed, specific exception for the user.
                _raise_with_detail(resp)
            
            # If we get here, the request was successful
            self._track_request(method, url, resp.status_code, response_time, None)
            return resp

        except requests.RequestException as e:
            # Handles network-level errors (e.g., DNS, connection refused)
            response_time = time.time() - start_time
            status_code = getattr(getattr(e, 'response', None), 'status_code', None)
            self._track_request(method, url, status_code, response_time, e)
            raise

        finally:
            # For non-persistent mode, log out after request
            if not self.persistent_login and self._logged_in:
                self.logout()

    def _track_request(self, method: str, url: str, status_code: Optional[int], response_time: float, error: Optional[Exception]) -> None:
        """Track request for statistics and history."""
        from urllib.parse import urlparse

        # Update basic counters
        self._total_requests += 1
        if error:
            self._total_errors += 1

        # Track by method
        method_upper = method.upper()
        self._requests_by_method[method_upper] = self._requests_by_method.get(method_upper, 0) + 1

        # Track by endpoint
        parsed = urlparse(url)
        path_parts = parsed.path.split('/')
        if 'entity' in path_parts:
            idx = path_parts.index('entity')
            if idx + 3 < len(path_parts):
                endpoint = path_parts[idx + 3]  # Get entity name
                self._requests_by_endpoint[endpoint] = self._requests_by_endpoint.get(endpoint, 0) + 1

        # Track response times
        self._response_times.append(response_time)
        if len(self._response_times) > 100:  # Keep only last 100
            self._response_times.pop(0)

        # Calculate average response time
        self._avg_response_time = sum(self._response_times) / len(self._response_times)
        self._last_request_time = time.time()

        # Store last request info
        self._last_request_info = {
            'timestamp': time.time(),
            'method': method_upper,
            'url': url,
            'status_code': status_code,
            'response_time': response_time,
            'error': str(error) if error else None
        }

        # Track in request history if enabled
        if getattr(self, '_request_history_enabled', False):
            if not hasattr(self, '_request_history'):
                self._request_history = []

            # Extract endpoint name for easier filtering
            endpoint_name = None
            parsed = urlparse(url)
            path_parts = parsed.path.split('/')
            if 'entity' in path_parts:
                idx = path_parts.index('entity')
                if idx + 3 < len(path_parts):
                    endpoint_name = path_parts[idx + 3]

            self._request_history.insert(0, {
                'timestamp': time.time(),
                'method': method_upper,
                'url': url,
                'endpoint': endpoint_name,
                'status_code': status_code,
                'response_time': response_time,
                'error': str(error) if error else None,
                'success': error is None
            })

            # Limit history size
            max_items = getattr(self, '_request_history_max', 100)
            if len(self._request_history) > max_items:
                self._request_history = self._request_history[:max_items]

        # Track errors for history
        if error:
            if not hasattr(self, '_error_history'):
                self._error_history = []

            self._error_history.insert(0, {
                'timestamp': time.time(),
                'method': method_upper,
                'url': url,
                'status_code': status_code,
                'message': str(error),
                'response_time': response_time
            })

            # Keep only last 50 errors
            if len(self._error_history) > 50:
                self._error_history = self._error_history[:50]

    def close(self) -> None:
        """
        Closes the client session and logs out if necessary.
        
        This method should be called when you're done with the client
        to ensure proper cleanup. It's automatically called on exit.
        """
        # Close AcumaticaClient
        
        try:
            if self._logged_in:
                self.logout()
        except Exception as e:
            logger.debug(f"Error during logout in close(): {e}")

        try:
            self.session.close()
        except Exception as e:
            logger.debug(f"Error closing session in close(): {e}")
        
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
        cache_info = f"cache={'enabled' if self.cache_enabled else 'disabled'}"
        perf_info = f"startup={self._startup_time:.2f}s" if self._startup_time else "startup=pending"
        return (f"<AcumaticaClient("
                f"base_url='{self.base_url}', "
                f"tenant='{self.tenant}', "
                f"user='{self.username}', "
                f"logged_in={self._logged_in}, "
                f"{cache_info}, "
                f"{perf_info})>")


def _cleanup_all_clients() -> None:
    """Cleanup function called on interpreter shutdown."""
    # Cleaning up all active AcumaticaClient instances
    
    # Create a list to avoid modifying set during iteration
    clients = list(_active_clients)
    
    for client in clients:
        try:
            client.close()
        except Exception as e:
            logger.debug(f"Error cleaning up client at exit: {e}")