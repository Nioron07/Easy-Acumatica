# Easy-Acumatica Stub Setup Guide

This guide explains how to generate type stubs so VSCode, PyCharm, and mypy
get full IDE autocompletion and type checking for the dynamically-generated
models and services.

## TL;DR

```bash
generate-stubs --url "https://your-instance.acumatica.com" \
               --username "your-username" \
               --password "your-password" \
               --tenant "your-tenant"
```

That's it. Restart your IDE if it doesn't immediately pick up the types.
**No `settings.json`, `mypy.ini`, or `stubPath` config required** — the
stubs are written into the installed `easy_acumatica` package directory
itself, alongside its existing `py.typed` marker. PEP 561 compliant
type checkers find them automatically.

## What gets generated

The generator writes seven `.pyi` files into the package install directory:

```
{site-packages}/easy_acumatica/
├── __init__.pyi      # package re-exports
├── client.pyi        # AcumaticaClient + service attributes (introspected)
├── core.pyi          # BaseService / BaseDataClassModel
├── models.pyi        # one stub per dynamically-generated dataclass
├── services.pyi      # one stub per generated service
├── odata.pyi         # QueryOptions, Filter, F factory
├── batch.pyi         # BatchCall + helpers
└── py.typed          # already shipped — not re-written
```

You can find this directory by running:

```bash
python -c "import easy_acumatica; print(easy_acumatica.__file__)"
```

## How credentials are loaded

In priority order:

1. `--url`, `--username`, `--password`, `--tenant`, `--endpoint-version`,
   `--endpoint-name` command-line flags
2. `ACUMATICA_*` env vars in a `.env` file in your current directory
3. Interactive prompts for anything still missing (passwords use
   `getpass`, not echoed)

```bash
# Loads from .env automatically
generate-stubs

# Or specify on the command line
generate-stubs --url ... --username ... --password ... --tenant ...
```

## When to regenerate

Stubs are tied to a specific Acumatica instance + endpoint version.
Regenerate when:

- You connect to a different Acumatica tenant
- The schema changes server-side (new customization deployed,
  fields added/removed, etc.)
- You bump `easy_acumatica` to a version that adds new client methods

Stubs are **per-installation** — if you have multiple Acumatica instances
with different schemas, you'll need to switch between them by regenerating.
For that case, see "Writing stubs elsewhere" below.

## Writing stubs elsewhere (Lambda, read-only installs, multi-tenant)

Pass `--output-dir` to write to a custom location:

```bash
generate-stubs --output-dir ./my-stubs --url ... --username ... ...
```

In this mode the generator also writes its own `py.typed` marker so the
output directory is self-contained. **You must point your IDE/type
checker at it manually:**

### VSCode (Pylance)

`.vscode/settings.json`:

```json
{
    "python.analysis.stubPath": "./my-stubs"
}
```

For Pylance to pick this up, the directory passed to `stubPath` is
treated as a search root for stub *packages*. The default inline-mode
flow avoids this problem entirely; only worry about it if you have to
use `--output-dir`.

### mypy

`mypy.ini`:

```ini
[mypy]
mypy_path = ./my-stubs
```

### PyCharm

Settings → Project → Python Interpreter, then mark the stubs dir as
"Sources Root."

## Verifying it worked

In any Python file:

```python
from easy_acumatica import AcumaticaClient

client = AcumaticaClient(...)
client.contact.get_list(  # ← IDE should show full signature on hover
    options=...           # ← IDE should suggest QueryOptions
)
```

If hovering on `.get_list` shows a signature with `options: Optional[QueryOptions]`
and a typed return value, you're done.

## Troubleshooting

### No type hints at all

1. Restart the IDE (Pylance caches aggressively).
2. Confirm stubs were written: `ls "$(python -c 'import easy_acumatica, os; print(os.path.dirname(easy_acumatica.__file__))')"/*.pyi`
3. If you see `.pyi` files but still no hints, check the IDE's Python
   extension is using the same interpreter you ran `generate-stubs` against.

### Specific service or model unknown

If `client.foo.get_list()` says "unknown attribute," your stubs are out
of date relative to the live schema. Regenerate.

### Permission denied writing stubs

Your install dir is read-only (e.g. system Python on macOS, locked-down
container). Two options:

- Use a virtualenv: `python -m venv .venv && .venv/bin/pip install easy_acumatica && .venv/bin/generate-stubs ...`
- Or use `--output-dir` and configure your IDE manually (see above).

### Editable installs (`pip install -e .`)

Stubs land in `src/easy_acumatica/`. They're listed in `.gitignore` so
they don't pollute commits. Each developer regenerates against their own
instance.

## Important notes

- Stubs only affect type checking and IDE support — they have zero
  runtime impact.
- The generator runs the full `AcumaticaClient` initialization, so it
  hits your Acumatica instance the same way a real connection would.
  Treat it as a one-time cost.
- Different Acumatica instances may need different stubs — there's no
  universal stub set.

## Resources

- [PEP 561: Distributing Type Information](https://www.python.org/dev/peps/pep-0561/)
- [Pylance documentation](https://github.com/microsoft/pylance-release)
- [mypy stub files](https://mypy.readthedocs.io/en/stable/stubs.html)
