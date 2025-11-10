# Easy-Acumatica Stub Setup Guide

This guide explains how to generate and use type stubs for easy-acumatica to enable IDE autocompletion and type checking.

## Quick Start

Generate type stubs by running the stub generator:

```bash
python -m easy_acumatica.generate_stubs
```

The generator will prompt you for connection details or you can provide them as arguments.

## What Are Stubs?

Type stubs (.pyi files) provide type information for dynamically generated code. Since easy-acumatica creates models and services from your Acumatica schema at runtime, stubs help IDEs understand the structure of your code.

## Generating Stubs

### Method 1: Interactive

Run the generator and provide credentials when prompted:

```bash
python -m easy_acumatica.generate_stubs
```

### Method 2: Command Line Arguments

```bash
python -m easy_acumatica.generate_stubs \
    --url "https://your-instance.acumatica.com" \
    --username "your-username" \
    --password "your-password" \
    --tenant "your-tenant" \
    --output-dir "./my-stubs"
```

### Method 3: Environment Variables

Create a .env file with your credentials:

```env
ACUMATICA_URL=https://your-instance.acumatica.com
ACUMATICA_USERNAME=your-username
ACUMATICA_PASSWORD=your-password
ACUMATICA_TENANT=your-tenant
ACUMATICA_ENDPOINT_VERSION=24.200.001
```

Then run:

```bash
python -m easy_acumatica.generate_stubs
```

## Generated Structure

The generator creates a `stubs/` directory with the following files:

```
stubs/
├── __init__.pyi        # Package exports
├── batch.pyi           # Batch operations
├── client.pyi          # Main client class
├── core.pyi            # Base classes
├── models.pyi          # Your Acumatica models
├── odata.pyi           # Query builder
├── services.pyi        # Your Acumatica services
└── py.typed            # PEP 561 marker
```

## Using the Stubs

### VSCode Setup

1. Generate stubs in your project directory
2. VSCode's Pylance will automatically detect them
3. Optional: Add to settings.json:

```json
{
    "python.analysis.typeCheckingMode": "basic",
    "python.analysis.stubPath": "./stubs"
}
```

### PyCharm Setup

1. Generate stubs in your project directory
2. Go to Settings > Project > Python Interpreter
3. PyCharm should automatically detect the stubs
4. If not, mark the stubs directory as "Sources Root"

### Mypy Setup

Create or update mypy.ini:

```ini
[mypy]
mypy_path = ./stubs
```

Then run:

```bash
python -m mypy your_code.py
```

## Verification

Test that stubs are working:

```python
from easy_acumatica import AcumaticaClient

# You should see type hints and autocompletion
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin",
    password="password",
    tenant="Company"
)

# These should show type hints in your IDE
customer = client.models.Customer(CustomerID="TEST001")
result = client.customer.put_entity(customer)
```

## Troubleshooting

### No Type Hints in VSCode

1. Restart VSCode after generating stubs
2. Check that Python extension and Pylance are installed
3. Verify stub location matches your configuration
4. Check VSCode Output > Python for errors

### Mypy Errors

Ensure mypy_path in mypy.ini points to the correct stubs directory:

```bash
python -m mypy --config-file mypy.ini your_code.py
```

### PyCharm Not Recognizing Stubs

1. File > Invalidate Caches and Restart
2. Verify stubs directory is marked as Sources Root
3. Check Python interpreter is correctly set

## Advanced Options

### Custom Output Directory

```bash
python -m easy_acumatica.generate_stubs --output-dir "./custom-location"
```

### Specific Endpoint Version

```bash
python -m easy_acumatica.generate_stubs \
    --endpoint-version "23.200.001" \
    --endpoint-name "Custom"
```

## Important Notes

- Stubs must be regenerated when your Acumatica schema changes
- Stubs are only for type checking and IDE support
- They do not affect runtime behavior
- Different Acumatica instances may require different stubs

## Additional Resources

- [PEP 561: Distributing Type Information](https://www.python.org/dev/peps/pep-0561/)
- [MyPy Stub Files Documentation](https://mypy.readthedocs.io/en/stable/stubs.html)
- [Pylance Documentation](https://github.com/microsoft/pylance-release)

---

Need help? Open an issue on [GitHub](https://github.com/Nioron07/Easy-Acumatica/issues) with:
- Python version
- IDE and version
- Output from stub generation
- Any error messages
