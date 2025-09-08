# Easy-Acumatica

A lightweight, Pythonic wrapper around Acumatica's contract-based REST API with intelligent caching and comprehensive utility methods.  
Handles session management, login/logout, URL building, OData query-string construction, and provides powerful introspection capabilities so you can focus on your business logic.

## 🚀 Key Features

- **Dynamic API Discovery**: Automatically generates data models and service methods from live API schema
- **Intelligent Caching**: Optional caching system dramatically improves startup times for subsequent connections
- **Comprehensive Utilities**: Built-in methods for exploring available models, services, and API capabilities
- **Performance Monitoring**: Track startup times, cache hit rates, and other performance metrics
- **Robust Error Handling**: Comprehensive exception hierarchy with detailed error information
- **Rate Limiting**: Built-in respect for API rate limits with configurable thresholds
- **Connection Pooling**: Efficient HTTP connection management for optimal performance

## Installation

```bash
pip install easy-acumatica
```

Supports Python 3.8+ and depends only on `requests`.

## Quick Start

```python
from easy_acumatica import AcumaticaClient

# Basic connection
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin",
    password="Pa$$w0rd",
    tenant="Company"
)

# Enhanced connection with caching for faster subsequent startups
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin",
    password="Pa$$w0rd",
    tenant="Company",
    cache_methods=True,  # Enable intelligent caching
    cache_ttl_hours=24   # Cache valid for 24 hours
)

# Explore available resources
print(f"Available models: {len(client.list_models())}")
print(f"Available services: {len(client.list_services())}")

# Get help
client.help()  # General help
client.help('models')  # Model-specific help

# Use dynamically generated models and services
contact = client.models.Contact(
    Email="test@example.com",
    DisplayName="Test User"
)
result = client.contacts.put_entity(contact)

client.logout()
```

## 🔧 Enhanced Configuration Options

### Caching System

The caching system stores generated models and services to dramatically improve startup times:

```python
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin", 
    password="password",
    tenant="Company",
    cache_methods=True,           # Enable caching
    cache_ttl_hours=48,          # Cache valid for 48 hours
    cache_dir=Path("./my_cache"), # Custom cache directory
    force_rebuild=False          # Set True to force rebuild ignoring cache
)
```

### Performance Optimization

```python
# High-performance configuration
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin",
    password="password", 
    tenant="Company",
    cache_methods=True,                    # Enable caching
    cache_ttl_hours=48,                   # Longer cache TTL
    rate_limit_calls_per_second=20,       # Higher rate if API supports it
    timeout=30,                           # Shorter timeout for faster failures
    retry_on_idle_logout=True             # Auto-retry on session timeout
)
```

## 🔍 Utility Methods

### Discovery and Introspection

```python
# List all available resources
models = client.list_models()
services = client.list_services()

# Search by pattern
contact_models = client.search_models('contact')
invoice_services = client.search_services('invoice')

# Get detailed information
model_info = client.get_model_info('Contact')
print(f"Contact fields: {list(model_info['fields'].keys())}")

service_info = client.get_service_info('Contact')
print(f"Available methods: {[m['name'] for m in service_info['methods']]}")
```

### Performance Monitoring

```python
# Get performance statistics
stats = client.get_performance_stats()
print(f"Startup time: {stats['startup_time']:.2f}s")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Models loaded: {stats['model_count']}")
print(f"Services loaded: {stats['service_count']}")
```

### Cache Management

```python
# Clear all cached data
client.clear_cache()

# Check cache effectiveness
stats = client.get_performance_stats()
if stats['cache_hit_rate'] < 0.5:
    print("Consider increasing cache TTL or checking for schema changes")
```

## 📚 Built-in Help System

The client includes a comprehensive help system:

```python
client.help()              # General overview and usage
client.help('models')      # Model system help
client.help('services')    # Service system help  
client.help('cache')       # Caching system help
client.help('performance') # Performance optimization tips
```

## 🏗️ Dynamic API Usage

### Working with Models

```python
# List available models
print("Available models:", client.list_models()[:10])  # First 10

# Get model details
contact_info = client.get_model_info('Contact')
print("Contact fields:", list(contact_info['fields'].keys()))

# Create model instances
contact = client.models.Contact(
    Email="user@example.com",
    DisplayName="John Doe"
)

# Models have built-in validation and conversion methods
payload = contact.to_acumatica_payload()
```

### Working with Services

```python
# List available services
print("Available services:", client.list_services()[:10])  # First 10

# Get service details
service_info = client.get_service_info('Contact')
print("Available methods:", [m['name'] for m in service_info['methods']])

# Use services
contacts = client.contacts.get_list()
specific_contact = client.contacts.get_by_id("CONTACT001")
new_contact = client.contacts.put_entity(contact)
```

### Advanced Querying with OData

```python
from easy_acumatica.odata import F, QueryOptions

# Build complex filters
filter_expr = (
    (F.Status == "Active") & 
    (F.Amount > 1000) &
    F.CustomerName.tolower().startswith("acme")
)

options = QueryOptions(
    filter=filter_expr,
    select=["CustomerID", "CustomerName", "Amount"],
    top=50,
    orderby="Amount desc"
)

results = client.customers.get_list(options=options)
```

## 🛠️ Advanced Configuration

### Using Configuration Files

```python
from easy_acumatica.config import AcumaticaConfig

# Load from JSON file
config = AcumaticaConfig.from_file("config.json")
client = AcumaticaClient(config=config, cache_methods=True)

# Load from environment variables
config = AcumaticaConfig.from_env()
client = AcumaticaClient(config=config)
```

### Environment Variables

```bash
export ACUMATICA_URL=https://demo.acumatica.com
export ACUMATICA_USERNAME=admin
export ACUMATICA_PASSWORD=password
export ACUMATICA_TENANT=Company
export ACUMATICA_BRANCH=MAIN
```

```python
# Automatically uses environment variables
client = AcumaticaClient(cache_methods=True)
```

## 🔧 Error Handling

```python
from easy_acumatica.exceptions import (
    AcumaticaAuthError,
    AcumaticaConnectionError, 
    AcumaticaValidationError,
    AcumaticaRateLimitError
)

try:
    client = AcumaticaClient(
        base_url="https://demo.acumatica.com",
        username="admin",
        password="wrong_password",
        tenant="Company"
    )
except AcumaticaAuthError as e:
    print(f"Authentication failed: {e}")
except AcumaticaConnectionError as e:
    print(f"Connection failed: {e}")
```

## 📊 Monitoring and Debugging

### Performance Monitoring

```python
# Track client performance
stats = client.get_performance_stats()

print(f"""
Performance Report:
- Startup time: {stats['startup_time']:.2f}s
- Cache hit rate: {stats['cache_hit_rate']:.1%}  
- Models loaded: {stats['model_count']}
- Services loaded: {stats['service_count']}
- Schema cache size: {stats['schema_cache_size']}
""")
```

### Debugging API Structure

```python
# Explore available resources
print("All models:", client.list_models())
print("All services:", client.list_services())

# Search for specific functionality
customer_related = client.search_models('customer')
invoice_services = client.search_services('invoice')

# Get detailed field information
contact_info = client.get_model_info('Contact')
for field_name, field_info in contact_info['fields'].items():
    required = "required" if field_info['required'] else "optional"
    print(f"  {field_name}: {field_info['type']} ({required})")
```

## 🎯 Best Practices

### 1. Use Caching in Production

```python
# Recommended production setup
client = AcumaticaClient(
    base_url=os.getenv('ACUMATICA_URL'),
    username=os.getenv('ACUMATICA_USERNAME'), 
    password=os.getenv('ACUMATICA_PASSWORD'),
    tenant=os.getenv('ACUMATICA_TENANT'),
    cache_methods=True,        # Enable caching
    cache_ttl_hours=24,       # 24-hour cache
    verify_ssl=True,          # Always verify SSL in production
    timeout=60                # Reasonable timeout
)
```

### 2. Handle Cache Warming

```python
# Warm cache during application startup
def initialize_acumatica():
    client = AcumaticaClient(
        ...,
        cache_methods=True,
        force_rebuild=False  # Use cache if valid
    )
    
    # Verify cache effectiveness
    stats = client.get_performance_stats()
    logger.info(f"Acumatica initialized in {stats['startup_time']:.2f}s "
               f"(cache hit rate: {stats['cache_hit_rate']:.1%})")
    
    return client
```

### 3. Monitor Performance

```python
# Regular performance monitoring
def monitor_client_performance(client):
    stats = client.get_performance_stats()
    
    # Alert on slow startup
    if stats['startup_time'] > 10:
        logger.warning(f"Slow Acumatica startup: {stats['startup_time']:.2f}s")
    
    # Alert on low cache hit rate
    if stats['cache_hit_rate'] < 0.8:
        logger.warning(f"Low cache hit rate: {stats['cache_hit_rate']:.1%}")
        
    return stats
```

### 4. Error Handling

```python
from easy_acumatica.exceptions import AcumaticaError
import time

def robust_client_initialization(max_retries=3):
    for attempt in range(max_retries):
        try:
            client = AcumaticaClient(
                base_url=os.getenv('ACUMATICA_URL'),
                username=os.getenv('ACUMATICA_USERNAME'),
                password=os.getenv('ACUMATICA_PASSWORD'),
                tenant=os.getenv('ACUMATICA_TENANT'),
                cache_methods=True
            )
            return client
        except AcumaticaError as e:
            if attempt == max_retries - 1:
                raise
            logger.warning(f"Client initialization failed (attempt {attempt + 1}): {e}")
            time.sleep(2 ** attempt)  # Exponential backoff
```

## 📖 Documentation

Full usage examples and API reference can be found on our docs website:  
https://easyacumatica.com/python

Or on our Github Wiki:
https://github.com/Nioron07/Easy-Acumatica/wiki

## 📦 Package Links

**PyPI**: https://pypi.org/project/easy-acumatica/

**NPM Version**: Not using Python? See the NPM version by joeBewon [here](https://easyacumatica.com/npm)

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines and feel free to submit pull requests or open issues.

## 📄 License

MIT-licensed (see [LICENSE](LICENSE) for details)

## 🔧 Generate Stubs for Development

For enhanced IDE support with type hints:

```bash
easy-acumatica-stubs --url "*base url*" --username "*username*" --password "*password*" --tenant "*Tenant*" --endpoint-version "*api version*"
```

## 🆘 Troubleshooting

### Slow Startup Times

1. Enable caching: `cache_methods=True`
2. Increase cache TTL: `cache_ttl_hours=48`
3. Monitor cache hit rate: `client.get_performance_stats()`

### Memory Usage

1. Clear caches when needed: `client.clear_cache()`
2. Use context managers for temporary clients
3. Monitor schema cache size in performance stats

### API Connection Issues

1. Verify credentials and URL
2. Check network connectivity
3. Verify SSL certificates
4. Review rate limiting settings

For more help, check the built-in help system:
```python
client.help('performance')  # Performance optimization tips
```
