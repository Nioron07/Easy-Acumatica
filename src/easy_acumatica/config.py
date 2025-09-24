"""easy_acumatica.config
=====================

Enhanced configuration management for Easy Acumatica with caching support.

Provides flexible configuration options through:
- Direct parameters
- Environment variables  
- Configuration files (JSON/YAML)
- Secure credential storage integration
- Performance and caching options
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional
from .exceptions import AcumaticaConfigError, ErrorCode

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class AcumaticaConfig:
    """
    Enhanced configuration for Acumatica client with caching and performance options.
    
    This class centralizes all configuration options and provides
    multiple ways to load and save configurations.
    
    Attributes:
        base_url: Root URL of the Acumatica instance
        username: Authentication username
        password: Authentication password (handle with care)
        tenant: Tenant/Company identifier
        branch: Optional branch within the tenant
        locale: Optional UI locale (e.g., "en-US")
        verify_ssl: Whether to verify SSL certificates
        persistent_login: Keep session alive between requests
        retry_on_idle_logout: Auto-retry on session timeout
        endpoint_name: API endpoint name (default: "Default")
        endpoint_version: Specific API version to use
        timeout: Request timeout in seconds
        max_retries: Maximum retry attempts
        rate_limit_calls_per_second: API rate limiting
        cache_methods: Enable method caching for faster startup
        cache_ttl_hours: Cache time-to-live in hours
        cache_dir: Directory for storing cache files
        force_rebuild: Force rebuild ignoring cache
    """
    
    # Required fields
    base_url: str
    username: str
    password: str
    tenant: str
    
    # Optional fields with defaults
    branch: Optional[str] = None
    locale: Optional[str] = None
    verify_ssl: bool = True
    persistent_login: bool = True
    retry_on_idle_logout: bool = True
    endpoint_name: str = "Default"
    endpoint_version: Optional[str] = None
    
    # Advanced settings
    timeout: int = 60
    max_retries: int = 3
    rate_limit_calls_per_second: float = 10.0
    
    # Caching and performance options
    cache_methods: bool = False
    cache_ttl_hours: int = 24
    cache_dir: Optional[Path] = None
    force_rebuild: bool = False
    
    # Additional options
    log_level: str = "INFO"
    log_file: Optional[str] = None
    
    @classmethod
    def from_env(cls, prefix: str = "ACUMATICA_") -> "AcumaticaConfig":
        """
        Create configuration from environment variables.
        
        Args:
            prefix: Environment variable prefix (default: "ACUMATICA_")
            
        Returns:
            AcumaticaConfig instance
            
        Raises:
            KeyError: If required environment variables are missing
            
        Example:
            Set environment variables:
            - ACUMATICA_URL=https://example.acumatica.com
            - ACUMATICA_USERNAME=myuser
            - ACUMATICA_PASSWORD=mypass
            - ACUMATICA_TENANT=MyCompany
            - ACUMATICA_CACHE_METHODS=true
            - ACUMATICA_CACHE_TTL_HOURS=48
        """
        def get_env(key: str, default: Any = None, type_fn: callable = str) -> Any:
            """Helper to get and convert environment variables."""
            value = os.getenv(f"{prefix}{key}", default)
            if value is None:
                return None
            if type_fn == bool:
                # Handle the case where default is already a bool
                if isinstance(value, bool):
                    return value
                # Convert string to bool
                return str(value).lower() in ('true', '1', 'yes', 'on')
            elif type_fn == Path:
                return Path(value) if value else None
            return type_fn(value)
        
        # Check for required fields
        required = ['URL', 'USERNAME', 'PASSWORD', 'TENANT']
        missing = [f"{prefix}{r}" for r in required if not os.getenv(f"{prefix}{r}")]
        if missing:
            raise AcumaticaConfigError(
                f"Missing required environment variables: {', '.join(missing)}",
                missing_field=missing[0] if len(missing) == 1 else None
            )
        
        return cls(
            base_url=os.environ[f"{prefix}URL"],
            username=os.environ[f"{prefix}USERNAME"],
            password=os.environ[f"{prefix}PASSWORD"],
            tenant=os.environ[f"{prefix}TENANT"],
            branch=get_env("BRANCH"),
            locale=get_env("LOCALE"),
            verify_ssl=get_env("VERIFY_SSL", True, bool),
            persistent_login=get_env("PERSISTENT_LOGIN", True, bool),
            retry_on_idle_logout=get_env("RETRY_ON_IDLE", True, bool),
            endpoint_name=get_env("ENDPOINT_NAME", "Default"),
            endpoint_version=get_env("ENDPOINT_VERSION"),
            timeout=get_env("TIMEOUT", 60, int),
            max_retries=get_env("MAX_RETRIES", 3, int),
            rate_limit_calls_per_second=get_env("RATE_LIMIT", 10.0, float),
            cache_methods=get_env("CACHE_METHODS", False, bool),
            cache_ttl_hours=get_env("CACHE_TTL_HOURS", 24, int),
            cache_dir=get_env("CACHE_DIR", None, Path),
            force_rebuild=get_env("FORCE_REBUILD", False, bool),
            log_level=get_env("LOG_LEVEL", "INFO"),
            log_file=get_env("LOG_FILE"),
        )
    
    @classmethod
    def from_file(cls, path: Path, file_format: Optional[str] = None) -> "AcumaticaConfig":
        """
        Load configuration from a file.
        
        Args:
            path: Path to configuration file
            file_format: Format ('json' or 'yaml'). Auto-detected if None.
            
        Returns:
            AcumaticaConfig instance
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is unsupported
        """
        path = Path(path)
        if not path.exists():
            raise AcumaticaConfigError(
                f"Configuration file not found: {path}",
                suggestions=[
                    f"Create the configuration file at: {path}",
                    "Check if the file path is correct",
                    "Use environment variables instead"
                ]
            )
        
        # Auto-detect format from extension
        if file_format is None:
            file_format = path.suffix.lower().lstrip('.')
        
        with open(path, 'r') as f:
            if file_format == 'json':
                data = json.load(f)
            elif file_format in ('yaml', 'yml'):
                if not HAS_YAML:
                    raise AcumaticaConfigError(
                        "PyYAML is required for YAML config files",
                        suggestions=[
                            "Install PyYAML with: pip install pyyaml",
                            "Use a JSON config file instead",
                            "Use environment variables"
                        ]
                    )
                data = yaml.safe_load(f)
            else:
                raise AcumaticaConfigError(
                        f"Unsupported file format: {file_format}",
                        suggestions=[
                            "Use .json, .yaml, or .yml file extensions",
                            "Check the file extension is correct"
                        ]
                    )
        
        # Handle potential key variations and Path conversion
        normalized_data = {}
        for key, value in data.items():
            # Convert from various naming conventions
            normalized_key = key.lower().replace('-', '_')
            
            # Convert cache_dir string to Path
            if normalized_key == 'cache_dir' and value is not None:
                value = Path(value)
                
            normalized_data[normalized_key] = value
        
        return cls(**normalized_data)
    
    def to_file(self, path: Path, file_format: Optional[str] = None, 
                include_password: bool = False) -> None:
        """
        Save configuration to a file.
        
        Args:
            path: Output file path
            file_format: Format ('json' or 'yaml'). Auto-detected if None.
            include_password: Whether to include password (default: False)
            
        Warning:
            Saving passwords to files is a security risk. Consider using
            environment variables or secure credential storage instead.
        """
        path = Path(path)
        
        # Auto-detect format from extension
        if file_format is None:
            file_format = path.suffix.lower().lstrip('.')
        
        # Create dictionary excluding None values
        data = {}
        for key, value in self.__dict__.items():
            if value is None:
                continue
            
            # Convert Path to string for serialization
            if isinstance(value, Path):
                value = str(value)
                
            data[key] = value
        
        # Remove password unless explicitly requested
        if not include_password:
            data.pop('password', None)
        
        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w') as f:
            if file_format == 'json':
                json.dump(data, f, indent=2)
            elif file_format in ('yaml', 'yml'):
                if not HAS_YAML:
                    raise AcumaticaConfigError(
                        "PyYAML is required for YAML config files",
                        suggestions=[
                            "Install PyYAML with: pip install pyyaml",
                            "Use a JSON config file instead",
                            "Use environment variables"
                        ]
                    )
                yaml.dump(data, f, default_flow_style=False)
            else:
                raise AcumaticaConfigError(
                        f"Unsupported file format: {file_format}",
                        suggestions=[
                            "Use .json, .yaml, or .yml file extensions",
                            "Check the file extension is correct"
                        ]
                    )
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcumaticaConfig":
        """
        Create configuration from a dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            AcumaticaConfig instance
        """
        # Filter out any extra keys and handle Path conversion
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {}
        
        for k, v in data.items():
            if k in valid_fields:
                # Convert cache_dir string to Path if needed
                if k == 'cache_dir' and v is not None and not isinstance(v, Path):
                    v = Path(v)
                filtered_data[k] = v
                
        return cls(**filtered_data)
    
    def to_dict(self, include_password: bool = False, include_paths_as_strings: bool = True) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            include_password: Whether to include password
            include_paths_as_strings: Convert Path objects to strings
            
        Returns:
            Configuration dictionary
        """
        data = {}
        for k, v in self.__dict__.items():
            if v is None:
                continue
                
            # Convert Path to string if requested
            if include_paths_as_strings and isinstance(v, Path):
                v = str(v)
                
            data[k] = v
            
        if not include_password and 'password' in data:
            data.pop('password')
            
        return data
    
    def validate(self) -> None:
        """
        Validate configuration values.
        
        Raises:
            ValueError: If configuration is invalid
        """
        # Check required fields
        if not self.base_url:
            raise AcumaticaConfigError(
                "base_url is required",
                missing_field="base_url"
            )
        if not self.username:
            raise AcumaticaConfigError(
                "username is required",
                missing_field="username"
            )
        if not self.password:
            raise AcumaticaConfigError(
                "password is required",
                missing_field="password"
            )
        if not self.tenant:
            raise AcumaticaConfigError(
                "tenant is required",
                missing_field="tenant"
            )
        
        # Validate URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise AcumaticaConfigError(
                "base_url must start with http:// or https://",
                suggestions=[
                    "Add https:// to the beginning of your URL",
                    f"Example: https://{self.base_url}"
                ]
            )
        
        # Validate numeric ranges
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.rate_limit_calls_per_second <= 0:
            raise ValueError("rate_limit_calls_per_second must be positive")
        if self.cache_ttl_hours <= 0:
            raise ValueError("cache_ttl_hours must be positive")
        
        # Validate log level
        valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_log_levels)}")
        
        # Validate cache directory
        if self.cache_dir is not None and not isinstance(self.cache_dir, Path):
            raise ValueError("cache_dir must be a Path object or None")
    
    def get_cache_dir(self) -> Path:
        """
        Get the effective cache directory.
        
        Returns:
            Path to cache directory (default if not specified)
        """
        if self.cache_dir is not None:
            return self.cache_dir
        return Path.home() / ".easy_acumatica_cache"
    
    def optimize_for_performance(self) -> "AcumaticaConfig":
        """
        Return a copy of this config optimized for performance.
        
        Returns:
            Optimized configuration instance
        """
        optimized_dict = self.to_dict(include_password=True, include_paths_as_strings=False)
        
        # Performance optimizations
        optimized_dict.update({
            'cache_methods': True,
            'cache_ttl_hours': 48,  # Longer cache
            'timeout': 30,          # Shorter timeout for faster failures
            'persistent_login': True,
            'retry_on_idle_logout': True,
        })
        
        return self.from_dict(optimized_dict)
    
    def optimize_for_development(self) -> "AcumaticaConfig":
        """
        Return a copy of this config optimized for development.
        
        Returns:
            Development-optimized configuration instance
        """
        dev_dict = self.to_dict(include_password=True, include_paths_as_strings=False)
        
        # Development optimizations
        dev_dict.update({
            'cache_methods': False,      # Disable cache for fresh data
            'force_rebuild': True,       # Always rebuild
            'log_level': 'DEBUG',        # More verbose logging
            'timeout': 60,               # Longer timeout for debugging
        })
        
        return self.from_dict(dev_dict)
    
    def mask_sensitive_data(self) -> str:
        """
        Return a string representation with sensitive data masked.
        
        Returns:
            String with password masked
        """
        data = self.to_dict(include_password=False)
        data['password'] = '***MASKED***'
        return f"AcumaticaConfig({data})"
    
    def __repr__(self) -> str:
        """Safe string representation without sensitive data."""
        return self.mask_sensitive_data()


def load_config(
    config_path: Optional[Path] = None,
    env_prefix: str = "ACUMATICA_",
    use_env_override: bool = True,
    optimize_for: Optional[str] = None
) -> AcumaticaConfig:
    """
    Load configuration with fallback hierarchy and optional optimization.
    
    Priority order:
    1. Environment variables (if use_env_override=True)
    2. Config file (if provided)
    3. Environment variables (if no config file)
    
    Args:
        config_path: Optional path to config file
        env_prefix: Environment variable prefix
        use_env_override: Allow env vars to override config file
        optimize_for: Optional optimization preset ('performance' or 'development')
        
    Returns:
        AcumaticaConfig instance
        
    Example:
        >>> # Load from file with env overrides
        >>> config = load_config(Path("config.json"))
        >>> 
        >>> # Load from environment only
        >>> config = load_config()
        >>> 
        >>> # Load with performance optimization
        >>> config = load_config(optimize_for='performance')
    """
    config = None
    
    # Try loading from file first
    if config_path and config_path.exists():
        config = AcumaticaConfig.from_file(config_path)
    
    # Try environment variables
    try:
        env_config = AcumaticaConfig.from_env(env_prefix)
        if config is None:
            config = env_config
        elif use_env_override:
            # Override file config with env values
            env_dict = env_config.to_dict(include_password=True, include_paths_as_strings=False)
            config_dict = config.to_dict(include_password=True, include_paths_as_strings=False)
            config_dict.update({k: v for k, v in env_dict.items() if v is not None})
            config = AcumaticaConfig.from_dict(config_dict)
    except KeyError:
        if config is None:
            raise
    
    if config is None:
        raise ValueError("No configuration source available")
    
    # Apply optimization if requested
    if optimize_for == 'performance':
        config = config.optimize_for_performance()
    elif optimize_for == 'development':
        config = config.optimize_for_development()
    elif optimize_for is not None:
        raise ValueError(f"Unknown optimization preset: {optimize_for}")
    
    # Validate before returning
    config.validate()
    return config


def create_sample_config(path: Path, include_caching: bool = True) -> None:
    """
    Create a sample configuration file with helpful comments.
    
    Args:
        path: Path where to save the sample config
        include_caching: Whether to include caching options
    """
    config_data = {
        "base_url": "https://your-instance.acumatica.com",
        "username": "your-username",
        "password": "your-password",  # Consider using environment variables
        "tenant": "your-company",
        "branch": "MAIN",  # Optional
        "verify_ssl": True,
        "timeout": 60,
        "rate_limit_calls_per_second": 10.0
    }
    
    if include_caching:
        config_data.update({
            "cache_methods": True,
            "cache_ttl_hours": 24,
            "cache_dir": "~/.easy_acumatica_cache",  # Optional custom cache directory
            "force_rebuild": False
        })
    
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write with comments if JSON
    if path.suffix.lower() == '.json':
        with open(path, 'w') as f:
            f.write('{\n')
            f.write('  // Acumatica connection settings\n')
            f.write('  "base_url": "https://your-instance.acumatica.com",\n')
            f.write('  "username": "your-username",\n')
            f.write('  "password": "your-password",  // Consider using environment variables\n')
            f.write('  "tenant": "your-company",\n')
            f.write('  "branch": "MAIN",  // Optional\n')
            f.write('  \n')
            f.write('  // Connection options\n')
            f.write('  "verify_ssl": true,\n')
            f.write('  "timeout": 60,\n')
            f.write('  "rate_limit_calls_per_second": 10.0,\n')
            
            if include_caching:
                f.write('  \n')
                f.write('  // Caching options for improved performance\n')
                f.write('  "cache_methods": true,\n')
                f.write('  "cache_ttl_hours": 24,\n')
                f.write('  "cache_dir": "~/.easy_acumatica_cache",  // Optional\n')
                f.write('  "force_rebuild": false\n')
            
            f.write('}\n')
    else:
        # Regular JSON without comments
        with open(path, 'w') as f:
            json.dump(config_data, f, indent=2)
    
    print(f"Sample configuration created at: {path}")
    print("Remember to update with your actual credentials!")
    if not include_caching:
        print("Add 'cache_methods': true for better performance.")


def create_sample_env_file(path: Path, include_caching: bool = True) -> None:
    """
    Create a sample .env file with all available options.
    
    Args:
        path: Path where to save the .env file
        include_caching: Whether to include caching options
    """
    # Ensure directory exists
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        f.write('# Easy-Acumatica Configuration\n')
        f.write('# Copy this file to .env and update with your credentials\n\n')
        
        f.write('# Required: Acumatica connection settings\n')
        f.write('ACUMATICA_URL=https://your-instance.acumatica.com\n')
        f.write('ACUMATICA_USERNAME=your-username\n')
        f.write('ACUMATICA_PASSWORD=your-password\n')
        f.write('ACUMATICA_TENANT=your-company\n\n')
        
        f.write('# Optional: Additional connection settings\n')
        f.write('# ACUMATICA_BRANCH=MAIN\n')
        f.write('# ACUMATICA_LOCALE=en-US\n')
        f.write('# ACUMATICA_ENDPOINT_NAME=Default\n')
        f.write('# ACUMATICA_ENDPOINT_VERSION=24.200.001\n\n')
        
        if include_caching:
            f.write('# Performance: Caching options (recommended for production)\n')
            f.write('ACUMATICA_CACHE_METHODS=true\n')
            f.write('ACUMATICA_CACHE_TTL_HOURS=24\n')
            f.write('# ACUMATICA_CACHE_DIR=/custom/cache/path\n')
            f.write('# ACUMATICA_FORCE_REBUILD=false\n\n')
        
        f.write('# Advanced: Connection tuning\n')
        f.write('# ACUMATICA_TIMEOUT=60\n')
        f.write('# ACUMATICA_RATE_LIMIT=10.0\n')
        f.write('# ACUMATICA_VERIFY_SSL=true\n')
        f.write('# ACUMATICA_PERSISTENT_LOGIN=true\n')
        f.write('# ACUMATICA_RETRY_ON_IDLE=true\n\n')
        
        f.write('# Development: Logging\n')
        f.write('# ACUMATICA_LOG_LEVEL=INFO\n')
        f.write('# ACUMATICA_LOG_FILE=/path/to/logfile.log\n')
    
    print(f"Sample .env file created at: {path}")
    print("Remember to:")
    print("1. Update with your actual credentials")
    print("2. Add .env to your .gitignore file")
    print("3. Never commit credentials to version control")