"""Apply a diff result to a .env file, adding or updating keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional

from envdiff.differ import DiffResult


@dataclass
class PatchResult:
    patched: Dict[str, Optional[str]] = field(default_factory=dict)
    added: List[str] = field(default_factory=list)
    updated: List[str] = field(default_factory=list)
    skipped: List[str] = field(default_factory=list)


def patch_env(
    base: Dict[str, Optional[str]],
    diff: DiffResult,
    *,
    add_missing: bool = True,
    fix_mismatched: bool = False,
    skip_keys: Optional[List[str]] = None,
) -> PatchResult:
    """Return a new env dict with changes from *diff* applied.

    Parameters
    ----------
    base:           The original env mapping to patch.
    diff:           DiffResult describing gaps between base and compare.
    add_missing:    When True, keys missing in base are added from compare.
    fix_mismatched: When True, mismatched values in base are overwritten.
    skip_keys:      Keys to leave untouched regardless of other flags.
    """
    skip = set(skip_keys or [])
    result = PatchResult(patched=dict(base))

    if add_missing:
        for key, value in diff.missing_in_base.items():
            if key in skip:
                result.skipped.append(key)
                continue
            result.patched[key] = value
            result.added.append(key)

    if fix_mismatched:
        for key, (_, compare_val) in diff.mismatched.items():
            if key in skip:
                result.skipped.append(key)
                continue
            result.patched[key] = compare_val
            result.updated.append(key)

    return result


def write_patched_env(env: Dict[str, Optional[str]], path: Path) -> None:
    """Write *env* mapping to *path* in .env format."""
    lines: List[str] = []
    for key in sorted(env):
        value = env[key] if env[key] is not None else ""
        if " " in value or "\t" in value:
            lines.append(f'{key}="{value}"')
        else:
            lines.append(f"{key}={value}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
