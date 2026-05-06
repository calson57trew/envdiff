"""Formats and outputs DiffResult reports to various targets."""

from __future__ import annotations

from enum import Enum
from typing import TextIO
import sys

from envdiff.differ import DiffResult


class OutputFormat(str, Enum):
    TEXT = "text"
    JSON = "json"
    GITHUB = "github"


def _format_text(result: DiffResult, base_name: str, compare_name: str) -> str:
    lines: list[str] = []

    if result.missing_in_compare:
        lines.append(f"Missing in '{compare_name}':")
        for key in sorted(result.missing_in_compare):
            lines.append(f"  - {key}")

    if result.missing_in_base:
        lines.append(f"Missing in '{base_name}':")
        for key in sorted(result.missing_in_base):
            lines.append(f"  - {key}")

    if result.mismatched:
        lines.append("Mismatched values:")
        for key in sorted(result.mismatched):
            base_val, cmp_val = result.mismatched[key]
            lines.append(f"  ~ {key}: '{base_val}' -> '{cmp_val}'")

    if not lines:
        lines.append("No differences found.")

    return "\n".join(lines)


def _format_json(result: DiffResult, base_name: str, compare_name: str) -> str:
    import json

    data = {
        "base": base_name,
        "compare": compare_name,
        "missing_in_compare": sorted(result.missing_in_compare),
        "missing_in_base": sorted(result.missing_in_base),
        "mismatched": {
            k: {"base": v[0], "compare": v[1]}
            for k, v in sorted(result.mismatched.items())
        },
    }
    return json.dumps(data, indent=2)


def _format_github(result: DiffResult, base_name: str, compare_name: str) -> str:
    lines: list[str] = []

    for key in sorted(result.missing_in_compare):
        lines.append(f"::warning::Key '{key}' missing in {compare_name}")
    for key in sorted(result.missing_in_base):
        lines.append(f"::warning::Key '{key}' missing in {base_name}")
    for key in sorted(result.mismatched):
        lines.append(f"::error::Key '{key}' has mismatched values between {base_name} and {compare_name}")

    if not lines:
        lines.append("::notice::No differences found between env files")

    return "\n".join(lines)


def render(
    result: DiffResult,
    base_name: str = "base",
    compare_name: str = "compare",
    fmt: OutputFormat = OutputFormat.TEXT,
    out: TextIO = sys.stdout,
) -> None:
    """Render a DiffResult to *out* in the requested format."""
    formatters = {
        OutputFormat.TEXT: _format_text,
        OutputFormat.JSON: _format_json,
        OutputFormat.GITHUB: _format_github,
    }
    text = formatters[fmt](result, base_name, compare_name)
    out.write(text + "\n")
