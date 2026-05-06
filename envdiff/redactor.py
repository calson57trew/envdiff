"""Redacts sensitive values in parsed env dicts before display or export."""

from __future__ import annotations

import re
from typing import Dict, Iterable, Optional

# Default patterns that suggest a key holds a sensitive value
_DEFAULT_SENSITIVE_PATTERNS: list[str] = [
    r".*SECRET.*",
    r".*PASSWORD.*",
    r".*PASSWD.*",
    r".*TOKEN.*",
    r".*API_KEY.*",
    r".*PRIVATE.*",
    r".*CREDENTIAL.*",
]

REDACTED_PLACEHOLDER = "***REDACTED***"


def _compile_patterns(patterns: Iterable[str]) -> list[re.Pattern[str]]:
    """Compile a list of glob-style regex pattern strings."""
    return [re.compile(p, re.IGNORECASE) for p in patterns]


def is_sensitive(
    key: str,
    patterns: Optional[list[re.Pattern[str]]] = None,
) -> bool:
    """Return True if *key* matches any sensitive pattern."""
    compiled = patterns if patterns is not None else _compile_patterns(_DEFAULT_SENSITIVE_PATTERNS)
    return any(p.fullmatch(key) for p in compiled)


def redact_env(
    env: Dict[str, Optional[str]],
    extra_patterns: Optional[list[str]] = None,
    placeholder: str = REDACTED_PLACEHOLDER,
) -> Dict[str, Optional[str]]:
    """Return a copy of *env* with sensitive values replaced by *placeholder*.

    Args:
        env: Mapping of key -> value as returned by ``parse_env_file``.
        extra_patterns: Additional regex patterns (merged with defaults).
        placeholder: Replacement string for sensitive values.

    Returns:
        New dict with sensitive values redacted; ``None`` values are kept as-is.
    """
    all_patterns = list(_DEFAULT_SENSITIVE_PATTERNS)
    if extra_patterns:
        all_patterns.extend(extra_patterns)
    compiled = _compile_patterns(all_patterns)

    return {
        key: (placeholder if (value is not None and is_sensitive(key, compiled)) else value)
        for key, value in env.items()
    }
