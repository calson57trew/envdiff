"""Thin integration shim: registers ``watch`` as a sub-command of the main CLI.

Import and call :func:`register` from ``envdiff/cli.py`` to attach the
``watch`` sub-command without circular imports.
"""

from __future__ import annotations

import argparse
from typing import Optional

from envdiff.cli_watch import build_watch_parser, run_watch


def register(subparsers: argparse._SubParsersAction) -> None:  # noqa: SLF001
    """Attach the *watch* sub-command to an existing subparsers group."""
    build_watch_parser(parent=subparsers)


def dispatch(args: argparse.Namespace) -> Optional[int]:
    """Dispatch to :func:`run_watch` when ``args.command == 'watch'``.

    Returns ``None`` if the command was not ``watch`` (caller should continue
    its own dispatch chain).
    """
    if getattr(args, "command", None) != "watch":
        return None
    run_watch(args)
    return 0
