"""Summarize a DiffResult into high-level statistics."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from envdiff.differ import DiffResult


@dataclass
class DiffSummary:
    """High-level counts derived from a DiffResult."""

    total_keys: int
    missing_in_compare: int
    missing_in_base: int
    mismatched: int
    identical: int

    @property
    def total_issues(self) -> int:
        return self.missing_in_compare + self.missing_in_base + self.mismatched

    @property
    def is_clean(self) -> bool:
        return self.total_issues == 0

    def as_dict(self) -> Dict[str, int]:
        return {
            "total_keys": self.total_keys,
            "missing_in_compare": self.missing_in_compare,
            "missing_in_base": self.missing_in_base,
            "mismatched": self.mismatched,
            "identical": self.identical,
            "total_issues": self.total_issues,
        }


def summarize(result: DiffResult) -> DiffSummary:
    """Return a :class:`DiffSummary` for *result*."""
    missing_in_compare = len(result.missing_in_compare)
    missing_in_base = len(result.missing_in_base)
    mismatched = len(result.mismatched)

    all_keys = (
        set(result.missing_in_compare)
        | set(result.missing_in_base)
        | set(result.mismatched)
        | set(result.identical)
    )
    total_keys = len(all_keys)
    identical = len(result.identical)

    return DiffSummary(
        total_keys=total_keys,
        missing_in_compare=missing_in_compare,
        missing_in_base=missing_in_base,
        mismatched=mismatched,
        identical=identical,
    )
