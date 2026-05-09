"""Baseline comparison: pin a reference env and detect drift over time."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.parser import parse_env_file


@dataclass
class BaselineEntry:
    key: str
    expected: Optional[str]
    actual: Optional[str]
    status: str  # "ok" | "drifted" | "added" | "removed"

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "expected": self.expected,
            "actual": self.actual,
            "status": self.status,
        }


@dataclass
class BaselineReport:
    baseline_path: str
    target_path: str
    entries: List[BaselineEntry] = field(default_factory=list)

    @property
    def is_clean(self) -> bool:
        return all(e.status == "ok" for e in self.entries)

    @property
    def drift_count(self) -> int:
        return sum(1 for e in self.entries if e.status != "ok")

    def as_dict(self) -> dict:
        return {
            "baseline": self.baseline_path,
            "target": self.target_path,
            "is_clean": self.is_clean,
            "drift_count": self.drift_count,
            "entries": [e.as_dict() for e in self.entries],
        }


def save_baseline(env: Dict[str, Optional[str]], path: Path) -> None:
    """Persist an env dict as a JSON baseline file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        json.dump(env, fh, indent=2, sort_keys=True)


def load_baseline(path: Path) -> Dict[str, Optional[str]]:
    """Load a previously saved baseline JSON file."""
    with path.open("r", encoding="utf-8") as fh:
        return json.load(fh)


def compare_to_baseline(
    baseline_path: Path,
    target_path: Path,
    check_values: bool = True,
) -> BaselineReport:
    """Compare a live .env file against a pinned baseline."""
    baseline_env = load_baseline(baseline_path)
    target_env = parse_env_file(target_path)

    result: DiffResult = diff_envs(
        baseline_env, target_env, check_values=check_values
    )

    entries: List[BaselineEntry] = []

    for key in sorted(
        set(baseline_env) | set(target_env)
    ):
        expected = baseline_env.get(key)
        actual = target_env.get(key)

        if key in result.missing_in_compare:
            status = "removed"
        elif key in result.missing_in_base:
            status = "added"
        elif key in result.mismatched:
            status = "drifted"
        else:
            status = "ok"

        entries.append(
            BaselineEntry(
                key=key,
                expected=expected,
                actual=actual,
                status=status,
            )
        )

    return BaselineReport(
        baseline_path=str(baseline_path),
        target_path=str(target_path),
        entries=entries,
    )
