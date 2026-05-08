"""Tests for envdiff.auditor and envdiff.cli_audit."""
from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

import pytest

from envdiff.auditor import AuditEntry, AuditLog, load_audit_log, record_audit
from envdiff.differ import DiffResult
from envdiff.cli_audit import build_audit_parser, run_audit


@pytest.fixture()
def audit_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.jsonl"


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        missing_in_compare={"SECRET"},
        missing_in_base={"NEW_KEY"},
        mismatched={"PORT": ("8080", "9090")},
    )


@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(missing_in_compare=set(), missing_in_base=set(), mismatched={})


# --- record_audit ---

def test_record_audit_creates_file(audit_path, diff_result):
    record_audit(diff_result, "base.env", "prod.env", audit_path)
    assert audit_path.exists()


def test_record_audit_entry_counts(audit_path, diff_result):
    entry = record_audit(diff_result, "base.env", "prod.env", audit_path)
    assert entry.missing_in_compare == 1
    assert entry.missing_in_base == 1
    assert entry.mismatched == 1


def test_record_audit_with_label(audit_path, diff_result):
    entry = record_audit(diff_result, "a.env", "b.env", audit_path, label="ci-run")
    assert entry.label == "ci-run"


def test_record_audit_appends_multiple(audit_path, diff_result, clean_result):
    record_audit(diff_result, "a.env", "b.env", audit_path)
    record_audit(clean_result, "a.env", "b.env", audit_path)
    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 2


# --- load_audit_log ---

def test_load_audit_log_missing_file_returns_empty(tmp_path):
    log = load_audit_log(tmp_path / "nonexistent.jsonl")
    assert isinstance(log, AuditLog)
    assert log.entries == []


def test_load_audit_log_round_trip(audit_path, diff_result):
    record_audit(diff_result, "base.env", "compare.env", audit_path, label="test")
    log = load_audit_log(audit_path)
    assert len(log.entries) == 1
    e = log.entries[0]
    assert e.base_file == "base.env"
    assert e.compare_file == "compare.env"
    assert e.label == "test"
    assert e.mismatched == 1


# --- cli_audit ---

def _run(args, audit_file):
    parser = build_audit_parser()
    ns = parser.parse_args(["--audit-file", str(audit_file)] + args)
    out = StringIO()
    code = run_audit(ns, out=out)
    return code, out.getvalue()


def test_cli_audit_empty_log(audit_path):
    code, output = _run([], audit_path)
    assert code == 0
    assert "No audit entries found" in output


def test_cli_audit_text_output(audit_path, diff_result):
    record_audit(diff_result, "base.env", "prod.env", audit_path)
    code, output = _run([], audit_path)
    assert code == 0
    assert "base.env" in output
    assert "prod.env" in output


def test_cli_audit_json_output(audit_path, diff_result):
    record_audit(diff_result, "base.env", "prod.env", audit_path)
    code, output = _run(["--format", "json"], audit_path)
    assert code == 0
    data = json.loads(output)
    assert isinstance(data, list)
    assert data[0]["base_file"] == "base.env"


def test_cli_audit_last_flag(audit_path, diff_result, clean_result):
    record_audit(diff_result, "a.env", "b.env", audit_path)
    record_audit(clean_result, "c.env", "d.env", audit_path)
    code, output = _run(["--last", "1", "--format", "json"], audit_path)
    data = json.loads(output)
    assert len(data) == 1
    assert data[0]["base_file"] == "c.env"
