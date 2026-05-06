"""Merge multiple .env files into a unified baseline with conflict tracking."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass
class MergeConflict:
    """Represents a key whose value differs across merged sources."""

    key: str
    values: Dict[str, Optional[str]]  # source_label -> value

    @property
    def sources(self) -> List[str]:
        return list(self.values.keys())


@dataclass
class MergeResult:
    """Outcome of merging two or more env mappings."""

    merged: Dict[str, Optional[str]] = field(default_factory=dict)
    conflicts: List[MergeConflict] = field(default_factory=list)

    @property
    def has_conflicts(self) -> bool:
        return len(self.conflicts) > 0


def merge_envs(
    sources: List[Tuple[str, Dict[str, Optional[str]]]],
    prefer: Optional[str] = None,
) -> MergeResult:
    """Merge *sources* (list of (label, env_dict) pairs) into a single mapping.

    When a key appears in multiple sources with different values a
    :class:`MergeConflict` is recorded.  If *prefer* names a source label its
    value wins silently; otherwise the first source's value is kept.
    """
    if not sources:
        return MergeResult()

    merged: Dict[str, Optional[str]] = {}
    # key -> {label: value}
    seen: Dict[str, Dict[str, Optional[str]]] = {}

    for label, env in sources:
        for key, value in env.items():
            if key not in seen:
                seen[key] = {}
                merged[key] = value
            seen[key][label] = value

    conflicts: List[MergeConflict] = []
    for key, label_values in seen.items():
        unique_values = set(label_values.values())
        if len(unique_values) > 1:
            conflicts.append(MergeConflict(key=key, values=label_values))
            # Apply preference if requested
            if prefer and prefer in label_values:
                merged[key] = label_values[prefer]

    return MergeResult(merged=merged, conflicts=conflicts)
