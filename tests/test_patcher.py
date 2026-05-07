"""Tests for envdiff.patcher."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.differ import DiffResult
from envdiff.patcher import PatchResult, patch_env, write_patched_env


@pytest.fixture()
def base_env():
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture()
def diff_result():
    return DiffResult(
        missing_in_compare={"DEBUG": "true"},
        missing_in_base={"SECRET_KEY": "abc123", "LOG_LEVEL": "info"},
        mismatched={"PORT": ("5432", "6543")},
    )


def test_patch_adds_missing_in_base(base_env, diff_result):
    result = patch_env(base_env, diff_result, add_missing=True)
    assert "SECRET_KEY" in result.patched
    assert "LOG_LEVEL" in result.patched
    assert result.patched["SECRET_KEY"] == "abc123"
    assert set(result.added) == {"SECRET_KEY", "LOG_LEVEL"}


def test_patch_does_not_add_when_flag_false(base_env, diff_result):
    result = patch_env(base_env, diff_result, add_missing=False)
    assert "SECRET_KEY" not in result.patched
    assert result.added == []


def test_patch_fixes_mismatched_when_flag_true(base_env, diff_result):
    result = patch_env(base_env, diff_result, fix_mismatched=True)
    assert result.patched["PORT"] == "6543"
    assert "PORT" in result.updated


def test_patch_leaves_mismatched_when_flag_false(base_env, diff_result):
    result = patch_env(base_env, diff_result, fix_mismatched=False)
    assert result.patched["PORT"] == "5432"
    assert result.updated == []


def test_patch_skips_specified_keys(base_env, diff_result):
    result = patch_env(
        base_env, diff_result, add_missing=True, skip_keys=["SECRET_KEY"]
    )
    assert "SECRET_KEY" not in result.patched
    assert "SECRET_KEY" in result.skipped
    assert "LOG_LEVEL" in result.patched


def test_patch_preserves_untouched_keys(base_env, diff_result):
    result = patch_env(base_env, diff_result)
    assert result.patched["HOST"] == "localhost"
    assert result.patched["DEBUG"] == "true"


def test_write_patched_env_creates_file(tmp_path):
    env = {"Z_KEY": "last", "A_KEY": "first", "SPACE": "hello world"}
    out = tmp_path / ".env.patched"
    write_patched_env(env, out)
    text = out.read_text()
    lines = [l for l in text.splitlines() if l]
    assert lines[0].startswith("A_KEY=")
    assert 'SPACE="hello world"' in text


def test_write_patched_env_none_value(tmp_path):
    env = {"EMPTY_KEY": None}
    out = tmp_path / ".env"
    write_patched_env(env, out)
    assert "EMPTY_KEY=" in out.read_text()
