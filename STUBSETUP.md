# Easy-Acumatica Stub Setup Guide

This guide will help you generate and use type stubs for easy-acumatica that work properly with VSCode, mypy, PyCharm, and other type checkers across different Python environments.

## 🎯 Quick Start (Recommended)

The easiest and most compatible approach is to generate **inline stubs** (PEP 561 compliant):

```bash
# Generate stubs directly in the package
easy-acumatica-stubs --url "your-url" --username "user" --password "pass" --tenant "tenant" --mode inline
```

This places `.pyi` files alongside the Python files and creates a `py.typed` marker, making them automatically discoverable by all type checkers.

## 📋 What the Problem Was

The original stub generation had several issues:

1. **Wrong Location**: Stubs were in a nested `/stubs` subdirectory
2. **No PEP 561 Compliance**: Missing `py.typed` marker file
3. **Import Issues**: Incorrect relative imports in stubs
4. **Discovery Problems**: Type checkers couldn't find the stubs

## ✅ The Solution: Three Approaches

### 1. Inline Stubs (Recommended) 

**Best for**: Most users, production code, automatic discovery

```bash
easy-acumatica-stubs --mode inline
```

**What it does**:
- Creates `.pyi` files next to `.py` files in the package
- Adds `py.typed` marker for PEP 561 compliance  
- Works automatically with VSCode, mypy, PyCharm
- No additional configuration needed

**File structure**:
```
site-packages/easy_acumatica/
├── __init__.py
├── client.py
├── client.pyi          # ← Generated stub
├── models.py
├── models.pyi          # ← Generated stub  
├── py.typed            # ← PEP 561 marker
└── ...
```

### 2. External Stub Package

**Best for**: Distributing stubs separately, contributing to typeshed

```bash
easy-acumatica-stubs --mode external --output-dir ./stubs
cd stubs
pip install -e .
```

**What it does**:
- Creates `easy_acumatica-stubs` package
- Can be installed separately from main package
- Follows typeshed conventions

### 3. Both (For Development)

```bash
easy-acumatica-stubs --mode both
```

Generates both inline and external stubs for testing and comparison.

## 🔧 Installation & Setup

### Step 1: Update Package (For Maintainers)

If you're maintaining the package, update `pyproject.toml`:

```toml
[project]
classifiers = [
  # ... existing classifiers ...
  "Typing :: Typed",  # ← Add this
]

[project.scripts]
easy-acumatica-stubs = "easy_acumatica.generate_stubs:main"

[tool.setuptools.package-data]
easy_acumatica = ["py.typed", "*.pyi"]  # ← Include stubs in package
```

### Step 2: Generate Stubs

Choose your preferred method:

#### Method A: Interactive Generation
```bash
easy-acumatica-stubs
# Will prompt for URL, username, password, tenant
```

#### Method B: Command Line Arguments
```bash
easy-acumatica-stubs \
    --url "https://demo.acumatica.com" \
    --username "admin" \
    --password "password" \
    --tenant "Company" \
    --mode inline
```

#### Method C: Environment Variables
Create `.env` file:
```env
ACUMATICA_URL=https://your-instance.acumatica.com
ACUMATICA_USERNAME=your-username
ACUMATICA_PASSWORD=your-password
ACUMATICA_TENANT=your-tenant
ACUMATICA_ENDPOINT_VERSION=24.200.001
```

Then run:
```bash
easy-acumatica-stubs --mode inline
```

### Step 3: Verify Setup

Test that stubs are working:

```python
from easy_acumatica import AcumaticaClient

# You should see full type hints and autocompletion
client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin", 
    password="password",
    tenant="Company"
)

# These should show type hints:
customer = client.models.Customer(CustomerID="TEST001")
result = client.customers.put_entity(customer)
```

## 🛠️ Troubleshooting

### VSCode Not Showing Type Hints

1. **Ensure Pylance is active**:
   - Open Command Palette (`Ctrl+Shift+P`)
   - Type "Python: Select Interpreter"
   - Choose the environment where easy-acumatica is installed

2. **Check language server**:
   ```json
   // .vscode/settings.json
   {
       "python.languageServer": "Pylance",
       "python.analysis.typeCheckingMode": "basic"
   }
   ```

3. **Restart VSCode** after generating stubs

4. **Verify package location**:
   ```bash
   python -c "import easy_acumatica; print(easy_acumatica.__file__)"
   ```

### MyPy Not Finding Stubs

1. **Check installation**:
   ```bash
   python -m mypy --version
   pip show easy-acumatica
   ```

2. **Verify PEP 561 compliance**:
   ```bash
   python -c "
   import easy_acumatica
   from pathlib import Path
   pkg_dir = Path(easy_acumatica.__file__).parent
   print('py.typed exists:', (pkg_dir / 'py.typed').exists())
   print('client.pyi exists:', (pkg_dir / 'client.pyi').exists())
   "
   ```

3. **Test mypy directly**:
   ```bash
   python -m mypy your_code.py
   ```

### PyCharm Issues

1. **Clear caches**: File → Invalidate Caches and Restart
2. **Check interpreter**: Settings → Project → Python Interpreter
3. **Verify stub recognition**: Should see ".pyi" files in project view

## 🌍 Environment-Specific Notes

### Virtual Environments
```bash
# Activate your venv first
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Then generate stubs
easy-acumatica-stubs --mode inline
```

### Conda Environments
```bash
conda activate your-env
easy-acumatica-stubs --mode inline
```

### Global Installation
```bash
# Install globally
pip install easy-acumatica

# Generate stubs globally  
easy-acumatica-stubs --mode inline
```

### Docker/CI Environments

For automated environments, use environment variables:

```dockerfile
FROM python:3.11

# Install package
RUN pip install easy-acumatica

# Set environment variables
ENV ACUMATICA_URL=https://demo.acumatica.com
ENV ACUMATICA_USERNAME=admin
ENV ACUMATICA_PASSWORD=password
ENV ACUMATICA_TENANT=Company

# Generate stubs during build
RUN easy-acumatica-stubs --mode inline
```

## 📝 Advanced Configuration

### Custom Endpoint Versions
```bash
easy-acumatica-stubs \
    --endpoint-version "23.200.001" \
    --endpoint-name "Custom" \
    --mode inline
```

### Multiple Environments
Generate different stubs for different Acumatica versions:

```bash
# Development environment
ACUMATICA_URL=https://dev.acumatica.com easy-acumatica-stubs --mode external --output-dir ./dev-stubs

# Production environment  
ACUMATICA_URL=https://prod.acumatica.com easy-acumatica-stubs --mode external --output-dir ./prod-stubs
```

## 🧪 Verification Commands

Run these to verify your setup:

```python
# test_stubs.py
from easy_acumatica import AcumaticaClient
from easy_acumatica.odata import F, QueryOptions

def test_type_hints():
    # These should all show proper type hints
    client = AcumaticaClient(
        base_url="https://demo.acumatica.com",
        username="admin",
        password="password", 
        tenant="Company"
    )
    
    # Model creation with hints
    contact = client.models.Contact(
        ContactID="TEST001",
        Email="test@example.com"
    )
    
    # Service method with hints
    result = client.contacts.put_entity(contact)
    
    # OData filtering with hints
    filter_query = (F.Status == "Active") & (F.Amount > 1000)
    options = QueryOptions(filter=filter_query, top=10)
    
    contacts = client.contacts.get_list(options=options)
    
    print("✅ All type hints working correctly!")

if __name__ == "__main__":
    test_type_hints()
```

Run with mypy to verify:
```bash
python -m mypy test_stubs.py --strict
```

## 🎉 Success Indicators

You'll know it's working when:

✅ **VSCode**: Full autocompletion and type hints in editor  
✅ **MyPy**: No import errors, proper type checking  
✅ **PyCharm**: Recognizes all methods and attributes  
✅ **Runtime**: Code still works normally (stubs don't affect runtime)

## 🆘 Getting Help

If you're still having issues:

1. **Check Python version**: Stubs require Python 3.8+
2. **Verify package installation**: `pip show easy-acumatica`  
3. **Look for error messages** in VSCode Output → Python
4. **Try clean reinstall**: 
   ```bash
   pip uninstall easy-acumatica
   pip install easy-acumatica
   easy-acumatica-stubs --mode inline
   ```

## 📚 Additional Resources

- [PEP 561: Distributing Type Information](https://www.python.org/dev/peps/pep-0561/)
- [MyPy Stub Files Documentation](https://mypy.readthedocs.io/en/stable/stubs.html)  
- [Pylance Settings Reference](https://github.com/microsoft/pylance-release)
- [Easy-Acumatica Documentation](https://easyacumatica.com/python)

---

**Need more help?** Open an issue on [GitHub](https://github.com/Nioron07/Easy-Acumatica/issues) with:
- Your Python version (`python --version`)  
- Your environment type (venv, conda, global)
- Your IDE (VSCode, PyCharm, etc.)
- Any error messages you're seeing