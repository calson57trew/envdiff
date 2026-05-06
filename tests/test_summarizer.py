"""Tests for envdiff.summarizer."""
from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.summarizer import DiffSummary, summarize


@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=[],
        missing_in_base=[],
        mismatched={},
        identical={"KEY": "val", "OTHER": "x"},
    )


@pytest.fixture()
def dirty_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=["GONE"],
        missing_in_base=["NEW"],
        mismatched={"CHANGED": ("old", "new")},
        identical={"SAME": "y"},
    )


def test_summarize_clean_result_is_clean(clean_result):
    s = summarize(clean_result)
    assert s.is_clean is True


def test_summarize_clean_result_counts(clean_result):
    s = summarize(clean_result)
    assert s.total_keys == 2
    assert s.identical == 2
    assert s.total_issues == 0


def test_summarize_dirty_result_not_clean(dirty_result):
    s = summarize(dirty_result)
    assert s.is_clean is False


def test_summarize_dirty_result_counts(dirty_result):
    s = summarize(dirty_result)
    assert s.missing_in_compare == 1
    assert s.missing_in_base == 1
    assert s.mismatched == 1
    assert s.identical == 1
    assert s.total_keys == 4
    assert s.total_issues == 3


def test_summarize_as_dict_keys(dirty_result):
    d = summarize(dirty_result).as_dict()
    expected_keys = {
        "total_keys",
        "missing_in_compare",
        "missing_in_base",
        "mismatched",
        "identical",
        "total_issues",
    }
    assert set(d.keys()) == expected_keys


def test_summarize_empty_result():
    result = DiffResult(
        missing_in_compare=[],
        missing_in_base=[],
        mismatched={},
        identical={},
    )
    s = summarize(result)
    assert s.total_keys == 0
    assert s.is_clean is True


def test_diff_summary_total_issues_property():
    s = DiffSummary(
        total_keys=10,
        missing_in_compare=2,
        missing_in_base=1,
        mismatched=3,
        identical=4,
    )
    assert s.total_issues == 6
