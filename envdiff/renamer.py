"""Rename keys across a parsed env dict, with optional dry-run support."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class RenameResult:
    """Outcome of a rename operation."""

    renamed: Dict[str, str] = field(default_factory=dict)   # old_key -> new_key
    skipped: List[str] = field(default_factory=list)         # old keys not found
    output: Dict[str, Optional[str]] = field(default_factory=dict)  # final env


def has_renames(result: RenameResult) -> bool:
    """Return True when at least one key was successfully renamed."""
    return bool(result.renamed)


def rename_keys(
    env: Dict[str, Optional[str]],
    mapping: Dict[str, str],
    *,
    overwrite: bool = False,
) -> RenameResult:
    """Rename keys in *env* according to *mapping* (old -> new).

    Parameters
    ----------
    env:
        Parsed environment dict as returned by ``parse_env_file``.
    mapping:
        Dict of ``{old_key: new_key}`` pairs to apply.
    overwrite:
        When *True*, silently replace an existing key that shares the new
        name.  When *False* (default) the rename is skipped and the old key
        is added to ``RenameResult.skipped``.
    """
    output: Dict[str, Optional[str]] = dict(env)
    renamed: Dict[str, str] = {}
    skipped: List[str] = []

    for old_key, new_key in mapping.items():
        if old_key not in output:
            skipped.append(old_key)
            continue

        if new_key in output and not overwrite:
            skipped.append(old_key)
            continue

        value = output.pop(old_key)
        output[new_key] = value
        renamed[old_key] = new_key

    return RenameResult(renamed=renamed, skipped=skipped, output=output)
