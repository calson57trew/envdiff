"""Watch .env files for changes and report diffs on modification."""

from __future__ import annotations

import time
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, Optional

from envdiff.parser import parse_env_file
from envdiff.differ import diff_envs, DiffResult


@dataclass
class WatchState:
    """Tracks last-seen mtime and parsed contents for a watched file."""
    path: Path
    mtime: float
    env: Dict[str, Optional[str]]


def _current_mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except FileNotFoundError:
        return -1.0


def _load_state(path: Path) -> WatchState:
    env = parse_env_file(str(path)) if path.exists() else {}
    return WatchState(path=path, mtime=_current_mtime(path), env=env)


def watch(
    base_path: str,
    compare_path: str,
    callback: Callable[[DiffResult], None],
    interval: float = 1.0,
    max_cycles: Optional[int] = None,
    check_values: bool = True,
) -> None:
    """Poll *base_path* and *compare_path* and invoke *callback* on change.

    Parameters
    ----------
    base_path:     Path to the base .env file.
    compare_path:  Path to the comparison .env file.
    callback:      Called with a fresh :class:`DiffResult` whenever either
                   file changes.
    interval:      Polling interval in seconds (default 1.0).
    max_cycles:    Stop after this many poll cycles (``None`` = run forever).
    check_values:  Passed through to :func:`diff_envs`.
    """
    base = _load_state(Path(base_path))
    compare = _load_state(Path(compare_path))

    cycles = 0
    while max_cycles is None or cycles < max_cycles:
        time.sleep(interval)
        cycles += 1

        base_mtime = _current_mtime(base.path)
        compare_mtime = _current_mtime(compare.path)

        changed = base_mtime != base.mtime or compare_mtime != compare.mtime
        if changed:
            base = _load_state(base.path)
            compare = _load_state(compare.path)
            result = diff_envs(base.env, compare.env, check_values=check_values)
            callback(result)
