"""Normalizes .env key/value pairs for consistent comparison.

Handles case folding, whitespace trimming, and common value
normalization (e.g. boolean synonyms, empty-string variants).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional

# Values that should be treated as logically equivalent to "true"
_TRUE_SYNONYMS: frozenset[str] = frozenset({"1", "yes", "on", "true"})
# Values that should be treated as logically equivalent to "false"
_FALSE_SYNONYMS: frozenset[str] = frozenset({"0", "no", "off", "false"})


@dataclass(frozen=True)
class NormalizeOptions:
    """Controls which normalizations are applied."""

    fold_keys: bool = True          # lowercase all keys
    strip_values: bool = True       # strip leading/trailing whitespace from values
    fold_booleans: bool = False     # collapse boolean synonyms to "true"/"false"
    empty_as_none: bool = False     # treat empty string values as None


def _normalize_value(
    value: Optional[str],
    opts: NormalizeOptions,
) -> Optional[str]:
    if value is None:
        return None

    if opts.strip_values:
        value = value.strip()

    if opts.empty_as_none and value == "":
        return None

    if opts.fold_booleans:
        lower = value.lower()
        if lower in _TRUE_SYNONYMS:
            return "true"
        if lower in _FALSE_SYNONYMS:
            return "false"

    return value


def normalize_env(
    env: Dict[str, Optional[str]],
    opts: Optional[NormalizeOptions] = None,
) -> Dict[str, Optional[str]]:
    """Return a new dict with keys and values normalized per *opts*.

    Args:
        env:  Parsed environment mapping (key -> value or None).
        opts: Normalization options; defaults to :class:`NormalizeOptions`.

    Returns:
        A new dict with normalized keys and values.
    """
    if opts is None:
        opts = NormalizeOptions()

    result: Dict[str, Optional[str]] = {}
    for key, value in env.items():
        normalized_key = key.lower() if opts.fold_keys else key
        normalized_value = _normalize_value(value, opts)
        result[normalized_key] = normalized_value
    return result
