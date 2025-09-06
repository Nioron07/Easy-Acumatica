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
import warnings
from datetime import datetime, timedelta
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Type, Union
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
from .core import BaseDataClassModel, BaseService

__all__ = ["AcumaticaClient"]

# Configure logging
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
        logger.warning(f"Failed to load .env file {env_file_path}: {e}")
    
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
            logger.debug(f"Found .env file at: {env_file}")
            return env_file
    
    logger.debug("No .env file found")
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
                        logger.info(f"Loaded configuration from: {env_file_path}")
                    else:
                        logger.warning(f"Specified .env file not found: {env_file_path}")
                else:
                    # Search for .env file automatically
                    found_env_file = find_env_file()
                    if found_env_file:
                        env_vars_loaded = load_env_file(found_env_file)
                        logger.info(f"Automatically loaded configuration from: {found_env_file}")
                
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
        
        logger.info(f"AcumaticaClient initialized for {self.base_url} (tenant: {self.tenant}) "
                   f"in {self._startup_time:.2f}s (cache {'enabled' if self.cache_enabled else 'disabled'})")

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

    def _build_components(self) -> None:
        """Build models and services with caching support."""
        cache_key = self._get_cache_key()
        cache_file = self.cache_dir / f"{cache_key}.pkl"
        schema_hash_file = self.cache_dir / f"{cache_key}_schema_hash.txt"
        
        use_cache = (
            self.cache_enabled and 
            not self.force_rebuild and
            cache_file.exists() and 
            schema_hash_file.exists() and
            self._is_cache_valid(schema_hash_file)
        )
        
        if use_cache:
            try:
                # Load from cache
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                
                # Restore models
                for name, model_class in cached_data['models'].items():
                    setattr(self.models, name, model_class)
                    self._model_classes[name] = model_class
                
                # Restore services - we need to rebuild these as they can't be pickled easily
                self._cache_hits += 1
                logger.info(f"Loaded {len(cached_data['models'])} models from cache")
                
                # Still need to build services fresh
                schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
                self._build_dynamic_services(schema)
                
                return
                
            except Exception as e:
                logger.warning(f"Failed to load from cache: {e}. Rebuilding...")
                self._cache_misses += 1
        else:
            self._cache_misses += 1
        
        # Build from scratch
        schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
        self._build_dynamic_models(schema)
        self._build_dynamic_services(schema)
        
        # Cache the results if caching is enabled
        if self.cache_enabled:
            self._save_to_cache(cache_file, schema_hash_file, schema)

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
                logger.debug("Cache expired due to TTL")
                return False
            
            # Check schema hash
            with open(schema_hash_file, 'r') as f:
                cached_hash = f.read().strip()
            
            current_schema = self._fetch_schema(self.endpoint_name, self.endpoint_version)
            current_hash = hashlib.md5(json.dumps(current_schema, sort_keys=True).encode()).hexdigest()
            
            is_valid = cached_hash == current_hash
            if not is_valid:
                logger.debug("Cache invalid due to schema changes")
            return is_valid
            
        except Exception as e:
            logger.debug(f"Cache validation failed: {e}")
            return False

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
            
            logger.debug(f"Saved cache with {len(cache_data['models'])} models")
            
        except Exception as e:
            logger.warning(f"Failed to save cache: {e}")

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
            
            # Attach each generated class to the models module and store reference
            for name, model_class in model_dict.items():
                # Only set __module__ if it's actually a class, not a dict
                if hasattr(model_class, '__module__'):
                    model_class.__module__ = 'easy_acumatica.models'
                setattr(self.models, name, model_class)
                self._model_classes[name] = model_class
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
                self._service_instances[name] = service_instance
                logger.debug(f"Created service: {attr_name}")
                
            logger.info(f"Successfully built {len(services_dict)} services")
            
        except Exception as e:
            raise AcumaticaError(f"Failed to build dynamic services: {e}")

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
                logger.info("Disk cache cleared")
            except Exception as e:
                logger.warning(f"Failed to clear disk cache: {e}")
        
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
            print("Available topics: models, services, cache, performance")

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
    logger.info("Cleaning up all active AcumaticaClient instances")
    
    # Create a list to avoid modifying set during iteration
    clients = list(_active_clients)
    
    for client in clients:
        try:
            client.close()
        except Exception as e:
            logger.error(f"Error cleaning up client: {e}")