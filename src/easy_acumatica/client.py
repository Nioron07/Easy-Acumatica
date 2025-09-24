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
import hashlib
import inspect
import json
import logging
import os
import pickle
import time
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
from weakref import WeakSet
import xml.etree.ElementTree as ET

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from . import models
from .config import AcumaticaConfig
from .exceptions import AcumaticaAuthError, AcumaticaError, AcumaticaConnectionError
from .helpers import _raise_with_detail
from .model_factory import ModelFactory
from .service_factory import ServiceFactory
from .core import BatchMethodWrapper
from .utils import RateLimiter, retry_on_error, validate_entity_id
from .core import BaseDataClassModel, BaseService

__all__ = ["AcumaticaClient"]

# Logger instance (not used directly, available for external use)
logger = logging.getLogger(__name__)

# Track all client instances for cleanup
_active_clients: WeakSet[AcumaticaClient] = WeakSet()


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
        pass  # Silently skip if .env file cannot be loaded

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
        cache_methods: bool = False,
        cache_ttl_hours: int = 24,
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
        self.retry_on_idle_logout: bool = retry_on_idle_logout
        self.endpoint_name: str = endpoint_name
        self.endpoint_version: Optional[str] = endpoint_version
        self.timeout: int = timeout or self._default_timeout
        
        # Cache configuration
        self.cache_enabled: bool = cache_methods
        self.cache_ttl_hours: int = cache_ttl_hours
        self.force_rebuild: bool = force_rebuild
        self.cache_dir: Path = cache_dir or Path.home() / ".easy_acumatica_cache"
        
        if self.cache_enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize session with connection pooling and retry logic
        self.session: requests.Session = self._create_session()
        
        # Rate limiter
        self._rate_limiter = RateLimiter(calls_per_second=rate_limit_calls_per_second)
        
        # State tracking
        self.endpoints: Dict[str, Dict] = {}
        self._logged_in: bool = False
        self._available_services: Set[str] = set()
        self._schema_cache: Dict[str, Any] = {}
        self._model_classes: Dict[str, Type[BaseDataClassModel]] = {}
        self._service_instances: Dict[str, BaseService] = {}
        
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
                except:
                    pass
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
            "User-Agent": f"easy-acumatica/0.4.9 Python/{requests.__version__}",
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
        
        # Store endpoint information
        for endpoint in endpoints:
            name = endpoint.get('name')
            if name and (name not in self.endpoints or 
                        endpoint.get('version', '0') > self.endpoints[name].get('version', '0')):
                self.endpoints[name] = endpoint

    def _build_components(self) -> None:
        """Build models and services with differential caching support."""
        if not self.cache_enabled:
            # No caching - build everything from scratch
            schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
            self._build_dynamic_models(schema)
            self._build_dynamic_services(schema)
            return

        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        
        # Always fetch current schema and inquiries to compare
        current_schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
        current_inquiries_xml = None
        
        try:
            current_inquiries_xml = self._fetch_gi_xml()
        except Exception as e:
            pass  # Could not fetch inquiries XML
        
        if self.force_rebuild or not cache_file.exists():
            # Fresh build
            self._build_dynamic_models(current_schema)
            self._build_dynamic_services(current_schema)
            if current_inquiries_xml:
                self._build_inquiries_service(current_inquiries_xml)
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
                self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)
                self._cache_misses += 1
                return

            # Perform differential update
            self._perform_differential_update(cached_data, current_schema, current_inquiries_xml)
            self._save_differential_cache(cache_file, current_schema, current_inquiries_xml)
            
        except Exception as e:
            # Differential caching failed, rebuild from scratch
            self._build_dynamic_models(current_schema)
            self._build_dynamic_services(current_schema)
            if current_inquiries_xml:
                self._build_inquiries_service(current_inquiries_xml)
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
                'version': '1.1',  # Cache format version (updated for inquiries)
                'timestamp': time.time(),
                'schema_hash': self._calculate_schema_hash(schema),
                'inquiries_hash': self._calculate_inquiries_xml_hash(inquiries_xml_path) if inquiries_xml_path else None,
                'model_hashes': model_hashes,
                'service_hashes': service_hashes,
                'inquiry_hashes': inquiry_hashes,
                'models': self._model_classes.copy(),
                'service_definitions': self._extract_service_definitions(schema),
                'inquiry_definitions': self._extract_inquiry_definitions(inquiries_xml_path) if inquiries_xml_path else {},
                'endpoint_info': {
                    'name': self.endpoint_name,
                    'version': self.endpoint_version,
                    'base_url': self.base_url,
                    'tenant': self.tenant
                }
            }
            
            # Save to temporary file first, then move to prevent corruption
            temp_file = cache_file.with_suffix('.tmp')
            with open(temp_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            temp_file.replace(cache_file)
            # Cache saved successfully
            
        except Exception as e:
            pass  # Failed to save differential cache

    def _load_differential_cache(self, cache_file: Path) -> Dict[str, Any]:
        """Load and validate differential cache."""
        try:
            with open(cache_file, 'rb') as f:
                cached_data = pickle.load(f)
            
            # Validate cache format version
            cache_version = cached_data.get('version', '1.0')
            if cache_version not in ['1.0', '1.1']:
                return None  # Cache format version not supported
            
            # Check TTL
            cache_age = time.time() - cached_data.get('timestamp', 0)
            if cache_age > (self.cache_ttl_hours * 3600):
                return None  # Cache expired due to TTL
            
            # Validate endpoint compatibility
            endpoint_info = cached_data.get('endpoint_info', {})
            if (endpoint_info.get('name') != self.endpoint_name or
                endpoint_info.get('version') != self.endpoint_version or
                endpoint_info.get('base_url') != self.base_url or
                endpoint_info.get('tenant') != self.tenant):
                return None  # Cache endpoint info mismatch
                
            return cached_data
        except requests.exceptions.ConnectionError:
            # Network error during cache validation, using stale cache
            return cached_data
        except Exception as e:
            return None  # Failed to load cache

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
            pass  # Error calculating inquiry hashes
        
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
            pass  # Error extracting inquiry definitions
        
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
                    
                # Built inquiries service successfully
                pass

        except Exception as e:
            pass  # Could not build inquiries service

    def _clear_inquiry_methods(self, service) -> None:
        """Remove existing inquiry methods from service."""
        # Get list of methods that look like inquiry methods
        methods_to_remove = []
        for attr_name in dir(service):
            if not attr_name.startswith('_') and callable(getattr(service, attr_name)):
                # Skip built-in BaseService methods
                if attr_name not in ['_get', '_put', '_post_action', '_delete', '_get_files', 
                                   '_get_schema', '_get_inquiry', '_request', '_get_url',
                                   '_get_by_keys']:
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
            import requests
            response = requests.get(
                url=metadata_url,
                auth=(self.username, self._password)
            )
            response.raise_for_status()

            # Save to metadata directory
            import os
            package_dir = os.path.dirname(os.path.abspath(__file__))
            metadata_dir = os.path.join(package_dir, ".metadata")
            os.makedirs(metadata_dir, exist_ok=True)

            output_path = os.path.join(metadata_dir, "odata_inquiries_schema.xml")
            with open(output_path, 'wb') as f:
                f.write(response.content)

            # Inquiries schema saved successfully
            return output_path

        except Exception as e:
            raise  # Error fetching inquiries metadata

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
        """Calculate overall schema hash for quick comparison."""
        hash_content = {
            'info': schema.get('info', {}),
            'servers': schema.get('servers', []),
            'paths_count': len(schema.get('paths', {})),
            'schemas_count': len(schema.get('components', {}).get('schemas', {}))
        }
        hash_input = json.dumps(hash_content, sort_keys=True)
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
                pass  # Model built successfully
            except Exception as e:
                pass  # Failed to build model

    def _build_specific_services(self, schema: Dict[str, Any], service_names: Set[str]) -> None:
        """Build only specific services from the schema."""
        # Build specific services from the schema
        
        factory = ServiceFactory(self, schema)
        all_services = factory.build_services()
        
        for service_name in service_names:
            if service_name in all_services:
                service_instance = all_services[service_name]
                # Convert PascalCase to snake_case
                snake_case = ''.join(['_' + i.lower() if i.isupper() else i for i in service_name]).lstrip('_')
                # Handle pluralization properly
                if service_name == 'Inquiries' or snake_case.endswith('ies'):
                    attr_name = snake_case
                elif snake_case.endswith('inquiry'):
                    # inquiry -> inquiries
                    attr_name = snake_case[:-1] + 'ies'
                elif snake_case.endswith('class'):
                    # class -> classes
                    attr_name = snake_case + 'es'
                elif not snake_case.endswith('s'):
                    attr_name = snake_case + 's'
                else:
                    attr_name = snake_case
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
        attr_name = ''.join(['_' + i.lower() if i.isupper() else i for i in service_name]).lstrip('_') + 's'
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

    def _is_cache_valid(self, schema_hash_file: Path) -> bool:
        """Check if cached data is still valid based on schema hash and TTL."""
        try:
            # Check TTL
            cache_age = time.time() - schema_hash_file.stat().st_mtime
            if cache_age > (self.cache_ttl_hours * 3600):
                return False  # Cache expired due to TTL
            
            # Check schema hash
            with open(schema_hash_file, 'r') as f:
                cached_hash = f.read().strip()
            
            current_schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
            current_hash = hashlib.md5(json.dumps(current_schema, sort_keys=True).encode()).hexdigest()
            
            is_valid = cached_hash == current_hash
            if not is_valid:
                pass  # Cache invalid due to schema changes
            return is_valid
            
        except Exception as e:
            return False  # Cache validation failed

    def _save_to_cache(self, cache_file: Path, schema_hash_file: Path, schema: Dict[str, Any]) -> None:
        """Save current models to cache."""
        try:
            # Only cache the models as services are easier to rebuild
            cache_data = {
                'models': self._model_classes.copy(),
                'timestamp': time.time()
            }
            
            # Save cache file
            with open(cache_file, 'wb') as f:
                pickle.dump(cache_data, f)
            
            # Save schema hash
            schema_hash = hashlib.md5(json.dumps(schema, sort_keys=True).encode()).hexdigest()
            with open(schema_hash_file, 'w') as f:
                f.write(schema_hash)
            
            pass  # Cache saved successfully
            
        except Exception as e:
            pass  # Failed to save cache

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
            version = self.endpoints[endpoint_name]['version']
        cache_key = f"{endpoint_name}:{version}"
        if cache_key in self._schema_cache:
            # Using cached schema
            return self._schema_cache[cache_key]
        
        schema_url = f"{self.base_url}/entity/{endpoint_name}/{version}/swagger.json"
        if self.tenant:
            schema_url += f"?company={self.tenant}"
        
        # Fetch schema from API
        
        try:
            schema = self._request("get", schema_url).json()
            self._schema_cache[cache_key] = schema
            return schema
        except Exception as e:
            raise AcumaticaError(f"Failed to fetch schema for {endpoint_name} v{version}: {e}")

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
                # Convert PascalCase to snake_case
                snake_case = ''.join(['_' + i.lower() if i.isupper() else i for i in name]).lstrip('_')
                # Handle pluralization properly
                if name == 'Inquiries' or snake_case.endswith('ies'):
                    attr_name = snake_case
                elif snake_case.endswith('inquiry'):
                    # inquiry -> inquiries
                    attr_name = snake_case[:-1] + 'ies'
                elif snake_case.endswith('class'):
                    # class -> classes
                    attr_name = snake_case + 'es'
                elif not snake_case.endswith('s'):
                    attr_name = snake_case + 's'
                else:
                    attr_name = snake_case
                
                # Add batch support to all service methods
                self._add_batch_support_to_service(service_instance)
                
                setattr(self, attr_name, service_instance)
                self._available_services.add(name)
                self._service_instances[name] = service_instance
                pass  # Service created successfully
                
            # Successfully built services
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic services: {e}")
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
                    'required': not str(field_type).startswith('Optional')
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
        
        return {
            'name': service_name,
            'entity_name': service.entity_name,
            'endpoint_name': getattr(service, 'endpoint_name', 'Default'),
            'methods': methods,
            'method_count': len(methods),
            'client_attribute': ''.join(['_' + i.lower() if i.isupper() else i for i in service_name]).lstrip('_') + 's'
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
                    'max_retries': adapter.max_retries.total if hasattr(adapter.max_retries, 'total') else 0
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
        import time

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
        import os

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
        import time

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

    def disable_request_history(self) -> None:
        """Disable request/response history tracking."""
        self._request_history_enabled = False

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

    def clear_cache(self) -> None:
        """
        Clear all cached data (both memory and disk).

        Example:
            >>> client.clear_cache()
            >>> print("Cache cleared")
        """
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
                pass  # Failed to clear disk cache
        
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

    @retry_on_error(max_attempts=3, delay=1.0, backoff=2.0)
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
            response = self.session.post(url, verify=self.verify_ssl, timeout=self.timeout)
            self.session.cookies.clear()
            self._logged_in = False
            return response.status_code
            
        except Exception as e:
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
        import time
        start_time = time.time()

        # Track request for statistics
        if not hasattr(self, '_total_requests'):
            self._total_requests = 0
            self._total_errors = 0
            self._requests_by_method = {}
            self._requests_by_endpoint = {}
            self._response_times = []

        # Apply rate limiting by calling the rate limiter directly
        with self._rate_limiter._lock:
            current_time = time.time()
            time_passed = current_time - self._rate_limiter._last_call_time
            self._rate_limiter._tokens = min(
                self._rate_limiter.burst_size,
                self._rate_limiter._tokens + time_passed * self._rate_limiter.calls_per_second
            )
            if self._rate_limiter._tokens < 1.0:
                sleep_time = (1.0 - self._rate_limiter._tokens) / self._rate_limiter.calls_per_second
                time.sleep(sleep_time)
                self._rate_limiter._tokens = 1.0
            self._rate_limiter._tokens -= 1.0
            self._rate_limiter._last_call_time = time.time()
        
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
        import time
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
            pass  # Error during logout
        
        try:
            self.session.close()
        except Exception as e:
            pass  # Error closing session
        
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
            pass  # Error cleaning up client