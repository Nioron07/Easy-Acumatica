# Easy-Acumatica

**Easy-Acumatica** is a lightweight, Pythonic wrapper around Acumatica’s
**contract-based REST API**.  
It hides the boilerplate—session management, login/logout, URL building,
OData query-string fiddling—so you can focus on business logic:

```python
from easy_acumatica import AcumaticaClient, Filter, QueryOptions

client = AcumaticaClient(...credentials...)

flt = Filter().eq("ContactID", 102210).and_(
    Filter().contains("DisplayName", "Brian")
)

opts = QueryOptions(filter=flt, select=["ContactID", "DisplayName"])
contacts = client.contacts.get_contacts("24.200.001", options=opts)
```

---

## 1  Client setup

```python
from easy_acumatica import AcumaticaClient

client = AcumaticaClient(
    base_url="https://demo.acumatica.com",
    username="admin",
    password="Pa$$w0rd",
    tenant="Company",
    branch="HQ",
    locale="en-US",      # optional
    verify_ssl=True      # default
)

# …do your work…

client.logout()  # optional – runs automatically on interpreter exit
```

* The client opens a persistent `requests.Session`.
* It logs in **immediately**; failed credentials raise an exception.
* A single `logout()` is registered with `atexit`, so forgotten clean-ups
  don’t leak server sessions.

---

## 2  Filters & query parameters

Build OData-v3 `$filter`, `$expand`, `$select`, `$top`, `$skip`
fragments without manual string concatenation.

```python
from easy_acumatica.filters import Filter, QueryOptions

flt = (
    Filter()
    .eq("Status", "Active")
    .and_(Filter().gt("CreatedDateTime", "2025-01-01"))
)

opts = QueryOptions(
    filter=flt,
    expand=["Address"],
    select=["ContactID", "DisplayName", "Email"],
    top=25,
    skip=0,
)

params = opts.to_params()
# {'$filter': "Status eq 'Active' and CreatedDateTime gt '2025-01-01'",
#  '$expand': 'Address',
#  '$select': 'ContactID,DisplayName,Email',
#  '$top': '25',
#  '$skip': '0'}
```

### Common predicates

| Method                         | Output example                                   |
|--------------------------------|--------------------------------------------------|
| `eq("Field", 5)`               | `Field eq 5`                                     |
| `gt("Field", 3)`               | `Field gt 3`                                     |
| `lt("Field", 9)`               | `Field lt 9`                                     |
| `contains("Name","Bob")`       | `substringof('Bob',Name)`                        |
| Chain with `.and_(…)` / `.or_(…)` for complex logic |

---
## 3 Sub-Services
Each Acumatica resource lives under a *service* object created by the
client. Each of these contains different endpoints related to that sub-service



## 3.1  Contacts sub-service

The Contacts sub-service provides access to all contacts in your Acumatica account. It also supports filtering and query parameters

### Available endpoint methods

| Method                                 | Description                                  |
|----------------------------------------|----------------------------------------------|
| `get_contacts(api_version, options)`   | Returns a list of contacts. `api_version` is the semantic version string (e.g. `"24.200.001"`). |

### Usage examples

```python
# 3.1 Get a single contact by ID
contact = client.contacts.get_contacts(
    "24.200.001",
    options=QueryOptions(filter=Filter().eq("ContactID", 100073))
)[0]

# 3.2 Paginate active contacts, 50 per page
active_filter = Filter().eq("Status", "Active")
page1 = client.contacts.get_contacts(
    "24.200.001",
    options=QueryOptions(filter=active_filter, top=50, skip=0)
)
page2 = client.contacts.get_contacts(
    "24.200.001",
    options=QueryOptions(filter=active_filter, top=50, skip=50)
)
```

---

## 4  Installation

```bash
pip install easy_acumatica
```

Supports Python 3.8+ and ships zero third‑party deps beyond `requests`.

---

## 5  License

MIT
