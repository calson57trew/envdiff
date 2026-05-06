"""Tests for envdiff.filter."""

from __future__ import annotations

import pytest

from envdiff.filter import filter_env


@pytest.fixture()
def sample_env() -> dict[str, str]:
    return {
        "DATABASE_URL": "postgres://localhost/db",
        "DATABASE_POOL": "5",
        "REDIS_URL": "redis://localhost",
        "SECRET_KEY": "supersecret",
        "DEBUG": "true",
    }


def test_no_filters_returns_all(sample_env: dict[str, str]) -> None:
    assert filter_env(sample_env) == sample_env


def test_include_exact_key(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, include=["DEBUG"])
    assert result == {"DEBUG": "true"}


def test_include_glob_pattern(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, include=["DATABASE_*"])
    assert set(result.keys()) == {"DATABASE_URL", "DATABASE_POOL"}


def test_exclude_exact_key(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, exclude=["SECRET_KEY"])
    assert "SECRET_KEY" not in result
    assert len(result) == len(sample_env) - 1


def test_exclude_glob_pattern(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, exclude=["DATABASE_*"])
    assert "DATABASE_URL" not in result
    assert "DATABASE_POOL" not in result
    assert "REDIS_URL" in result


def test_include_then_exclude(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, include=["DATABASE_*"], exclude=["DATABASE_POOL"])
    assert result == {"DATABASE_URL": "postgres://localhost/db"}


def test_include_no_match_returns_empty(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, include=["NONEXISTENT_*"])
    assert result == {}


def test_original_env_not_mutated(sample_env: dict[str, str]) -> None:
    original_copy = dict(sample_env)
    filter_env(sample_env, include=["DEBUG"], exclude=["DEBUG"])
    assert sample_env == original_copy


def test_multiple_include_patterns(sample_env: dict[str, str]) -> None:
    result = filter_env(sample_env, include=["DEBUG", "REDIS_*"])
    assert set(result.keys()) == {"DEBUG", "REDIS_URL"}
