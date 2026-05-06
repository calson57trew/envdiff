"""Tests for envdiff.sorter."""

from __future__ import annotations

import pytest

from envdiff.differ import DiffResult
from envdiff.sorter import SortOrder, sorted_entries


@pytest.fixture()
def mixed_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=["ZEBRA", "ALPHA"],
        missing_in_base=["MANGO"],
        mismatched=["BETA"],
    )


@pytest.fixture()
def empty_result() -> DiffResult:
    return DiffResult(missing_in_compare=[], missing_in_base=[], mismatched=[])


def test_sorted_by_key_alphabetical(mixed_result: DiffResult) -> None:
    entries = sorted_entries(mixed_result, order=SortOrder.KEY)
    keys = [e[0] for e in entries]
    assert keys == sorted(keys, key=str.lower)


def test_sorted_by_severity_missing_first(mixed_result: DiffResult) -> None:
    entries = sorted_entries(mixed_result, order=SortOrder.SEVERITY)
    categories = [e[1] for e in entries]
    # All missing_in_compare come before missing_in_base before mismatched
    seen_categories: list[str] = []
    for cat in categories:
        if cat not in seen_categories:
            seen_categories.append(cat)
    severity_order = ["missing_in_compare", "missing_in_base", "mismatched"]
    assert seen_categories == [c for c in severity_order if c in seen_categories]


def test_sorted_by_key_default_is_key(mixed_result: DiffResult) -> None:
    default_entries = sorted_entries(mixed_result)
    key_entries = sorted_entries(mixed_result, order=SortOrder.KEY)
    assert default_entries == key_entries


def test_empty_result_returns_empty_list(empty_result: DiffResult) -> None:
    assert sorted_entries(empty_result) == []


def test_categories_are_correct(mixed_result: DiffResult) -> None:
    entries = sorted_entries(mixed_result)
    category_map = {key: cat for key, cat in entries}
    assert category_map["ZEBRA"] == "missing_in_compare"
    assert category_map["ALPHA"] == "missing_in_compare"
    assert category_map["MANGO"] == "missing_in_base"
    assert category_map["BETA"] == "mismatched"


def test_severity_within_same_category_sorted_by_key(mixed_result: DiffResult) -> None:
    entries = sorted_entries(mixed_result, order=SortOrder.SEVERITY)
    missing_keys = [e[0] for e in entries if e[1] == "missing_in_compare"]
    assert missing_keys == sorted(missing_keys, key=str.lower)
