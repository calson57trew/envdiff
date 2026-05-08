"""Multi-file comparator: diff one base env against multiple compare envs."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.differ import DiffResult, diff_envs
from envdiff.parser import parse_env_file


@dataclass
class ComparisonEntry:
    """Diff result paired with the name of the compared file."""

    name: str
    result: DiffResult


@dataclass
class MultiComparison:
    """Aggregated comparison of a base env against several targets."""

    base_name: str
    entries: List[ComparisonEntry] = field(default_factory=list)

    def names(self) -> List[str]:
        return [e.name for e in self.entries]

    def clean_names(self) -> List[str]:
        return [e.name for e in self.entries if not _is_dirty(e.result)]

    def dirty_names(self) -> List[str]:
        return [e.name for e in self.entries if _is_dirty(e.result)]

    def get(self, name: str) -> Optional[ComparisonEntry]:
        for entry in self.entries:
            if entry.name == name:
                return entry
        return None

    def as_dict(self) -> Dict:
        return {
            "base": self.base_name,
            "comparisons": [
                {
                    "name": e.name,
                    "missing_in_compare": list(e.result.missing_in_compare),
                    "missing_in_base": list(e.result.missing_in_base),
                    "mismatched": {
                        k: {"base": v[0], "compare": v[1]}
                        for k, v in e.result.mismatched.items()
                    },
                }
                for e in self.entries
            ],
        }


def _is_dirty(result: DiffResult) -> bool:
    return bool(
        result.missing_in_compare
        or result.missing_in_base
        or result.mismatched
    )


def compare_many(
    base_path: Path,
    compare_paths: List[Path],
    check_values: bool = True,
) -> MultiComparison:
    """Parse *base_path* and diff it against every path in *compare_paths*."""
    base_env = parse_env_file(base_path)
    mc = MultiComparison(base_name=base_path.name)
    for cp in compare_paths:
        compare_env = parse_env_file(cp)
        result = diff_envs(base_env, compare_env, check_values=check_values)
        mc.entries.append(ComparisonEntry(name=cp.name, result=result))
    return mc
