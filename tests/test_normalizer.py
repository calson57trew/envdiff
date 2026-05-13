"""Tests for envdiff.normalizer."""

from __future__ import annotations

import pytest

from envdiff.normalizer import NormalizeOptions, normalize_env


# ---------------------------------------------------------------------------
# fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_env() -> dict:
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "DEBUG": "True",
        "EMPTY_VAL": "",
        "SPACED": "  hello world  ",
        "ENABLED": "yes",
        "DISABLED": "OFF",
        "NONE_VAL": None,
    }


# ---------------------------------------------------------------------------
# key folding
# ---------------------------------------------------------------------------

def test_fold_keys_lowercases_all_keys(sample_env):
    result = normalize_env(sample_env, NormalizeOptions(fold_keys=True))
    assert "database_url" in result
    assert "DATABASE_URL" not in result


def test_no_fold_keys_preserves_case(sample_env):
    result = normalize_env(sample_env, NormalizeOptions(fold_keys=False))
    assert "DATABASE_URL" in result
    assert "database_url" not in result


# ---------------------------------------------------------------------------
# value stripping
# ---------------------------------------------------------------------------

def test_strip_values_removes_whitespace(sample_env):
    result = normalize_env(sample_env, NormalizeOptions(strip_values=True))
    assert result["spaced"] == "hello world"


def test_no_strip_preserves_whitespace(sample_env):
    opts = NormalizeOptions(fold_keys=False, strip_values=False)
    result = normalize_env(sample_env, opts)
    assert result["SPACED"] == "  hello world  "


# ---------------------------------------------------------------------------
# boolean folding
# ---------------------------------------------------------------------------

def test_fold_booleans_normalises_true_synonyms(sample_env):
    opts = NormalizeOptions(fold_booleans=True)
    result = normalize_env(sample_env, opts)
    assert result["debug"] == "true"
    assert result["enabled"] == "true"


def test_fold_booleans_normalises_false_synonyms(sample_env):
    opts = NormalizeOptions(fold_booleans=True)
    result = normalize_env(sample_env, opts)
    assert result["disabled"] == "false"


def test_no_fold_booleans_preserves_original(sample_env):
    opts = NormalizeOptions(fold_booleans=False, fold_keys=False)
    result = normalize_env(sample_env, opts)
    assert result["ENABLED"] == "yes"
    assert result["DISABLED"] == "OFF"


# ---------------------------------------------------------------------------
# empty-as-none
# ---------------------------------------------------------------------------

def test_empty_as_none_converts_empty_string(sample_env):
    opts = NormalizeOptions(empty_as_none=True)
    result = normalize_env(sample_env, opts)
    assert result["empty_val"] is None


def test_empty_as_none_false_keeps_empty_string(sample_env):
    opts = NormalizeOptions(empty_as_none=False)
    result = normalize_env(sample_env, opts)
    assert result["empty_val"] == ""


# ---------------------------------------------------------------------------
# none passthrough
# ---------------------------------------------------------------------------

def test_none_value_is_preserved_regardless(sample_env):
    result = normalize_env(sample_env, NormalizeOptions(fold_booleans=True, empty_as_none=True))
    assert result["none_val"] is None


# ---------------------------------------------------------------------------
# defaults
# ---------------------------------------------------------------------------

def test_default_options_applied_when_none_passed():
    env = {"MY_KEY": "  value  "}
    result = normalize_env(env)
    # Default: fold_keys=True, strip_values=True
    assert "my_key" in result
    assert result["my_key"] == "value"
