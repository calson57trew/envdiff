"""Build a dependency graph of .env key references.

A key A depends on key B if A's value contains ${B} or $B.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set

_REF_RE = re.compile(r"\$\{?(\w+)\}?")


@dataclass
class GraphNode:
    key: str
    depends_on: FrozenSet[str] = field(default_factory=frozenset)
    depended_by: FrozenSet[str] = field(default_factory=frozenset)

    def as_dict(self) -> dict:
        return {
            "key": self.key,
            "depends_on": sorted(self.depends_on),
            "depended_by": sorted(self.depended_by),
        }


@dataclass
class EnvGraph:
    nodes: Dict[str, GraphNode] = field(default_factory=dict)

    def get(self, key: str) -> Optional[GraphNode]:
        return self.nodes.get(key)

    def roots(self) -> List[str]:
        """Keys with no dependencies (not referencing any other key)."""
        return sorted(k for k, n in self.nodes.items() if not n.depends_on)

    def leaves(self) -> List[str]:
        """Keys that no other key depends on."""
        return sorted(k for k, n in self.nodes.items() if not n.depended_by)

    def as_dict(self) -> dict:
        return {k: n.as_dict() for k, n in sorted(self.nodes.items())}


def _extract_refs(value: Optional[str]) -> Set[str]:
    if not value:
        return set()
    return set(_REF_RE.findall(value))


def build_graph(env: Dict[str, Optional[str]]) -> EnvGraph:
    """Build a reference graph from a parsed env mapping."""
    depends: Dict[str, Set[str]] = {}
    depended_by: Dict[str, Set[str]] = {k: set() for k in env}

    for key, value in env.items():
        refs = _extract_refs(value) & env.keys()  # only internal refs
        depends[key] = refs

    for key, refs in depends.items():
        for ref in refs:
            depended_by.setdefault(ref, set()).add(key)

    nodes = {
        key: GraphNode(
            key=key,
            depends_on=frozenset(depends.get(key, set())),
            depended_by=frozenset(depended_by.get(key, set())),
        )
        for key in env
    }
    return EnvGraph(nodes=nodes)
