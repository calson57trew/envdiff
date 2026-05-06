"""Tests for envdiff.linter."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.linter import lint_env_file, LintResult, LintIssue


@pytest.fixture()
def env_file(tmp_path: Path):
    """Return a helper that writes content to a temp .env file."""

    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(content, encoding="utf-8")
        return p

    return _write


def test_clean_file_has_no_issues(env_file):
    p = env_file("DB_HOST=localhost\nDB_PORT=5432\n")
    result = lint_env_file(p)
    assert not result.has_issues


def test_blank_lines_and_comments_ignored(env_file):
    p = env_file("# comment\n\nAPP_ENV=production\n")
    result = lint_env_file(p)
    assert not result.has_issues


def test_missing_equals_is_error(env_file):
    p = env_file("BADLINE\n")
    result = lint_env_file(p)
    assert len(result.errors) == 1
    assert "no '='" in result.errors[0].message
    assert result.errors[0].line_number == 1


def test_whitespace_around_key_is_warning(env_file):
    p = env_file(" DB_HOST =localhost\n")
    result = lint_env_file(p)
    warnings = result.warnings
    assert any("Whitespace" in w.message for w in warnings)


def test_lowercase_key_is_warning(env_file):
    p = env_file("db_host=localhost\n")
    result = lint_env_file(p)
    warnings = result.warnings
    assert any("UPPER_SNAKE_CASE" in w.message for w in warnings)
    assert warnings[0].key == "db_host"


def test_duplicate_key_is_error(env_file):
    p = env_file("API_KEY=abc\nAPI_KEY=xyz\n")
    result = lint_env_file(p)
    errors = result.errors
    assert len(errors) == 1
    assert "Duplicate" in errors[0].message
    assert errors[0].line_number == 2


def test_has_issues_property(env_file):
    p = env_file("BADLINE\n")
    result = lint_env_file(p)
    assert result.has_issues


def test_result_path_matches_input(env_file):
    p = env_file("KEY=val\n")
    result = lint_env_file(p)
    assert result.path == str(p)


def test_mixed_issues_counted_separately(env_file):
    content = "BADLINE\ndb_host=localhost\nAPI_KEY=a\nAPI_KEY=b\n"
    p = env_file(content)
    result = lint_env_file(p)
    assert len(result.errors) == 2   # missing '=' + duplicate
    assert len(result.warnings) >= 1  # lowercase key
