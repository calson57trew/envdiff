"""Tests for envdiff.differ_stats."""
import pytest

from envdiff.differ import DiffResult
from envdiff.differ_stats import DiffStats, compute_stats


@pytest.fixture
def empty_result() -> DiffResult:
    return DiffResult(missing_in_compare=[], missing_in_base=[], mismatched={})


@pytest.fixture
def result_a() -> DiffResult:
    return DiffResult(
        missing_in_compare=["KEY_A", "KEY_B"],
        missing_in_base=["KEY_C"],
        mismatched={"KEY_D": ("val1", "val2")},
    )


@pytest.fixture
def result_b() -> DiffResult:
    return DiffResult(
        missing_in_compare=["KEY_A"],
        missing_in_base=[],
        mismatched={"KEY_D": ("val1", "val3"), "KEY_E": ("x", "y")},
    )


def test_compute_stats_empty_list():
    stats = compute_stats([])
    assert stats.total_snapshots == 0
    assert stats.total_issues == 0
    assert stats.most_frequent_missing == []
    assert stats.most_frequent_mismatched == []


def test_compute_stats_single_result(result_a):
    stats = compute_stats([result_a])
    assert stats.total_snapshots == 1
    assert stats.total_missing_in_compare == 2
    assert stats.total_missing_in_base == 1
    assert stats.total_mismatched == 1
    assert stats.total_issues == 4


def test_compute_stats_multiple_results(result_a, result_b):
    stats = compute_stats([result_a, result_b])
    assert stats.total_snapshots == 2
    assert stats.total_missing_in_compare == 3  # KEY_A x2, KEY_B x1
    assert stats.total_missing_in_base == 1
    assert stats.total_mismatched == 3  # KEY_D x2, KEY_E x1


def test_most_frequent_missing_sorted(result_a, result_b):
    stats = compute_stats([result_a, result_b])
    # KEY_A appears in both results, should be first
    assert stats.most_frequent_missing[0] == "KEY_A"


def test_most_frequent_mismatched_sorted(result_a, result_b):
    stats = compute_stats([result_a, result_b])
    assert stats.most_frequent_mismatched[0] == "KEY_D"


def test_as_dict_keys(result_a):
    stats = compute_stats([result_a])
    d = stats.as_dict()
    assert set(d.keys()) == {
        "total_snapshots",
        "total_issues",
        "total_missing_in_compare",
        "total_missing_in_base",
        "total_mismatched",
        "most_frequent_missing",
        "most_frequent_mismatched",
    }


def test_clean_results_have_no_issues(empty_result):
    stats = compute_stats([empty_result, empty_result])
    assert stats.total_issues == 0
    assert stats.total_snapshots == 2
