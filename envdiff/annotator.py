"""Annotate a parsed env dict with metadata from a DiffResult."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

from envdiff.differ import DiffResult


@dataclass
class AnnotatedEntry:
    """A single env key decorated with diff metadata."""

    key: str
    value: Optional[str]
    status: str  # 'ok' | 'missing_in_compare' | 'missing_in_base' | 'mismatch'
    base_value: Optional[str] = None
    compare_value: Optional[str] = None


@dataclass
class AnnotatedEnv:
    """Full annotation result for a pair of env files."""

    entries: Dict[str, AnnotatedEntry] = field(default_factory=dict)

    def by_status(self, status: str) -> list[AnnotatedEntry]:
        return [e for e in self.entries.values() if e.status == status]


def annotate(base: dict[str, str | None], compare: dict[str, str | None], result: DiffResult) -> AnnotatedEnv:
    """Merge *base* and *compare* env dicts with diff metadata from *result*.

    Args:
        base: Parsed env from the base file.
        compare: Parsed env from the compare file.
        result: A :class:`~envdiff.differ.DiffResult` produced by
            :func:`~envdiff.differ.diff_envs`.

    Returns:
        An :class:`AnnotatedEnv` keyed by every env key seen across both files.
    """
    annotated = AnnotatedEnv()

    missing_in_compare = set(result.missing_in_compare)
    missing_in_base = set(result.missing_in_base)
    mismatched = {k for k, *_ in result.mismatched}

    all_keys = sorted(set(base) | set(compare))

    for key in all_keys:
        base_val = base.get(key)
        cmp_val = compare.get(key)

        if key in missing_in_compare:
            status = "missing_in_compare"
        elif key in missing_in_base:
            status = "missing_in_base"
        elif key in mismatched:
            status = "mismatch"
        else:
            status = "ok"

        annotated.entries[key] = AnnotatedEntry(
            key=key,
            value=base_val if status != "missing_in_base" else cmp_val,
            status=status,
            base_value=base_val,
            compare_value=cmp_val,
        )

    return annotated
