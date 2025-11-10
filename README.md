# Easy-Acumatica

A comprehensive Python client for Acumatica's REST API that simplifies integration with intelligent caching, batch operations, and automatic code generation.

## Related Projects

- **[AcuNexus](https://github.com/Nioron07/AcuNexus)** - Desktop application for exploring, managing, and deploying Acumatica clients and endpoints with a user-friendly GUI
- **[easy-acumatica-npm](https://www.npmjs.com/package/easy-acumatica)** - TypeScript/JavaScript sister package for Node.js environments

## Features

### Core Capabilities
- **Dynamic API Discovery** - Automatically generates Python models and service methods from Acumatica's API schema
- **Intelligent Caching** - Built-in caching system that dramatically reduces startup time after initial connection
- **Batch Operations** - Execute multiple API calls concurrently with automatic session management
- **Task Scheduling** - Built-in scheduler for recurring operations with cron-style scheduling
- **OData Query Builder** - Pythonic interface for building complex OData queries
- **Comprehensive Error Handling** - Detailed exception hierarchy with automatic retry logic
- **Performance Monitoring** - Track API usage, response times, and cache effectiveness

### Additional Features
- Automatic session management with login/logout handling
- Rate limiting to respect API constraints
- Connection pooling for optimal performance
- Support for custom API endpoints and inquiries
- Built-in introspection utilities for exploring available resources
- Type hints and IDE support through stub generation

## Installation

```bash
pip install easy-acumatica
```

Requirements:
- Python 3.8 or higher
- Dependencies: requests, aiohttp, croniter

## Quick Start

### Basic Usage

```python
from easy_acumatica import AcumaticaClient

# Initialize client
client = AcumaticaClient(
    base_url="https://your-instance.acumatica.com",
    username="your_username",
    password="your_password",
    tenant="YourTenant"
)

# Access dynamically generated models
contact = client.models.Contact(
    Email="john.doe@example.com",
    DisplayName="John Doe",
    FirstName="John",
    LastName="Doe"
)

# Use service methods to interact with API
result = client.contacts.put_entity(contact)
print(f"Created contact: {result}")

# Query existing data
all_contacts = client.contacts.get_list()

# Don't forget to logout
client.logout()
```

### Using Caching for Better Performance

```python
# Enable caching to speed up subsequent connections
client = AcumaticaClient(
    base_url="https://your-instance.acumatica.com",
    username="your_username",
    password="your_password",
    tenant="YourTenant",
    cache_methods=True,      # Enable caching
    cache_ttl_hours=24      # Cache valid for 24 hours
)

# First connection will build cache, subsequent connections will be much faster
```

### Batch Operations

```python
# Execute multiple operations concurrently
batch_results = client.batch_call([
    client.contacts.get_by_id.prepare("CONTACT001"),
    client.customers.get_by_id.prepare("CUSTOMER001"),
    client.vendors.get_list.prepare()
], max_workers=5)

for result in batch_results:
    if result.success:
        print(f"Success: {result.result}")
    else:
        print(f"Error: {result.error}")
```

### OData Queries

```python
from easy_acumatica.odata import F, QueryOptions

# Build complex filters
filter_expr = (
    (F.Status == "Active") &
    (F.OrderTotal > 1000) &
    F.CustomerName.contains("Corp")
)

options = QueryOptions(
    filter=filter_expr,
    select=["OrderNbr", "CustomerName", "OrderTotal"],
    orderby="OrderTotal desc",
    top=10
)

results = client.salesorders.get_list(options=options)
```

### Task Scheduling

```python
# Schedule recurring tasks
scheduler = client.scheduler

# Add a task that runs every hour
task = scheduler.add_task(
    name="Sync Contacts",
    callable_obj=lambda: client.contacts.get_list(),
    schedule=scheduler.IntervalSchedule(hours=1)
)

# Start the scheduler
scheduler.start()

# Schedule with cron expression
from easy_acumatica.scheduler import CronSchedule

task = scheduler.add_task(
    name="Daily Report",
    callable_obj=generate_daily_report,
    schedule=CronSchedule("0 9 * * MON-FRI")  # 9 AM on weekdays
)
```

## Configuration

### Environment Variables

Easy-Acumatica supports configuration through environment variables:

```bash
export ACUMATICA_URL=https://your-instance.acumatica.com
export ACUMATICA_USERNAME=your_username
export ACUMATICA_PASSWORD=your_password
export ACUMATICA_TENANT=YourTenant
export ACUMATICA_BRANCH=YourBranch
```

```python
# Client will automatically use environment variables
client = AcumaticaClient()
```

### Configuration Files

```python
from easy_acumatica.config import AcumaticaConfig

# Load from JSON file
config = AcumaticaConfig.from_file("config.json")
client = AcumaticaClient(config=config)
```

## Advanced Usage

### Performance Monitoring

```python
# Get client statistics
stats = client.get_performance_stats()
print(f"Startup time: {stats['startup_time']:.2f}s")
print(f"Cache hit rate: {stats['cache_hit_rate']:.1%}")
print(f"Total API calls: {stats['total_api_calls']}")
print(f"Average response time: {stats['avg_response_time']:.3f}s")
```

### Error Handling

```python
from easy_acumatica.exceptions import (
    AcumaticaAuthError,
    AcumaticaRateLimitError,
    AcumaticaValidationError
)

try:
    result = client.contacts.put_entity(contact)
except AcumaticaAuthError:
    # Handle authentication issues
    client.reconnect()
except AcumaticaRateLimitError as e:
    # Handle rate limiting
    time.sleep(e.retry_after)
except AcumaticaValidationError as e:
    # Handle validation errors
    print(f"Validation failed: {e.details}")
```

### Introspection Utilities

```python
# Discover available resources
models = client.list_models()
services = client.list_services()

# Search for specific resources
contact_models = client.search_models("contact")
invoice_services = client.search_services("invoice")

# Get detailed information
model_info = client.get_model_info("Contact")
print(f"Contact fields: {model_info['fields'].keys()}")

service_info = client.get_service_info("Contact")
print(f"Available methods: {[m['name'] for m in service_info['methods']]}")

# Built-in help system
client.help()                # General help
client.help('models')        # Model system help
client.help('services')      # Service system help
client.help('performance')   # Performance tips
```

## Generating Type Stubs

For enhanced IDE support with type hints:

```bash
generate-stubs --url "https://your-instance.acumatica.com" \
                     --username "username" \
                     --password "password" \
                     --tenant "Tenant" \
                     --endpoint-version "24.109.0029"
```

This generates Python stub files that provide full type hints for all dynamically generated models and services.

## Documentation

Full documentation is available at: **https://easyacumatica.com/python**

## Performance Best Practices

1. **Always enable caching in production** - Reduces startup time from seconds to milliseconds
2. **Use batch operations for multiple calls** - Executes calls concurrently for better performance
3. **Implement proper error handling** - Automatic retry logic handles transient failures
4. **Monitor performance metrics** - Track cache effectiveness and API usage
5. **Use connection pooling** - Reuse HTTP connections for better throughput

## Troubleshooting

### Slow Initial Connection
- Enable caching with `cache_methods=True`
- Increase cache TTL with `cache_ttl_hours=48`
- Use `force_rebuild=False` to use existing cache

### Authentication Issues
- Verify credentials and tenant information
- Check if API access is enabled for your user
- Ensure correct endpoint version is specified

### Rate Limiting
- Adjust `rate_limit_calls_per_second` parameter
- Implement exponential backoff for retries
- Use batch operations to reduce API call count

## License

MIT License - see [LICENSE](LICENSE) file for details.

## Support

- **Issues**: [GitHub Issues](https://github.com/Nioron07/Easy-Acumatica/issues)
- **Documentation**: https://easyacumatica.com/python
