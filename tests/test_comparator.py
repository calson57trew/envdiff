"""Tests for envdiff.comparator."""
from pathlib import Path

import pytest

from envdiff.comparator import compare_many, MultiComparison, ComparisonEntry


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(content)
    return p


def test_compare_many_no_targets_returns_empty(env_dir):
    base = _write(env_dir, ".env.base", "KEY=value\n")
    mc = compare_many(base, [])
    assert isinstance(mc, MultiComparison)
    assert mc.entries == []
    assert mc.names() == []


def test_compare_many_identical_files_are_clean(env_dir):
    base = _write(env_dir, ".env.base", "KEY=value\nOTHER=123\n")
    comp = _write(env_dir, ".env.prod", "KEY=value\nOTHER=123\n")
    mc = compare_many(base, [comp])
    assert mc.dirty_names() == []
    assert mc.clean_names() == [".env.prod"]


def test_compare_many_detects_missing_in_compare(env_dir):
    base = _write(env_dir, ".env.base", "KEY=value\nEXTRA=1\n")
    comp = _write(env_dir, ".env.staging", "KEY=value\n")
    mc = compare_many(base, [comp])
    entry = mc.get(".env.staging")
    assert entry is not None
    assert "EXTRA" in entry.result.missing_in_compare


def test_compare_many_detects_missing_in_base(env_dir):
    base = _write(env_dir, ".env.base", "KEY=value\n")
    comp = _write(env_dir, ".env.dev", "KEY=value\nNEW_KEY=hello\n")
    mc = compare_many(base, [comp])
    entry = mc.get(".env.dev")
    assert "NEW_KEY" in entry.result.missing_in_base


def test_compare_many_detects_mismatched_values(env_dir):
    base = _write(env_dir, ".env.base", "KEY=aaa\n")
    comp = _write(env_dir, ".env.prod", "KEY=bbb\n")
    mc = compare_many(base, [comp])
    entry = mc.get(".env.prod")
    assert "KEY" in entry.result.mismatched
    assert entry.result.mismatched["KEY"] == ("aaa", "bbb")


def test_compare_many_no_value_check_ignores_mismatches(env_dir):
    base = _write(env_dir, ".env.base", "KEY=aaa\n")
    comp = _write(env_dir, ".env.prod", "KEY=bbb\n")
    mc = compare_many(base, [comp], check_values=False)
    entry = mc.get(".env.prod")
    assert entry.result.mismatched == {}
    assert mc.clean_names() == [".env.prod"]


def test_compare_many_multiple_targets(env_dir):
    base = _write(env_dir, ".env.base", "A=1\nB=2\n")
    c1 = _write(env_dir, ".env.c1", "A=1\nB=2\n")
    c2 = _write(env_dir, ".env.c2", "A=1\n")
    mc = compare_many(base, [c1, c2])
    assert set(mc.names()) == {".env.c1", ".env.c2"}
    assert mc.clean_names() == [".env.c1"]
    assert mc.dirty_names() == [".env.c2"]


def test_as_dict_structure(env_dir):
    base = _write(env_dir, ".env.base", "X=1\n")
    comp = _write(env_dir, ".env.prod", "X=2\n")
    mc = compare_many(base, [comp])
    d = mc.as_dict()
    assert d["base"] == ".env.base"
    assert len(d["comparisons"]) == 1
    assert d["comparisons"][0]["name"] == ".env.prod"
    assert "mismatched" in d["comparisons"][0]
