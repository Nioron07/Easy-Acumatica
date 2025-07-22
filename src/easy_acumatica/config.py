"""easy_acumatica.config
=====================

Configuration management for Easy Acumatica.

Provides flexible configuration options through:
- Direct parameters
- Environment variables
- Configuration files (JSON/YAML)
- Secure credential storage integration
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class AcumaticaConfig:
    """
    Configuration for Acumatica client.
    
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
    
    # Additional options
    log_level: str = "INFO"
    log_file: Optional[str] = None
    cache_schemas: bool = True
    
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
            return type_fn(value)
        
        # Check for required fields
        required = ['URL', 'USERNAME', 'PASSWORD', 'TENANT']
        missing = [f"{prefix}{r}" for r in required if not os.getenv(f"{prefix}{r}")]
        if missing:
            raise KeyError(f"Missing required environment variables: {', '.join(missing)}")
        
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
            log_level=get_env("LOG_LEVEL", "INFO"),
            log_file=get_env("LOG_FILE"),
            cache_schemas=get_env("CACHE_SCHEMAS", True, bool),
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
            raise FileNotFoundError(f"Configuration file not found: {path}")
        
        # Auto-detect format from extension
        if file_format is None:
            file_format = path.suffix.lower().lstrip('.')
        
        with open(path, 'r') as f:
            if file_format == 'json':
                data = json.load(f)
            elif file_format in ('yaml', 'yml'):
                if not HAS_YAML:
                    raise ValueError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
                data = yaml.safe_load(f)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
        
        # Handle potential key variations
        normalized_data = {}
        for key, value in data.items():
            # Convert from various naming conventions
            normalized_key = key.lower().replace('-', '_')
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
        data = {k: v for k, v in self.__dict__.items() if v is not None}
        
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
                    raise ValueError("PyYAML is required for YAML config files. Install with: pip install pyyaml")
                yaml.dump(data, f, default_flow_style=False)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AcumaticaConfig":
        """
        Create configuration from a dictionary.
        
        Args:
            data: Configuration dictionary
            
        Returns:
            AcumaticaConfig instance
        """
        # Filter out any extra keys
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)
    
    def to_dict(self, include_password: bool = False) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Args:
            include_password: Whether to include password
            
        Returns:
            Configuration dictionary
        """
        data = {k: v for k, v in self.__dict__.items() if v is not None}
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
            raise ValueError("base_url is required")
        if not self.username:
            raise ValueError("username is required")
        if not self.password:
            raise ValueError("password is required")
        if not self.tenant:
            raise ValueError("tenant is required")
        
        # Validate URL format
        if not self.base_url.startswith(('http://', 'https://')):
            raise ValueError("base_url must start with http:// or https://")
        
        # Validate numeric ranges
        if self.timeout <= 0:
            raise ValueError("timeout must be positive")
        if self.max_retries < 0:
            raise ValueError("max_retries cannot be negative")
        if self.rate_limit_calls_per_second <= 0:
            raise ValueError("rate_limit_calls_per_second must be positive")
        
        # Validate log level
        valid_log_levels = {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}
        if self.log_level.upper() not in valid_log_levels:
            raise ValueError(f"log_level must be one of: {', '.join(valid_log_levels)}")
    
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
    use_env_override: bool = True
) -> AcumaticaConfig:
    """
    Load configuration with fallback hierarchy.
    
    Priority order:
    1. Environment variables (if use_env_override=True)
    2. Config file (if provided)
    3. Environment variables (if no config file)
    
    Args:
        config_path: Optional path to config file
        env_prefix: Environment variable prefix
        use_env_override: Allow env vars to override config file
        
    Returns:
        AcumaticaConfig instance
        
    Example:
        >>> # Load from file with env overrides
        >>> config = load_config(Path("config.json"))
        >>> 
        >>> # Load from environment only
        >>> config = load_config()
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
            env_dict = env_config.to_dict(include_password=True)
            config_dict = config.to_dict(include_password=True)
            config_dict.update({k: v for k, v in env_dict.items() if v is not None})
            config = AcumaticaConfig.from_dict(config_dict)
    except KeyError:
        if config is None:
            raise
    
    if config is None:
        raise ValueError("No configuration source available")
    
    # Validate before returning
    config.validate()
    return config