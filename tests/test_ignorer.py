"""Tests for envdiff.ignorer."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.differ import DiffResult
from envdiff.ignorer import apply_ignore, is_ignored, load_ignore_list


@pytest.fixture()
def dirty_result() -> DiffResult:
    return DiffResult(
        missing_in_compare={"SECRET_KEY", "DB_HOST"},
        missing_in_base={"NEW_FLAG"},
        mismatched={"API_URL": ("http://old", "http://new"), "LOG_LEVEL": ("DEBUG", "INFO")},
    )


@pytest.fixture()
def ignore_file(tmp_path: Path):
    def _write(name: str, content: str) -> Path:
        p = tmp_path / name
        p.write_text(content, encoding="utf-8")
        return p
    return _write


def test_load_ignore_list_text(ignore_file):
    p = ignore_file("ignore.txt", textwrap.dedent("""\
        SECRET_KEY
        # this is a comment
        DB_*
    """))
    patterns = load_ignore_list(p)
    assert patterns == ["SECRET_KEY", "DB_*"]


def test_load_ignore_list_json(ignore_file):
    p = ignore_file("ignore.json", json.dumps(["SECRET_KEY", "DB_*"]))
    patterns = load_ignore_list(p)
    assert patterns == ["SECRET_KEY", "DB_*"]


def test_load_ignore_list_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_ignore_list(tmp_path / "nonexistent.txt")


def test_load_ignore_list_json_not_list(ignore_file):
    p = ignore_file("bad.json", json.dumps({"key": "value"}))
    with pytest.raises(ValueError, match="top-level array"):
        load_ignore_list(p)


def test_is_ignored_exact_match():
    assert is_ignored("SECRET_KEY", ["SECRET_KEY"])


def test_is_ignored_glob_match():
    assert is_ignored("DB_HOST", ["DB_*"])


def test_is_ignored_no_match():
    assert not is_ignored("API_URL", ["SECRET_KEY", "DB_*"])


def test_apply_ignore_removes_from_missing_in_compare(dirty_result):
    result = apply_ignore(dirty_result, ["SECRET_KEY"])
    assert "SECRET_KEY" not in result.missing_in_compare
    assert "DB_HOST" in result.missing_in_compare


def test_apply_ignore_glob_removes_multiple(dirty_result):
    result = apply_ignore(dirty_result, ["DB_*"])
    assert "DB_HOST" not in result.missing_in_compare


def test_apply_ignore_removes_from_mismatched(dirty_result):
    result = apply_ignore(dirty_result, ["API_URL"])
    assert "API_URL" not in result.mismatched
    assert "LOG_LEVEL" in result.mismatched


def test_apply_ignore_removes_from_missing_in_base(dirty_result):
    result = apply_ignore(dirty_result, ["NEW_FLAG"])
    assert "NEW_FLAG" not in result.missing_in_base


def test_apply_ignore_empty_patterns_returns_same(dirty_result):
    result = apply_ignore(dirty_result, [])
    assert result is dirty_result
