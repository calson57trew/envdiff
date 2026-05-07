"""Timeline diff: compare a sequence of snapshots and track changes over time."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.snapshotter import load_snapshot


@dataclass
class TimelineEntry:
    """A single step in the timeline, comparing two consecutive snapshots."""

    from_label: Optional[str]
    to_label: Optional[str]
    from_path: str
    to_path: str
    diff: DiffResult

    @property
    def has_changes(self) -> bool:
        return bool(
            self.diff.missing_in_compare
            or self.diff.missing_in_base
            or self.diff.mismatched
        )


@dataclass
class DiffTimeline:
    """Ordered sequence of diffs across multiple snapshots."""

    entries: List[TimelineEntry] = field(default_factory=list)

    @property
    def total_steps(self) -> int:
        return len(self.entries)

    @property
    def steps_with_changes(self) -> int:
        return sum(1 for e in self.entries if e.has_changes)

    def as_dict(self) -> Dict:
        return {
            "total_steps": self.total_steps,
            "steps_with_changes": self.steps_with_changes,
            "entries": [
                {
                    "from_label": e.from_label,
                    "to_label": e.to_label,
                    "from_path": e.from_path,
                    "to_path": e.to_path,
                    "has_changes": e.has_changes,
                    "missing_in_compare": sorted(e.diff.missing_in_compare),
                    "missing_in_base": sorted(e.diff.missing_in_base),
                    "mismatched": sorted(e.diff.mismatched),
                }
                for e in self.entries
            ],
        }


def build_timeline(
    snapshot_paths: List[str],
    check_values: bool = True,
) -> DiffTimeline:
    """Load consecutive snapshots and produce a DiffTimeline.

    Args:
        snapshot_paths: Ordered list of snapshot file paths (oldest first).
        check_values: Whether to compare values or only keys.

    Returns:
        A DiffTimeline with one entry per consecutive pair.
    """
    if len(snapshot_paths) < 2:
        return DiffTimeline()

    entries: List[TimelineEntry] = []
    snapshots = [load_snapshot(p) for p in snapshot_paths]

    for i in range(len(snapshots) - 1):
        snap_a = snapshots[i]
        snap_b = snapshots[i + 1]
        env_a = snap_a.get("env", {})
        env_b = snap_b.get("env", {})
        diff = diff_envs(env_a, env_b, check_values=check_values)
        entries.append(
            TimelineEntry(
                from_label=snap_a.get("label"),
                to_label=snap_b.get("label"),
                from_path=snapshot_paths[i],
                to_path=snapshot_paths[i + 1],
                diff=diff,
            )
        )

    return DiffTimeline(entries=entries)
