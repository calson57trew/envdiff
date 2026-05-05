"""Tests for envdiff.differ module."""

import pytest

from envdiff.differ import diff_envs, DiffResult


BASE = {
    "APP_NAME": "myapp",
    "DEBUG": "false",
    "DATABASE_URL": "postgres://localhost/dev",
    "SECRET_KEY": "abc123",
}

COMPARE = {
    "APP_NAME": "myapp",
    "DEBUG": "true",          # mismatched
    "DATABASE_URL": "postgres://localhost/prod",  # mismatched
    "NEW_FEATURE_FLAG": "1",  # extra in compare
    # SECRET_KEY missing
}


def test_diff_detects_missing_in_compare():
    result = diff_envs(BASE, COMPARE)
    assert "SECRET_KEY" in result.missing_in_compare


def test_diff_detects_missing_in_base():
    result = diff_envs(BASE, COMPARE)
    assert "NEW_FEATURE_FLAG" in result.missing_in_base


def test_diff_detects_mismatched_values():
    result = diff_envs(BASE, COMPARE)
    assert "DEBUG" in result.mismatched
    assert result.mismatched["DEBUG"] == ("false", "true")
    assert "DATABASE_URL" in result.mismatched


def test_diff_no_value_check():
    result = diff_envs(BASE, COMPARE, check_values=False)
    assert result.mismatched == {}
    assert "SECRET_KEY" in result.missing_in_compare


def test_diff_identical_envs():
    result = diff_envs(BASE, BASE)
    assert not result.has_differences


def test_diff_labels_are_stored():
    result = diff_envs(BASE, COMPARE, base_label="dev", compare_label="prod")
    assert result.base_label == "dev"
    assert result.compare_label == "prod"


def test_has_differences_true():
    result = diff_envs(BASE, COMPARE)
    assert result.has_differences is True


def test_has_differences_false():
    result = diff_envs({"A": "1"}, {"A": "1"})
    assert result.has_differences is False
