"""Textual TUI for easy_acumatica. Launch with ``ea-debug``."""
from __future__ import annotations


def run() -> int:
    """Launch the TUI app. Returns an exit code."""
    from .app import AcumaticaTUI

    AcumaticaTUI().run()
    return 0


__all__ = ['run']
