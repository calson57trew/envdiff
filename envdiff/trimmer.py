"""trimmer.py – Remove keys from an env mapping by exact match or glob pattern.

Provides a simple way to strip unwanted keys before export, merge, or diff.
"""
from __future__ import annotations

import fnmatch
from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class TrimResult:
    """Outcome of a trim operation."""

    env: Dict[str, Optional[str]]
    removed_keys: List[str] = field(default_factory=list)

    @property
    def total_removed(self) -> int:
        return len(self.removed_keys)

    @property
    def is_unchanged(self) -> bool:
        return self.total_removed == 0

    def as_dict(self) -> dict:
        return {
            "env": self.env,
            "removed_keys": sorted(self.removed_keys),
            "total_removed": self.total_removed,
        }


def _matches_any(key: str, patterns: List[str]) -> bool:
    """Return True if *key* matches at least one pattern (exact or glob)."""
    for pattern in patterns:
        if key == pattern or fnmatch.fnmatch(key, pattern):
            return True
    return False


def trim_env(
    env: Dict[str, Optional[str]],
    patterns: List[str],
) -> TrimResult:
    """Remove keys matching any of *patterns* from *env*.

    Args:
        env:      Source environment mapping.
        patterns: List of exact key names or glob patterns to remove.

    Returns:
        A :class:`TrimResult` with the filtered env and the list of removed keys.
    """
    if not patterns:
        return TrimResult(env=dict(env), removed_keys=[])

    kept: Dict[str, Optional[str]] = {}
    removed: List[str] = []

    for key, value in env.items():
        if _matches_any(key, patterns):
            removed.append(key)
        else:
            kept[key] = value

    return TrimResult(env=kept, removed_keys=removed)
