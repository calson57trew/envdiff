"""Lint .env files for common issues such as whitespace around '=',
upper-case key convention violations, and duplicate keys."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import List


@dataclass
class LintIssue:
    line_number: int
    key: str | None
    message: str
    severity: str  # "error" | "warning"


@dataclass
class LintResult:
    path: str
    issues: List[LintIssue] = field(default_factory=list)

    @property
    def has_issues(self) -> bool:
        return bool(self.issues)

    @property
    def errors(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> List[LintIssue]:
        return [i for i in self.issues if i.severity == "warning"]


def lint_env_file(path: str | Path) -> LintResult:
    """Analyse *path* and return a :class:`LintResult` with any issues found."""
    path = Path(path)
    result = LintResult(path=str(path))
    seen_keys: dict[str, int] = {}

    with path.open(encoding="utf-8") as fh:
        for lineno, raw_line in enumerate(fh, start=1):
            line = raw_line.rstrip("\n")

            # Skip blanks and comments
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue

            if "=" not in line:
                result.issues.append(
                    LintIssue(lineno, None, "Line has no '=' separator", "error")
                )
                continue

            key_part, _, _value = line.partition("=")

            # Whitespace around the key (before '=')
            if key_part != key_part.strip():
                result.issues.append(
                    LintIssue(
                        lineno,
                        key_part.strip(),
                        "Whitespace around key or '=' separator",
                        "warning",
                    )
                )

            key = key_part.strip()

            # Key should be UPPER_SNAKE_CASE
            if key and not key.replace("_", "").isupper():
                result.issues.append(
                    LintIssue(
                        lineno,
                        key,
                        f"Key '{key}' is not UPPER_SNAKE_CASE",
                        "warning",
                    )
                )

            # Duplicate key detection
            if key in seen_keys:
                result.issues.append(
                    LintIssue(
                        lineno,
                        key,
                        f"Duplicate key '{key}' (first seen on line {seen_keys[key]})",
                        "error",
                    )
                )
            else:
                seen_keys[key] = lineno

    return result
