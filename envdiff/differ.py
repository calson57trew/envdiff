"""Core diffing logic for comparing parsed .env dictionaries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class DiffResult:
    """Holds the result of comparing two .env files."""

    base_label: str
    compare_label: str
    missing_in_compare: List[str] = field(default_factory=list)
    missing_in_base: List[str] = field(default_factory=list)
    mismatched: Dict[str, tuple] = field(default_factory=dict)

    @property
    def has_differences(self) -> bool:
        return bool(
            self.missing_in_compare or self.missing_in_base or self.mismatched
        )


def diff_envs(
    base: Dict[str, Optional[str]],
    compare: Dict[str, Optional[str]],
    base_label: str = "base",
    compare_label: str = "compare",
    check_values: bool = True,
) -> DiffResult:
    """Compare two parsed .env dictionaries.

    Args:
        base: The reference environment dict.
        compare: The environment dict to compare against base.
        base_label: Human-readable label for the base env.
        compare_label: Human-readable label for the compare env.
        check_values: Whether to report mismatched values (not just missing keys).

    Returns:
        A DiffResult containing all detected differences.
    """
    result = DiffResult(base_label=base_label, compare_label=compare_label)

    base_keys = set(base.keys())
    compare_keys = set(compare.keys())

    result.missing_in_compare = sorted(base_keys - compare_keys)
    result.missing_in_base = sorted(compare_keys - base_keys)

    if check_values:
        common_keys = base_keys & compare_keys
        for key in sorted(common_keys):
            if base[key] != compare[key]:
                result.mismatched[key] = (base[key], compare[key])

    return result
