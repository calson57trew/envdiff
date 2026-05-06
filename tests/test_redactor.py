"""Tests for envdiff.redactor."""

from __future__ import annotations

import pytest

from envdiff.redactor import (
    REDACTED_PLACEHOLDER,
    is_sensitive,
    redact_env,
)


# ---------------------------------------------------------------------------
# is_sensitive
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("key", [
    "DB_PASSWORD",
    "API_KEY",
    "AUTH_TOKEN",
    "APP_SECRET",
    "PRIVATE_KEY",
    "AWS_SECRET_ACCESS_KEY",
    "USER_CREDENTIAL",
])
def test_is_sensitive_returns_true_for_known_patterns(key: str) -> None:
    assert is_sensitive(key) is True


@pytest.mark.parametrize("key", [
    "APP_ENV",
    "PORT",
    "DEBUG",
    "DATABASE_URL",
    "LOG_LEVEL",
])
def test_is_sensitive_returns_false_for_benign_keys(key: str) -> None:
    assert is_sensitive(key) is False


def test_is_sensitive_case_insensitive() -> None:
    assert is_sensitive("db_password") is True
    assert is_sensitive("Api_Key") is True


# ---------------------------------------------------------------------------
# redact_env
# ---------------------------------------------------------------------------

def test_redact_env_replaces_sensitive_values() -> None:
    env = {"DB_PASSWORD": "s3cr3t", "APP_ENV": "production"}
    result = redact_env(env)
    assert result["DB_PASSWORD"] == REDACTED_PLACEHOLDER
    assert result["APP_ENV"] == "production"


def test_redact_env_preserves_none_values() -> None:
    env = {"API_KEY": None, "PORT": "8080"}
    result = redact_env(env)
    assert result["API_KEY"] is None


def test_redact_env_does_not_mutate_original() -> None:
    env = {"DB_PASSWORD": "hunter2", "HOST": "localhost"}
    original_copy = dict(env)
    redact_env(env)
    assert env == original_copy


def test_redact_env_extra_patterns() -> None:
    env = {"INTERNAL_CODE": "xyz", "APP_ENV": "staging"}
    result = redact_env(env, extra_patterns=[r".*INTERNAL.*"])
    assert result["INTERNAL_CODE"] == REDACTED_PLACEHOLDER
    assert result["APP_ENV"] == "staging"


def test_redact_env_custom_placeholder() -> None:
    env = {"AUTH_TOKEN": "abc123"}
    result = redact_env(env, placeholder="<hidden>")
    assert result["AUTH_TOKEN"] == "<hidden>"


def test_redact_env_empty_dict() -> None:
    assert redact_env({}) == {}
