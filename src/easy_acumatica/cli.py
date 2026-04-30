"""Entry point for the ``ea-debug`` command.

Launches the Textual TUI. The TUI lives under
:mod:`easy_acumatica.tui` and requires the optional ``textual`` dependency
(install with ``pip install easy_acumatica[tui]``).
"""
from __future__ import annotations

import sys
from typing import List, Optional


_INSTALL_HINT = (
    "The `ea-debug` CLI requires the 'textual' package. Install the TUI extra:\n"
    "    pip install easy_acumatica[tui]"
)


def main(argv: Optional[List[str]] = None) -> int:
    """Launch the TUI. Returns an exit code."""
    try:
        from easy_acumatica.tui import run
    except ModuleNotFoundError as e:
        # Only swallow the textual-missing case; re-raise anything else.
        if e.name and e.name.split('.')[0] == 'textual':
            print(_INSTALL_HINT, file=sys.stderr)
            return 1
        raise

    return run()


if __name__ == '__main__':
    sys.exit(main())
