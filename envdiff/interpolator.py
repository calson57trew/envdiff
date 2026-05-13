"""Resolve variable references within an env mapping.

Supports ``$VAR`` and ``${VAR}`` syntax.  References that cannot be
resolved are left as-is (or replaced with an empty string when
``strict=False`` and the key is absent).
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

_REF_RE = re.compile(r"\$\{([^}]+)\}|\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass
class InterpolationResult:
    resolved: Dict[str, Optional[str]]
    unresolved_refs: List[str] = field(default_factory=list)  # keys that had missing refs


def _resolve_value(
    value: str,
    env: Dict[str, Optional[str]],
    unresolved: List[str],
    key: str,
    strict: bool,
) -> str:
    def _replace(m: re.Match) -> str:  # type: ignore[type-arg]
        ref_name = m.group(1) or m.group(2)
        if ref_name in env and env[ref_name] is not None:
            return env[ref_name]  # type: ignore[return-value]
        if strict:
            return m.group(0)  # leave original token
        unresolved.append(key)
        return ""

    return _REF_RE.sub(_replace, value)


def interpolate_env(
    env: Dict[str, Optional[str]],
    *,
    strict: bool = True,
) -> InterpolationResult:
    """Return a new mapping with ``$VAR`` / ``${VAR}`` references expanded.

    Parameters
    ----------
    env:
        Flat key/value mapping (values may be ``None``).
    strict:
        When *True* (default) unresolvable references are left unchanged.
        When *False* they are replaced with an empty string and the key is
        recorded in ``InterpolationResult.unresolved_refs``.
    """
    unresolved: List[str] = []
    resolved: Dict[str, Optional[str]] = {}

    for key, value in env.items():
        if value is None or "$" not in value:
            resolved[key] = value
        else:
            resolved[key] = _resolve_value(value, env, unresolved, key, strict)

    return InterpolationResult(resolved=resolved, unresolved_refs=list(set(unresolved)))
