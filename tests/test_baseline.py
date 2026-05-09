"""Tests for envdiff.baseline."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.baseline import (
    BaselineEntry,
    BaselineReport,
    compare_to_baseline,
    load_baseline,
    save_baseline,
)


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# save_baseline / load_baseline
# ---------------------------------------------------------------------------


def test_save_creates_json_file(env_dir: Path) -> None:
    dest = env_dir / "baseline.json"
    save_baseline({"KEY": "value", "OTHER": None}, dest)
    assert dest.exists()
    data = json.loads(dest.read_text())
    assert data["KEY"] == "value"
    assert data["OTHER"] is None


def test_save_creates_parent_dirs(env_dir: Path) -> None:
    dest = env_dir / "deep" / "nested" / "baseline.json"
    save_baseline({"A": "1"}, dest)
    assert dest.exists()


def test_round_trip(env_dir: Path) -> None:
    original = {"FOO": "bar", "EMPTY": "", "NONE_VAL": None}
    dest = env_dir / "bl.json"
    save_baseline(original, dest)
    loaded = load_baseline(dest)
    assert loaded == original


# ---------------------------------------------------------------------------
# compare_to_baseline
# ---------------------------------------------------------------------------


def test_compare_identical_is_clean(env_dir: Path) -> None:
    bl = env_dir / "baseline.json"
    save_baseline({"A": "1", "B": "2"}, bl)
    target = _write(env_dir / ".env", "A=1\nB=2\n")

    report = compare_to_baseline(bl, target)

    assert report.is_clean
    assert report.drift_count == 0


def test_compare_detects_drifted_value(env_dir: Path) -> None:
    bl = env_dir / "baseline.json"
    save_baseline({"HOST": "localhost"}, bl)
    target = _write(env_dir / ".env", "HOST=production.example.com\n")

    report = compare_to_baseline(bl, target)

    assert not report.is_clean
    drifted = [e for e in report.entries if e.status == "drifted"]
    assert len(drifted) == 1
    assert drifted[0].key == "HOST"


def test_compare_detects_removed_key(env_dir: Path) -> None:
    bl = env_dir / "baseline.json"
    save_baseline({"A": "1", "B": "2"}, bl)
    target = _write(env_dir / ".env", "A=1\n")

    report = compare_to_baseline(bl, target)

    removed = [e for e in report.entries if e.status == "removed"]
    assert any(e.key == "B" for e in removed)


def test_compare_detects_added_key(env_dir: Path) -> None:
    bl = env_dir / "baseline.json"
    save_baseline({"A": "1"}, bl)
    target = _write(env_dir / ".env", "A=1\nNEW_KEY=hello\n")

    report = compare_to_baseline(bl, target)

    added = [e for e in report.entries if e.status == "added"]
    assert any(e.key == "NEW_KEY" for e in added)


def test_as_dict_structure(env_dir: Path) -> None:
    bl = env_dir / "baseline.json"
    save_baseline({"X": "y"}, bl)
    target = _write(env_dir / ".env", "X=y\n")

    report = compare_to_baseline(bl, target)
    d = report.as_dict()

    assert "baseline" in d
    assert "target" in d
    assert "is_clean" in d
    assert "drift_count" in d
    assert isinstance(d["entries"], list)
