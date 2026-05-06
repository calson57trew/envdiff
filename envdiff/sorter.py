"""Utilities for sorting and grouping diff results by severity or key name."""

from __future__ import annotations

from enum import Enum
from typing import List, Tuple

from envdiff.differ import DiffResult


class SortOrder(str, Enum):
    KEY = "key"
    SEVERITY = "severity"


# Severity rank: missing keys are more severe than mismatched values.
_SEVERITY_RANK = {
    "missing_in_compare": 0,
    "missing_in_base": 1,
    "mismatched": 2,
}


def _entry_severity(entry: Tuple[str, str]) -> int:
    """Return numeric severity for a (key, category) tuple."""
    _key, category = entry
    return _SEVERITY_RANK.get(category, 99)


def _categorised_entries(result: DiffResult) -> List[Tuple[str, str]]:
    """Flatten a DiffResult into (key, category) pairs."""
    entries: List[Tuple[str, str]] = []
    for key in result.missing_in_compare:
        entries.append((key, "missing_in_compare"))
    for key in result.missing_in_base:
        entries.append((key, "missing_in_base"))
    for key in result.mismatched:
        entries.append((key, "mismatched"))
    return entries


def sorted_entries(
    result: DiffResult,
    order: SortOrder = SortOrder.KEY,
) -> List[Tuple[str, str]]:
    """Return diff entries sorted by *order*.

    Parameters
    ----------
    result:
        The :class:`~envdiff.differ.DiffResult` to sort.
    order:
        ``SortOrder.KEY`` sorts alphabetically by key name.
        ``SortOrder.SEVERITY`` groups by severity (missing first).

    Returns
    -------
    list of (key, category) tuples.
    """
    entries = _categorised_entries(result)
    if order == SortOrder.KEY:
        return sorted(entries, key=lambda e: e[0].lower())
    if order == SortOrder.SEVERITY:
        return sorted(entries, key=lambda e: (_entry_severity(e), e[0].lower()))
    return entries
