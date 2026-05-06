"""Tests for envdiff.exporter."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.differ import DiffResult
from envdiff.exporter import ExportFormat, export_diff


@pytest.fixture()
def clean_result() -> DiffResult:
    base = {"APP_ENV": "production", "DB_URL": "postgres://localhost/db"}
    compare = {"APP_ENV": "production", "DB_URL": "postgres://localhost/db"}
    return DiffResult(
        base=base,
        compare=compare,
        missing_in_compare=set(),
        missing_in_base=set(),
        mismatched=set(),
    )


@pytest.fixture()
def dirty_result() -> DiffResult:
    base = {"APP_ENV": "production", "SECRET": "abc", "ONLY_BASE": "yes"}
    compare = {"APP_ENV": "staging", "ONLY_COMPARE": "yes"}
    return DiffResult(
        base=base,
        compare=compare,
        missing_in_compare={"SECRET", "ONLY_BASE"},
        missing_in_base={"ONLY_COMPARE"},
        mismatched={"APP_ENV"},
    )


def test_dotenv_export_sorted_keys(clean_result: DiffResult) -> None:
    content = export_diff(clean_result, ExportFormat.DOTENV)
    lines = content.strip().splitlines()
    assert lines[0].startswith("APP_ENV=")
    assert lines[1].startswith("DB_URL=")


def test_dotenv_export_quotes_values_with_spaces() -> None:
    result = DiffResult(
        base={"MSG": "hello world"},
        compare={},
        missing_in_compare=set(),
        missing_in_base=set(),
        mismatched=set(),
    )
    content = export_diff(result, ExportFormat.DOTENV)
    assert 'MSG="hello world"' in content


def test_json_export_structure(dirty_result: DiffResult) -> None:
    content = export_diff(dirty_result, ExportFormat.JSON)
    data = json.loads(content)
    assert set(data["missing_in_compare"]) == {"SECRET", "ONLY_BASE"}
    assert data["missing_in_base"] == ["ONLY_COMPARE"]
    assert data["mismatched"] == ["APP_ENV"]


def test_json_export_clean_result(clean_result: DiffResult) -> None:
    content = export_diff(clean_result, ExportFormat.JSON)
    data = json.loads(content)
    assert data["missing_in_compare"] == []
    assert data["missing_in_base"] == []
    assert data["mismatched"] == []


def test_markdown_export_contains_table_headers(dirty_result: DiffResult) -> None:
    content = export_diff(dirty_result, ExportFormat.MARKDOWN)
    assert "| Key |" in content
    assert "| Status |" in content


def test_markdown_export_lists_missing_keys(dirty_result: DiffResult) -> None:
    content = export_diff(dirty_result, ExportFormat.MARKDOWN)
    assert "missing in compare" in content
    assert "missing in base" in content
    assert "mismatch" in content


def test_markdown_export_no_differences(clean_result: DiffResult) -> None:
    content = export_diff(clean_result, ExportFormat.MARKDOWN)
    assert "no differences" in content


def test_export_writes_file(tmp_path: Path, clean_result: DiffResult) -> None:
    out = tmp_path / "report.md"
    export_diff(clean_result, ExportFormat.MARKDOWN, output_path=out)
    assert out.exists()
    assert "envdiff" in out.read_text()


def test_export_returns_content_even_when_writing_file(
    tmp_path: Path, dirty_result: DiffResult
) -> None:
    out = tmp_path / "diff.json"
    content = export_diff(dirty_result, ExportFormat.JSON, output_path=out)
    assert content == out.read_text()
