"""Tests for envdiff.reporter."""

from __future__ import annotations

import json
import io

import pytest

from envdiff.differ import DiffResult
from envdiff.reporter import OutputFormat, render


@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(missing_in_compare=set(), missing_in_base=set(), mismatched={})


@pytest.fixture()
def dirty_result() -> DiffResult:
    return DiffResult(
        missing_in_compare={"SECRET_KEY"},
        missing_in_base={"NEW_VAR"},
        mismatched={"DB_HOST": ("localhost", "db.prod")},
    )


def _capture(result, fmt, base="base.env", cmp="compare.env") -> str:
    buf = io.StringIO()
    render(result, base_name=base, compare_name=cmp, fmt=fmt, out=buf)
    return buf.getvalue()


def test_text_no_differences(clean_result):
    out = _capture(clean_result, OutputFormat.TEXT)
    assert "No differences found" in out


def test_text_missing_in_compare(dirty_result):
    out = _capture(dirty_result, OutputFormat.TEXT)
    assert "Missing in 'compare.env'" in out
    assert "SECRET_KEY" in out


def test_text_missing_in_base(dirty_result):
    out = _capture(dirty_result, OutputFormat.TEXT)
    assert "Missing in 'base.env'" in out
    assert "NEW_VAR" in out


def test_text_mismatched(dirty_result):
    out = _capture(dirty_result, OutputFormat.TEXT)
    assert "DB_HOST" in out
    assert "localhost" in out
    assert "db.prod" in out


def test_json_output_structure(dirty_result):
    out = _capture(dirty_result, OutputFormat.JSON)
    data = json.loads(out)
    assert data["base"] == "base.env"
    assert "SECRET_KEY" in data["missing_in_compare"]
    assert "NEW_VAR" in data["missing_in_base"]
    assert data["mismatched"]["DB_HOST"] == {"base": "localhost", "compare": "db.prod"}


def test_json_no_differences(clean_result):
    out = _capture(clean_result, OutputFormat.JSON)
    data = json.loads(out)
    assert data["missing_in_compare"] == []
    assert data["missing_in_base"] == []
    assert data["mismatched"] == {}


def test_github_warnings_for_missing(dirty_result):
    out = _capture(dirty_result, OutputFormat.GITHUB)
    assert "::warning::" in out
    assert "SECRET_KEY" in out


def test_github_error_for_mismatch(dirty_result):
    out = _capture(dirty_result, OutputFormat.GITHUB)
    assert "::error::" in out
    assert "DB_HOST" in out


def test_github_notice_when_clean(clean_result):
    out = _capture(clean_result, OutputFormat.GITHUB)
    assert "::notice::" in out
