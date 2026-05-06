"""Tests for envdiff.validator."""

import pytest

from envdiff.validator import KeySchema, ValidationResult, validate_env


@pytest.fixture()
def base_env() -> dict:
    return {
        "APP_ENV": "production",
        "PORT": "8080",
        "DEBUG": "false",
        "SECRET_KEY": "s3cr3t",
    }


@pytest.fixture()
def strict_schema() -> dict:
    return {
        "APP_ENV": KeySchema(required=True, allowed_values=["production", "staging", "development"]),
        "PORT": KeySchema(required=True, pattern="[0-9]*"),
        "DEBUG": KeySchema(required=True, allowed_values=["true", "false"]),
        "SECRET_KEY": KeySchema(required=True),
    }


def test_valid_env_passes(base_env, strict_schema):
    result = validate_env(base_env, strict_schema)
    assert result.is_valid
    assert result.missing_required == []
    assert result.type_errors == {}


def test_missing_required_key(strict_schema):
    env = {"PORT": "8080", "DEBUG": "false", "SECRET_KEY": "x"}
    result = validate_env(env, strict_schema)
    assert not result.is_valid
    assert "APP_ENV" in result.missing_required


def test_optional_key_absent_is_ok():
    schema = {"REQUIRED": KeySchema(required=True), "OPTIONAL": KeySchema(required=False)}
    env = {"REQUIRED": "yes"}
    result = validate_env(env, schema)
    assert result.is_valid
    assert result.missing_required == []


def test_disallowed_value_reported(base_env, strict_schema):
    base_env["APP_ENV"] = "local"  # not in allowed_values
    result = validate_env(base_env, strict_schema)
    assert not result.is_valid
    assert "APP_ENV" in result.type_errors


def test_pattern_mismatch_reported(base_env, strict_schema):
    base_env["PORT"] = "not-a-port"
    result = validate_env(base_env, strict_schema)
    assert "PORT" in result.type_errors


def test_unknown_keys_ignored_by_default(base_env, strict_schema):
    base_env["EXTRA_KEY"] = "value"
    result = validate_env(base_env, strict_schema)
    assert result.unknown_keys == []


def test_unknown_keys_reported_when_strict(base_env, strict_schema):
    base_env["EXTRA_KEY"] = "value"
    result = validate_env(base_env, strict_schema, allow_unknown=False)
    assert "EXTRA_KEY" in result.unknown_keys


def test_empty_env_all_required_missing(strict_schema):
    result = validate_env({}, strict_schema)
    assert set(result.missing_required) == set(strict_schema.keys())
    assert not result.is_valid


def test_validation_result_is_valid_ignores_unknown_keys():
    """unknown_keys alone should not make is_valid False."""
    result = ValidationResult(unknown_keys=["EXTRA"])
    assert result.is_valid
