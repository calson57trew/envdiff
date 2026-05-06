"""Tests for envdiff.merger."""

from __future__ import annotations

import pytest

from envdiff.merger import MergeConflict, MergeResult, merge_envs


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base() -> dict:
    return {"HOST": "localhost", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture()
def overlay() -> dict:
    return {"HOST": "prod.example.com", "PORT": "5432", "SECRET": "abc123"}


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

def test_merge_empty_sources_returns_empty():
    result = merge_envs([])
    assert result.merged == {}
    assert result.conflicts == []
    assert not result.has_conflicts


def test_merge_single_source(base):
    result = merge_envs([("base", base)])
    assert result.merged == base
    assert not result.has_conflicts


def test_merge_combines_unique_keys(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    assert "SECRET" in result.merged
    assert "DEBUG" in result.merged


def test_merge_detects_conflict_on_different_values(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    conflict_keys = {c.key for c in result.conflicts}
    assert "HOST" in conflict_keys
    assert result.has_conflicts


def test_merge_no_conflict_for_identical_values(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    conflict_keys = {c.key for c in result.conflicts}
    # PORT is the same in both sources
    assert "PORT" not in conflict_keys


def test_merge_prefer_overrides_conflict(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)], prefer="overlay")
    # HOST differs; overlay should win
    assert result.merged["HOST"] == "prod.example.com"


def test_merge_without_prefer_keeps_first_value(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    assert result.merged["HOST"] == "localhost"


def test_conflict_contains_all_source_values(base, overlay):
    result = merge_envs([("base", base), ("overlay", overlay)])
    host_conflict = next(c for c in result.conflicts if c.key == "HOST")
    assert host_conflict.values["base"] == "localhost"
    assert host_conflict.values["overlay"] == "prod.example.com"
    assert set(host_conflict.sources) == {"base", "overlay"}


def test_merge_three_sources_all_conflicts():
    a = {"KEY": "1"}
    b = {"KEY": "2"}
    c = {"KEY": "3"}
    result = merge_envs([("a", a), ("b", b), ("c", c)])
    assert result.has_conflicts
    assert result.conflicts[0].key == "KEY"
    assert len(result.conflicts[0].values) == 3
