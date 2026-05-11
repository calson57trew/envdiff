"""Key ignore-list support: load, match, and filter diff results by ignored keys."""
from __future__ import annotations

import fnmatch
import json
from pathlib import Path
from typing import Iterable, Sequence

from envdiff.differ import DiffResult


def load_ignore_list(path: str | Path) -> list[str]:
    """Load an ignore list from a JSON file (list of key patterns) or a plain
    text file (one pattern per line, # comments stripped)."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Ignore list not found: {path}")
    text = p.read_text(encoding="utf-8")
    if p.suffix == ".json":
        data = json.loads(text)
        if not isinstance(data, list):
            raise ValueError("JSON ignore list must be a top-level array of strings.")
        return [str(item) for item in data]
    # plain text
    patterns: list[str] = []
    for line in text.splitlines():
        stripped = line.split("#", 1)[0].strip()
        if stripped:
            patterns.append(stripped)
    return patterns


def is_ignored(key: str, patterns: Iterable[str]) -> bool:
    """Return True if *key* matches any glob pattern in *patterns*."""
    return any(fnmatch.fnmatch(key, p) for p in patterns)


def apply_ignore(result: DiffResult, patterns: Sequence[str]) -> DiffResult:
    """Return a new DiffResult with all ignored keys removed from every set."""
    if not patterns:
        return result

    def _filter(keys: set[str]) -> set[str]:
        return {k for k in keys if not is_ignored(k, patterns)}

    return DiffResult(
        missing_in_compare=_filter(result.missing_in_compare),
        missing_in_base=_filter(result.missing_in_base),
        mismatched={
            k: v
            for k, v in result.mismatched.items()
            if not is_ignored(k, patterns)
        },
    )
