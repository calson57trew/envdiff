"""Groups env keys by a shared prefix (e.g. DB_, AWS_, APP_)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class KeyGroup:
    prefix: str
    keys: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"prefix": self.prefix, "keys": sorted(self.keys), "count": len(self.keys)}


@dataclass
class GroupReport:
    groups: Dict[str, KeyGroup] = field(default_factory=dict)
    ungrouped: List[str] = field(default_factory=list)

    @property
    def total_groups(self) -> int:
        return len(self.groups)

    @property
    def total_ungrouped(self) -> int:
        return len(self.ungrouped)

    def as_dict(self) -> dict:
        return {
            "groups": {p: g.as_dict() for p, g in sorted(self.groups.items())},
            "ungrouped": sorted(self.ungrouped),
            "total_groups": self.total_groups,
            "total_ungrouped": self.total_ungrouped,
        }


def _extract_prefix(key: str, sep: str = "_") -> Optional[str]:
    """Return the portion before the first separator, or None if no separator."""
    idx = key.find(sep)
    if idx <= 0:
        return None
    return key[:idx]


def group_env(
    env: Dict[str, Optional[str]],
    sep: str = "_",
    min_group_size: int = 1,
) -> GroupReport:
    """Group env keys by prefix.

    Keys whose prefix appears fewer than *min_group_size* times are placed in
    ``ungrouped`` instead.
    """
    prefix_map: Dict[str, KeyGroup] = {}
    for key in env:
        prefix = _extract_prefix(key, sep)
        if prefix is None:
            continue
        if prefix not in prefix_map:
            prefix_map[prefix] = KeyGroup(prefix=prefix)
        prefix_map[prefix].keys.append(key)

    report = GroupReport()
    for prefix, group in prefix_map.items():
        if len(group.keys) >= min_group_size:
            report.groups[prefix] = group
        else:
            report.ungrouped.extend(group.keys)

    # keys that had no separator at all
    for key in env:
        if _extract_prefix(key, sep) is None:
            report.ungrouped.append(key)

    return report
