"""Scores a DiffResult to produce a numeric health metric for an env file."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

from envdiff.differ import DiffResult

# Penalty weights
_MISSING_IN_COMPARE_WEIGHT = 10
_MISSING_IN_BASE_WEIGHT = 5
_MISMATCH_WEIGHT = 3

_MAX_SCORE = 100


@dataclass(frozen=True)
class EnvScore:
    """Numeric health score derived from a DiffResult."""

    score: int          # 0 (worst) – 100 (perfect)
    penalty: int        # total penalty points before clamping
    total_keys: int
    missing_in_compare: int
    missing_in_base: int
    mismatched: int

    @property
    def grade(self) -> str:
        """Letter grade: A (>=90), B (>=75), C (>=60), D (>=40), F (<40)."""
        if self.score >= 90:
            return "A"
        if self.score >= 75:
            return "B"
        if self.score >= 60:
            return "C"
        if self.score >= 40:
            return "D"
        return "F"

    def as_dict(self) -> dict:
        return {
            "score": self.score,
            "grade": self.grade,
            "penalty": self.penalty,
            "total_keys": self.total_keys,
            "missing_in_compare": self.missing_in_compare,
            "missing_in_base": self.missing_in_base,
            "mismatched": self.mismatched,
        }


def score_diff(result: DiffResult) -> EnvScore:
    """Compute a health score for *result*.

    The score starts at 100 and penalties are subtracted per issue,
    scaled by the total number of unique keys so that large files are
    not unfairly penalised for a single problem.
    """
    n_compare = len(result.missing_in_compare)
    n_base = len(result.missing_in_base)
    n_mismatch = len(result.mismatched)

    all_keys = (
        set(result.missing_in_compare)
        | set(result.missing_in_base)
        | set(result.mismatched)
        | set(result.common)
    )
    total = len(all_keys) or 1  # avoid division by zero

    raw_penalty = (
        n_compare * _MISSING_IN_COMPARE_WEIGHT
        + n_base * _MISSING_IN_BASE_WEIGHT
        + n_mismatch * _MISMATCH_WEIGHT
    )

    # Normalise so that one critical issue on a 10-key file hurts more
    # than on a 100-key file.
    normalised_penalty = int((raw_penalty / total) * 10)
    final_score = max(0, _MAX_SCORE - normalised_penalty)

    return EnvScore(
        score=final_score,
        penalty=normalised_penalty,
        total_keys=total,
        missing_in_compare=n_compare,
        missing_in_base=n_base,
        mismatched=n_mismatch,
    )
