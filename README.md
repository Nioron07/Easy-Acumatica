# Easy-Acumatica

A Python client for Acumatica's REST API. Dynamically generates models and
service methods from your tenant's schema, supports OData queries, batch
operations, caching, and a built-in interactive TUI for exploring the API.

**Full documentation: [easyacumatica.com/python](https://easyacumatica.com/python)**

## Installation

```bash
pip install easy-acumatica           # core
pip install easy-acumatica[tui]      # core + interactive TUI
pip install easy-acumatica[scheduler]  # core + APScheduler
```

## Quick start

```python
from easy_acumatica import AcumaticaClient

client = AcumaticaClient(
    base_url="https://your-instance.acumatica.com",
    username="...",
    password="...",
    tenant="...",
)

contact = client.models.Contact(DisplayName="Jane Doe", Email="jane@example.com")
client.contacts.put_entity(contact)
```

`.env` files and environment variables (`ACUMATICA_URL`, `ACUMATICA_USERNAME`,
`ACUMATICA_PASSWORD`, `ACUMATICA_TENANT`, ...) are picked up automatically when
the constructor is called with no arguments.

## Interactive TUI (`ea-debug`)

Install the `[tui]` extra and launch the terminal UI:

```bash
pip install easy-acumatica[tui]
ea-debug
```

The TUI is a debug / exploration tool — connect to a tenant and browse:

- **Services** — every dynamically generated service. Pick one and run
  `get_list`, `get_by_id`, `get_by_keys`, `get_ad_hoc_schema`, `get_files`,
  `put_entity`, `put_file`, `delete_by_id`, `delete_by_keys`. Query options
  (`$top`, `$skip`, `$select`, `$expand`, `$orderby`, `$filter`) get a form,
  destructive calls require a confirmation press, and a live "Equivalent
  Python" pane shows the call you can copy back into your script.
- **Models** — every generated dataclass. Hit Enter on one to open the
  recursive model builder; the equivalent Python constructor renders next to
  the form as you type.
- **Inquiries** — every Generic Inquiry exposed in the tenant's metadata.
  Each inquiry gets its own execution menu with the same OData query options
  as `get_list`. Inquiries that aren't published to OData (the
  `Expose via OData` flag on `SM208000`) surface a clear error rather than a
  raw 403.

## Type stubs

Run once after install for full IDE autocompletion:

```bash
generate-stubs --url "https://your-instance.acumatica.com" \
               --username "..." --password "..." --tenant "..." \
               --endpoint-version "24.109.0029"
```

PEP 561 `.pyi` files are written into the installed package so
VSCode/Pylance/Pyright/mypy discover them automatically. Regenerate after
schema changes. See [STUBSETUP.md](STUBSETUP.md) for advanced setups
(Lambda, read-only installs, multi-tenant).

## Related projects

- **[Orbu](https://github.com/Nioron07/Orbu)** — Docker app for managing
  Acumatica clients and endpoints with a GUI.
- **[easy-acumatica-npm](https://www.npmjs.com/package/easy-acumatica)** —
  TypeScript / Node.js sister package.

## License

MIT — see [LICENSE](LICENSE).

## Support

- Issues: [GitHub Issues](https://github.com/Nioron07/Easy-Acumatica/issues)
- Documentation: [easyacumatica.com/python](https://easyacumatica.com/python)
