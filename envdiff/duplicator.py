"""Detect duplicate values across keys in an environment mapping."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DuplicateGroup:
    """A set of keys that share the same value."""

    value: Optional[str]
    keys: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"value": self.value, "keys": sorted(self.keys)}


@dataclass
class DuplicateReport:
    """Full report of duplicate-value groups found in an env mapping."""

    groups: List[DuplicateGroup] = field(default_factory=list)

    @property
    def has_duplicates(self) -> bool:
        return len(self.groups) > 0

    @property
    def total_duplicate_keys(self) -> int:
        return sum(len(g.keys) for g in self.groups)

    def as_dict(self) -> dict:
        return {
            "has_duplicates": self.has_duplicates,
            "total_duplicate_keys": self.total_duplicate_keys,
            "groups": [g.as_dict() for g in self.groups],
        }


def find_duplicates(
    env: Dict[str, Optional[str]],
    *,
    ignore_empty: bool = True,
) -> DuplicateReport:
    """Return a DuplicateReport for *env*.

    Args:
        env: Mapping of key -> value to inspect.
        ignore_empty: When True, keys whose value is ``None`` or ``""`` are
            excluded from duplicate detection (empty values are common and
            rarely meaningful duplicates).
    """
    buckets: Dict[Optional[str], List[str]] = {}

    for key, value in env.items():
        if ignore_empty and not value:
            continue
        buckets.setdefault(value, []).append(key)

    groups = [
        DuplicateGroup(value=val, keys=keys)
        for val, keys in buckets.items()
        if len(keys) > 1
    ]
    # Stable output: sort groups by their first key alphabetically.
    groups.sort(key=lambda g: sorted(g.keys)[0])

    return DuplicateReport(groups=groups)
