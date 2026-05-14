"""Tests for envdiff.trimmer."""
from __future__ import annotations

import pytest

from envdiff.trimmer import TrimResult, trim_env


@pytest.fixture()
def sample_env() -> dict:
    return {
        "APP_NAME": "myapp",
        "APP_SECRET": "s3cr3t",
        "DB_HOST": "localhost",
        "DB_PASSWORD": "pass",
        "DEBUG": "true",
        "EMPTY_KEY": None,
    }


# ---------------------------------------------------------------------------
# Basic behaviour
# ---------------------------------------------------------------------------

def test_no_patterns_returns_unchanged(sample_env):
    result = trim_env(sample_env, [])
    assert result.env == sample_env
    assert result.is_unchanged
    assert result.total_removed == 0


def test_exact_key_removed(sample_env):
    result = trim_env(sample_env, ["DEBUG"])
    assert "DEBUG" not in result.env
    assert "DEBUG" in result.removed_keys
    assert result.total_removed == 1


def test_multiple_exact_keys_removed(sample_env):
    result = trim_env(sample_env, ["APP_NAME", "DEBUG"])
    assert "APP_NAME" not in result.env
    assert "DEBUG" not in result.env
    assert result.total_removed == 2


def test_glob_pattern_removes_matching_keys(sample_env):
    result = trim_env(sample_env, ["DB_*"])
    assert "DB_HOST" not in result.env
    assert "DB_PASSWORD" not in result.env
    assert result.total_removed == 2


def test_glob_does_not_remove_non_matching_keys(sample_env):
    result = trim_env(sample_env, ["DB_*"])
    assert "APP_NAME" in result.env
    assert "APP_SECRET" in result.env
    assert "DEBUG" in result.env


def test_mixed_exact_and_glob(sample_env):
    result = trim_env(sample_env, ["DEBUG", "APP_*"])
    for key in ("DEBUG", "APP_NAME", "APP_SECRET"):
        assert key not in result.env
        assert key in result.removed_keys
    assert "DB_HOST" in result.env


def test_none_value_key_can_be_removed(sample_env):
    result = trim_env(sample_env, ["EMPTY_KEY"])
    assert "EMPTY_KEY" not in result.env
    assert result.total_removed == 1


def test_pattern_not_in_env_is_silently_ignored(sample_env):
    result = trim_env(sample_env, ["NONEXISTENT_KEY"])
    assert result.is_unchanged
    assert result.removed_keys == []


# ---------------------------------------------------------------------------
# TrimResult helpers
# ---------------------------------------------------------------------------

def test_as_dict_structure(sample_env):
    result = trim_env(sample_env, ["DEBUG", "DB_HOST"])
    d = result.as_dict()
    assert "env" in d
    assert "removed_keys" in d
    assert "total_removed" in d
    assert d["total_removed"] == 2
    assert d["removed_keys"] == sorted(["DEBUG", "DB_HOST"])


def test_removed_keys_sorted_in_as_dict(sample_env):
    result = trim_env(sample_env, ["DB_PASSWORD", "APP_NAME", "DEBUG"])
    d = result.as_dict()
    assert d["removed_keys"] == sorted(d["removed_keys"])
