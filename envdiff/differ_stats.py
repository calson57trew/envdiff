"""Compute statistics and trend data from a sequence of DiffResults."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from envdiff.differ import DiffResult


@dataclass
class DiffStats:
    """Aggregated statistics over one or more DiffResult snapshots."""

    total_snapshots: int = 0
    total_missing_in_compare: int = 0
    total_missing_in_base: int = 0
    total_mismatched: int = 0
    most_frequent_missing: List[str] = field(default_factory=list)
    most_frequent_mismatched: List[str] = field(default_factory=list)

    @property
    def total_issues(self) -> int:
        return (
            self.total_missing_in_compare
            + self.total_missing_in_base
            + self.total_mismatched
        )

    def as_dict(self) -> dict:
        return {
            "total_snapshots": self.total_snapshots,
            "total_issues": self.total_issues,
            "total_missing_in_compare": self.total_missing_in_compare,
            "total_missing_in_base": self.total_missing_in_base,
            "total_mismatched": self.total_mismatched,
            "most_frequent_missing": self.most_frequent_missing,
            "most_frequent_mismatched": self.most_frequent_mismatched,
        }


def compute_stats(results: List[DiffResult]) -> DiffStats:
    """Compute aggregate statistics across a list of DiffResult objects."""
    if not results:
        return DiffStats()

    missing_counts: dict[str, int] = {}
    mismatch_counts: dict[str, int] = {}

    total_missing_compare = 0
    total_missing_base = 0
    total_mismatched = 0

    for result in results:
        total_missing_compare += len(result.missing_in_compare)
        total_missing_base += len(result.missing_in_base)
        total_mismatched += len(result.mismatched)

        for key in result.missing_in_compare:
            missing_counts[key] = missing_counts.get(key, 0) + 1
        for key in result.missing_in_base:
            missing_counts[key] = missing_counts.get(key, 0) + 1
        for key in result.mismatched:
            mismatch_counts[key] = mismatch_counts.get(key, 0) + 1

    top_missing = sorted(missing_counts, key=lambda k: missing_counts[k], reverse=True)[:5]
    top_mismatched = sorted(mismatch_counts, key=lambda k: mismatch_counts[k], reverse=True)[:5]

    return DiffStats(
        total_snapshots=len(results),
        total_missing_in_compare=total_missing_compare,
        total_missing_in_base=total_missing_base,
        total_mismatched=total_mismatched,
        most_frequent_missing=top_missing,
        most_frequent_mismatched=top_mismatched,
    )
