"""Tests for envdiff.watcher."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List

import pytest

from envdiff.differ import DiffResult
from envdiff.watcher import watch, _load_state, _current_mtime


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_load_state_parses_file(env_dir: Path) -> None:
    p = env_dir / ".env"
    _write(p, "FOO=bar\nBAZ=qux\n")
    state = _load_state(p)
    assert state.env == {"FOO": "bar", "BAZ": "qux"}
    assert state.mtime == p.stat().st_mtime


def test_load_state_missing_file_returns_empty(env_dir: Path) -> None:
    p = env_dir / "missing.env"
    state = _load_state(p)
    assert state.env == {}
    assert state.mtime == -1.0


def test_current_mtime_missing_returns_minus_one(env_dir: Path) -> None:
    assert _current_mtime(env_dir / "nope.env") == -1.0


def test_watch_fires_callback_on_change(env_dir: Path) -> None:
    base = env_dir / "base.env"
    compare = env_dir / "compare.env"
    _write(base, "FOO=bar\n")
    _write(compare, "FOO=bar\n")

    results: List[DiffResult] = []

    def _cb(r: DiffResult) -> None:
        results.append(r)

    # Run one cycle with no changes — no callback expected.
    watch(str(base), str(compare), _cb, interval=0.0, max_cycles=1)
    assert results == []

    # Modify compare file, then run another cycle.
    time.sleep(0.01)          # ensure mtime differs
    _write(compare, "FOO=bar\nEXTRA=1\n")
    watch(str(base), str(compare), _cb, interval=0.0, max_cycles=1)
    assert len(results) == 1
    assert "EXTRA" in results[0].missing_in_base


def test_watch_no_callback_when_unchanged(env_dir: Path) -> None:
    base = env_dir / "base.env"
    compare = env_dir / "compare.env"
    _write(base, "A=1\n")
    _write(compare, "A=1\n")

    calls: List[DiffResult] = []
    watch(str(base), str(compare), calls.append, interval=0.0, max_cycles=3)
    assert calls == []


def test_watch_detects_value_change(env_dir: Path) -> None:
    base = env_dir / "base.env"
    compare = env_dir / "compare.env"
    _write(base, "KEY=original\n")
    _write(compare, "KEY=original\n")

    results: List[DiffResult] = []
    watch(str(base), str(compare), results.append, interval=0.0, max_cycles=1)
    assert results == []

    time.sleep(0.01)
    _write(compare, "KEY=changed\n")
    watch(str(base), str(compare), results.append, interval=0.0, max_cycles=1)
    assert len(results) == 1
    assert "KEY" in results[0].mismatched
