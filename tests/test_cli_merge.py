"""Tests for envdiff.cli_merge (merge sub-command logic)."""

from __future__ import annotations

import json
from argparse import Namespace
from pathlib import Path

import pytest

from envdiff.cli_merge import _render_env, _render_json, run_merge
from envdiff.merger import MergeConflict, MergeResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


# ---------------------------------------------------------------------------
# Unit tests for render helpers
# ---------------------------------------------------------------------------

def test_render_env_sorted_keys():
    result = MergeResult(merged={"Z": "1", "A": "2"})
    rendered = _render_env(result)
    assert rendered.index("A=") < rendered.index("Z=")


def test_render_env_none_value_becomes_empty():
    result = MergeResult(merged={"KEY": None})
    assert "KEY=\n" in _render_env(result)


def test_render_json_includes_conflicts():
    conflict = MergeConflict(key="HOST", values={"a": "x", "b": "y"})
    result = MergeResult(merged={"HOST": "x"}, conflicts=[conflict])
    data = json.loads(_render_json(result))
    assert len(data["conflicts"]) == 1
    assert data["conflicts"][0]["key"] == "HOST"


# ---------------------------------------------------------------------------
# Integration tests via run_merge
# ---------------------------------------------------------------------------

def test_run_merge_no_conflicts_exits_zero(env_dir):
    f1 = _write(env_dir / "a.env", "HOST=localhost\nPORT=5432\n")
    f2 = _write(env_dir / "b.env", "PORT=5432\nDEBUG=true\n")
    args = Namespace(files=[str(f1), str(f2)], prefer=None, output=None, fmt="env", exit_code=True)
    assert run_merge(args) == 0


def test_run_merge_conflict_exits_one_with_flag(env_dir):
    f1 = _write(env_dir / "a.env", "HOST=localhost\n")
    f2 = _write(env_dir / "b.env", "HOST=remote\n")
    args = Namespace(files=[str(f1), str(f2)], prefer=None, output=None, fmt="env", exit_code=True)
    assert run_merge(args) == 1


def test_run_merge_conflict_exits_zero_without_flag(env_dir):
    f1 = _write(env_dir / "a.env", "HOST=localhost\n")
    f2 = _write(env_dir / "b.env", "HOST=remote\n")
    args = Namespace(files=[str(f1), str(f2)], prefer=None, output=None, fmt="env", exit_code=False)
    assert run_merge(args) == 0


def test_run_merge_writes_output_file(env_dir):
    f1 = _write(env_dir / "a.env", "KEY=val\n")
    out = env_dir / "merged.env"
    args = Namespace(files=[str(f1)], prefer=None, output=str(out), fmt="env", exit_code=False)
    run_merge(args)
    assert out.exists()
    assert "KEY=val" in out.read_text()


def test_run_merge_json_format(env_dir):
    f1 = _write(env_dir / "a.env", "KEY=val\n")
    out = env_dir / "merged.json"
    args = Namespace(files=[str(f1)], prefer=None, output=str(out), fmt="json", exit_code=False)
    run_merge(args)
    data = json.loads(out.read_text())
    assert data["merged"]["KEY"] == "val"
    assert data["conflicts"] == []
