"""Transform env dictionaries by applying a sequence of named operations."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

EnvDict = Dict[str, Optional[str]]
Operation = Callable[[EnvDict], EnvDict]


@dataclass
class TransformResult:
    original: EnvDict
    transformed: EnvDict
    applied: List[str] = field(default_factory=list)

    @property
    def changed_keys(self) -> List[str]:
        all_keys = set(self.original) | set(self.transformed)
        return sorted(k for k in all_keys if self.original.get(k) != self.transformed.get(k))

    @property
    def is_unchanged(self) -> bool:
        return self.original == self.transformed

    def as_dict(self) -> dict:
        return {
            "applied": self.applied,
            "changed_keys": self.changed_keys,
            "is_unchanged": self.is_unchanged,
            "transformed": self.transformed,
        }


def _op_uppercase_keys(env: EnvDict) -> EnvDict:
    return {k.upper(): v for k, v in env.items()}


def _op_strip_values(env: EnvDict) -> EnvDict:
    return {k: (v.strip() if isinstance(v, str) else v) for k, v in env.items()}


def _op_remove_empty(env: EnvDict) -> EnvDict:
    return {k: v for k, v in env.items() if v not in (None, "")}


def _op_quote_spaces(env: EnvDict) -> EnvDict:
    result: EnvDict = {}
    for k, v in env.items():
        if isinstance(v, str) and " " in v and not (v.startswith('"') and v.endswith('"')):
            result[k] = f'"{v}"'
        else:
            result[k] = v
    return result


_BUILTIN_OPS: Dict[str, Operation] = {
    "uppercase_keys": _op_uppercase_keys,
    "strip_values": _op_strip_values,
    "remove_empty": _op_remove_empty,
    "quote_spaces": _op_quote_spaces,
}


def available_operations() -> List[str]:
    return sorted(_BUILTIN_OPS.keys())


def transform_env(env: EnvDict, operations: List[str]) -> TransformResult:
    """Apply named operations in order and return a TransformResult."""
    unknown = [op for op in operations if op not in _BUILTIN_OPS]
    if unknown:
        raise ValueError(f"Unknown operation(s): {', '.join(unknown)}")

    current = dict(env)
    applied: List[str] = []
    for name in operations:
        current = _BUILTIN_OPS[name](current)
        applied.append(name)

    return TransformResult(original=dict(env), transformed=current, applied=applied)
