"""Profile an env file: count keys, detect duplicates, measure value lengths."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from envdiff.parser import parse_env_file


@dataclass
class EnvProfile:
    total_keys: int = 0
    empty_values: List[str] = field(default_factory=list)
    duplicate_keys: List[str] = field(default_factory=list)
    longest_key: Optional[str] = None
    longest_value_key: Optional[str] = None
    avg_value_length: float = 0.0
    key_lengths: Dict[str, int] = field(default_factory=dict)
    value_lengths: Dict[str, int] = field(default_factory=dict)


def _find_duplicates(path: str) -> List[str]:
    """Re-parse raw lines to detect duplicate key declarations."""
    seen: Dict[str, int] = {}
    duplicates: List[str] = []
    try:
        with open(path, "r", encoding="utf-8") as fh:
            for raw_line in fh:
                line = raw_line.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                key = line.split("=", 1)[0].strip()
                seen[key] = seen.get(key, 0) + 1
    except OSError:
        pass
    for key, count in seen.items():
        if count > 1:
            duplicates.append(key)
    return sorted(duplicates)


def profile_env(path: str) -> EnvProfile:
    """Build an :class:`EnvProfile` for the .env file at *path*."""
    env = parse_env_file(path)
    duplicates = _find_duplicates(path)

    profile = EnvProfile()
    profile.total_keys = len(env)
    profile.duplicate_keys = duplicates

    if not env:
        return profile

    for key, value in env.items():
        profile.key_lengths[key] = len(key)
        profile.value_lengths[key] = len(value) if value else 0
        if value is None or value == "":
            profile.empty_values.append(key)

    profile.longest_key = max(profile.key_lengths, key=profile.key_lengths.get)
    profile.longest_value_key = max(profile.value_lengths, key=profile.value_lengths.get)

    total_value_len = sum(profile.value_lengths.values())
    profile.avg_value_length = total_value_len / len(env)

    profile.empty_values.sort()
    return profile
