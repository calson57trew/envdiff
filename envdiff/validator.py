"""Validate .env files against a schema of required and optional keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from fnmatch import fnmatch
from typing import Dict, List, Optional, Set


@dataclass
class ValidationResult:
    """Outcome of validating an env mapping against a schema."""

    missing_required: List[str] = field(default_factory=list)
    unknown_keys: List[str] = field(default_factory=list)
    type_errors: Dict[str, str] = field(default_factory=dict)  # key -> reason

    @property
    def is_valid(self) -> bool:
        return not (self.missing_required or self.type_errors)


@dataclass
class KeySchema:
    """Schema definition for a single key."""

    required: bool = True
    pattern: Optional[str] = None  # regex-free glob pattern for value
    allowed_values: Optional[List[str]] = None


def validate_env(
    env: Dict[str, str],
    schema: Dict[str, KeySchema],
    *,
    allow_unknown: bool = True,
) -> ValidationResult:
    """Validate *env* against *schema*.

    Parameters
    ----------
    env:
        Parsed environment mapping (key -> value).
    schema:
        Mapping of key name to :class:`KeySchema`.
    allow_unknown:
        When *False*, keys present in *env* but absent from *schema* are
        reported in :attr:`ValidationResult.unknown_keys`.
    """
    result = ValidationResult()

    for key, spec in schema.items():
        if spec.required and key not in env:
            result.missing_required.append(key)
            continue

        if key not in env:
            continue

        value = env[key]

        if spec.allowed_values is not None and value not in spec.allowed_values:
            result.type_errors[key] = (
                f"value {value!r} not in allowed set {spec.allowed_values}"
            )
        elif spec.pattern is not None and not fnmatch(value, spec.pattern):
            result.type_errors[key] = (
                f"value {value!r} does not match pattern {spec.pattern!r}"
            )

    if not allow_unknown:
        schema_keys: Set[str] = set(schema.keys())
        result.unknown_keys = sorted(set(env.keys()) - schema_keys)

    return result
