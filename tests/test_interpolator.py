"""Tests for envdiff.interpolator."""
from __future__ import annotations

import pytest

from envdiff.interpolator import interpolate_env, InterpolationResult


@pytest.fixture()
def base_env():
    return {
        "HOME": "/home/user",
        "CONFIG_DIR": "${HOME}/.config",
        "NESTED": "${CONFIG_DIR}/app",
        "NO_REF": "plain",
        "EMPTY": None,
    }


def test_plain_values_unchanged(base_env):
    result = interpolate_env(base_env)
    assert result.resolved["NO_REF"] == "plain"


def test_none_values_preserved(base_env):
    result = interpolate_env(base_env)
    assert result.resolved["EMPTY"] is None


def test_resolves_braced_reference(base_env):
    result = interpolate_env(base_env)
    assert result.resolved["CONFIG_DIR"] == "/home/user/.config"


def test_resolves_nested_reference(base_env):
    # NESTED references CONFIG_DIR which itself references HOME
    # Single-pass: CONFIG_DIR already resolved in the source mapping
    result = interpolate_env(base_env)
    assert result.resolved["NESTED"] == "/home/user/.config/app"


def test_resolves_bare_dollar_syntax():
    env = {"USER": "alice", "GREETING": "Hello $USER"}
    result = interpolate_env(env)
    assert result.resolved["GREETING"] == "Hello alice"


def test_strict_leaves_unresolvable_token():
    env = {"VAL": "${MISSING}_suffix"}
    result = interpolate_env(env, strict=True)
    assert result.resolved["VAL"] == "${MISSING}_suffix"
    assert result.unresolved_refs == []


def test_non_strict_replaces_unresolvable_with_empty():
    env = {"VAL": "${MISSING}_suffix"}
    result = interpolate_env(env, strict=False)
    assert result.resolved["VAL"] == "_suffix"
    assert "VAL" in result.unresolved_refs


def test_no_unresolved_refs_when_all_present(base_env):
    result = interpolate_env(base_env, strict=False)
    assert result.unresolved_refs == []


def test_empty_env_returns_empty_result():
    result = interpolate_env({})
    assert result.resolved == {}
    assert result.unresolved_refs == []


def test_self_referential_key_strict():
    # A key that references itself should remain unchanged in strict mode
    env = {"X": "${X}"}
    result = interpolate_env(env, strict=True)
    assert result.resolved["X"] == "${X}"


def test_interpolation_result_is_dataclass():
    result = interpolate_env({"A": "1"})
    assert isinstance(result, InterpolationResult)
    assert hasattr(result, "resolved")
    assert hasattr(result, "unresolved_refs")
