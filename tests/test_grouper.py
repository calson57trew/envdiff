"""Tests for envdiff.grouper."""
from __future__ import annotations

import pytest

from envdiff.grouper import GroupReport, KeyGroup, _extract_prefix, group_env


@pytest.fixture()
def sample_env():
    return {
        "DB_HOST": "localhost",
        "DB_PORT": "5432",
        "DB_NAME": "mydb",
        "AWS_ACCESS_KEY": "AKIA…",
        "AWS_SECRET_KEY": "secret",
        "PORT": "8080",
        "DEBUG": "true",
    }


def test_extract_prefix_with_separator():
    assert _extract_prefix("DB_HOST") == "DB"


def test_extract_prefix_no_separator_returns_none():
    assert _extract_prefix("PORT") is None


def test_extract_prefix_leading_sep_returns_none():
    assert _extract_prefix("_HIDDEN") is None


def test_group_env_creates_correct_groups(sample_env):
    report = group_env(sample_env)
    assert "DB" in report.groups
    assert "AWS" in report.groups
    assert sorted(report.groups["DB"].keys) == ["DB_HOST", "DB_NAME", "DB_PORT"]
    assert sorted(report.groups["AWS"].keys) == ["AWS_ACCESS_KEY", "AWS_SECRET_KEY"]


def test_group_env_ungrouped_keys(sample_env):
    report = group_env(sample_env)
    assert "PORT" in report.ungrouped
    assert "DEBUG" in report.ungrouped


def test_group_env_total_groups(sample_env):
    report = group_env(sample_env)
    assert report.total_groups == 2


def test_group_env_total_ungrouped(sample_env):
    report = group_env(sample_env)
    assert report.total_ungrouped == 2


def test_group_env_min_size_filters_small_groups():
    env = {"DB_HOST": "x", "DB_PORT": "y", "SOLO_KEY": "z"}
    report = group_env(env, min_group_size=2)
    assert "DB" in report.groups
    assert "SOLO" not in report.groups
    assert "SOLO_KEY" in report.ungrouped


def test_group_env_empty_env():
    report = group_env({})
    assert report.total_groups == 0
    assert report.total_ungrouped == 0


def test_as_dict_structure(sample_env):
    report = group_env(sample_env)
    d = report.as_dict()
    assert "groups" in d
    assert "ungrouped" in d
    assert d["total_groups"] == 2
    db = d["groups"]["DB"]
    assert db["count"] == 3
    assert db["keys"] == sorted(["DB_HOST", "DB_PORT", "DB_NAME"])


def test_custom_separator():
    env = {"APP.HOST": "x", "APP.PORT": "y", "OTHER": "z"}
    report = group_env(env, sep=".")
    assert "APP" in report.groups
    assert len(report.groups["APP"].keys) == 2
