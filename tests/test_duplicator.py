"""Tests for envdiff.duplicator."""
from __future__ import annotations

import pytest

from envdiff.duplicator import DuplicateGroup, DuplicateReport, find_duplicates


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def no_dupes_env():
    return {"A": "alpha", "B": "beta", "C": "gamma"}


@pytest.fixture()
def dupes_env():
    return {
        "SECRET": "abc123",
        "TOKEN": "abc123",  # duplicate of SECRET
        "HOST": "localhost",
        "DB_HOST": "localhost",  # duplicate of HOST
        "PORT": "5432",
    }


# ---------------------------------------------------------------------------
# find_duplicates
# ---------------------------------------------------------------------------

def test_no_duplicates_returns_empty_report(no_dupes_env):
    report = find_duplicates(no_dupes_env)
    assert not report.has_duplicates
    assert report.groups == []
    assert report.total_duplicate_keys == 0


def test_detects_duplicate_values(dupes_env):
    report = find_duplicates(dupes_env)
    assert report.has_duplicates
    assert len(report.groups) == 2


def test_duplicate_group_contains_correct_keys(dupes_env):
    report = find_duplicates(dupes_env)
    values_to_keys = {g.value: sorted(g.keys) for g in report.groups}
    assert values_to_keys["abc123"] == ["SECRET", "TOKEN"]
    assert values_to_keys["localhost"] == ["DB_HOST", "HOST"]


def test_total_duplicate_keys_count(dupes_env):
    report = find_duplicates(dupes_env)
    # 2 keys share "abc123" + 2 keys share "localhost" = 4
    assert report.total_duplicate_keys == 4


def test_empty_values_ignored_by_default():
    env = {"A": "", "B": "", "C": None, "D": None, "E": "real"}
    report = find_duplicates(env)
    assert not report.has_duplicates


def test_empty_values_included_when_flag_false():
    env = {"A": "", "B": "", "C": "real"}
    report = find_duplicates(env, ignore_empty=False)
    assert report.has_duplicates
    assert len(report.groups) == 1
    assert sorted(report.groups[0].keys) == ["A", "B"]


def test_none_values_included_when_flag_false():
    env = {"X": None, "Y": None}
    report = find_duplicates(env, ignore_empty=False)
    assert report.has_duplicates
    assert report.groups[0].value is None


def test_as_dict_structure(dupes_env):
    report = find_duplicates(dupes_env)
    d = report.as_dict()
    assert d["has_duplicates"] is True
    assert isinstance(d["groups"], list)
    for group in d["groups"]:
        assert "value" in group
        assert "keys" in group
        assert isinstance(group["keys"], list)


def test_groups_sorted_by_first_key():
    env = {"Z": "same", "A": "same", "M": "other", "B": "other"}
    report = find_duplicates(env)
    first_keys = [sorted(g.keys)[0] for g in report.groups]
    assert first_keys == sorted(first_keys)


def test_single_key_per_value_not_reported():
    env = {"ONLY": "unique"}
    report = find_duplicates(env)
    assert not report.has_duplicates
