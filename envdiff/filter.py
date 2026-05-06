"""Key filtering utilities — allow/deny-list keys before diffing."""

from __future__ import annotations

import fnmatch
from typing import Dict, Iterable, List, Optional


def _matches_any(key: str, patterns: Iterable[str]) -> bool:
    """Return True if *key* matches any glob pattern in *patterns*."""
    return any(fnmatch.fnmatch(key, pat) for pat in patterns)


def filter_env(
    env: Dict[str, str],
    *,
    include: Optional[List[str]] = None,
    exclude: Optional[List[str]] = None,
) -> Dict[str, str]:
    """Return a filtered copy of *env*.

    Parameters
    ----------
    env:
        Parsed environment mapping ``{key: value}``.
    include:
        Optional list of glob patterns.  When provided, only keys that match
        at least one pattern are kept.
    exclude:
        Optional list of glob patterns.  Keys that match are removed.
        Applied *after* ``include``.

    Returns
    -------
    Filtered ``dict``.

    Raises
    ------
    TypeError:
        If *include* or *exclude* is not a list (or ``None``).
    """
    if include is not None and not isinstance(include, list):
        raise TypeError(f"'include' must be a list or None, got {type(include).__name__!r}")
    if exclude is not None and not isinstance(exclude, list):
        raise TypeError(f"'exclude' must be a list or None, got {type(exclude).__name__!r}")

    result = dict(env)

    if include is not None:
        result = {k: v for k, v in result.items() if _matches_any(k, include)}

    if exclude is not None:
        result = {k: v for k, v in result.items() if not _matches_any(k, exclude)}

    return result
