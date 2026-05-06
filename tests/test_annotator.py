"""Tests for envdiff.annotator."""
from __future__ import annotations

import pytest

from envdiff.annotator import AnnotatedEntry, AnnotatedEnv, annotate
from envdiff.differ import DiffResult


@pytest.fixture()
def base_env() -> dict:
    return {"HOST": "localhost", "PORT": "5432", "SECRET": "abc"}


@pytest.fixture()
def compare_env() -> dict:
    return {"HOST": "prod.example.com", "PORT": "5432", "DEBUG": "true"}


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=["SECRET"],
        missing_in_base=["DEBUG"],
        mismatched=[("HOST", "localhost", "prod.example.com")],
    )


def test_annotate_returns_annotated_env(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    assert isinstance(result, AnnotatedEnv)


def test_all_keys_present(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    assert set(result.entries.keys()) == {"HOST", "PORT", "SECRET", "DEBUG"}


def test_ok_status_for_matching_key(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    assert result.entries["PORT"].status == "ok"


def test_mismatch_status(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    entry = result.entries["HOST"]
    assert entry.status == "mismatch"
    assert entry.base_value == "localhost"
    assert entry.compare_value == "prod.example.com"


def test_missing_in_compare_status(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    entry = result.entries["SECRET"]
    assert entry.status == "missing_in_compare"
    assert entry.value == "abc"


def test_missing_in_base_status(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    entry = result.entries["DEBUG"]
    assert entry.status == "missing_in_base"
    assert entry.value == "true"


def test_by_status_filters_correctly(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    mismatches = result.by_status("mismatch")
    assert len(mismatches) == 1
    assert mismatches[0].key == "HOST"


def test_empty_envs_produce_empty_annotation():
    empty_result = DiffResult(missing_in_compare=[], missing_in_base=[], mismatched=[])
    result = annotate({}, {}, empty_result)
    assert result.entries == {}


def test_keys_are_sorted(base_env, compare_env, diff_result):
    result = annotate(base_env, compare_env, diff_result)
    keys = list(result.entries.keys())
    assert keys == sorted(keys)
