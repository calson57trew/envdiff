"""Export diff or merged results to various file formats."""

from __future__ import annotations

import json
from enum import Enum
from pathlib import Path
from typing import Dict, Optional

from envdiff.differ import DiffResult


class ExportFormat(str, Enum):
    DOTENV = "dotenv"
    JSON = "json"
    MARKDOWN = "markdown"


def _to_dotenv(env: Dict[str, Optional[str]]) -> str:
    """Render a key/value mapping as a .env file string."""
    lines = []
    for key in sorted(env):
        value = env[key] if env[key] is not None else ""
        # Quote values that contain spaces or special characters
        if any(ch in value for ch in (" ", "\t", "#", "'", '"')):
            value = f'"{value}"'
        lines.append(f"{key}={value}")
    return "\n".join(lines) + ("\n" if lines else "")


def _to_json(env: Dict[str, Optional[str]]) -> str:
    """Render a key/value mapping as a JSON string."""
    return json.dumps({k: env[k] for k in sorted(env)}, indent=2) + "\n"


def _to_markdown(result: DiffResult) -> str:
    """Render a DiffResult as a Markdown summary table."""
    lines = [
        "# envdiff Report",
        "",
        "| Key | Status | Base Value | Compare Value |",
        "|-----|--------|------------|---------------|" ,
    ]
    for key in sorted(result.missing_in_compare):
        lines.append(f"| `{key}` | missing in compare | `{result.base.get(key)}` | — |")
    for key in sorted(result.missing_in_base):
        lines.append(f"| `{key}` | missing in base | — | `{result.compare.get(key)}` |")
    for key in sorted(result.mismatched):
        base_val = result.base.get(key)
        cmp_val = result.compare.get(key)
        lines.append(f"| `{key}` | mismatch | `{base_val}` | `{cmp_val}` |")
    if not (result.missing_in_compare or result.missing_in_base or result.mismatched):
        lines.append("| — | no differences | — | — |")
    return "\n".join(lines) + "\n"


def export_diff(
    result: DiffResult,
    fmt: ExportFormat,
    output_path: Optional[Path] = None,
) -> str:
    """Serialise *result* in the requested format.

    If *output_path* is given the content is also written to that file.
    Returns the serialised string regardless.
    """
    if fmt == ExportFormat.DOTENV:
        # Export the base env as a .env file (useful for bootstrapping)
        content = _to_dotenv(result.base)
    elif fmt == ExportFormat.JSON:
        payload = {
            "missing_in_compare": sorted(result.missing_in_compare),
            "missing_in_base": sorted(result.missing_in_base),
            "mismatched": sorted(result.mismatched),
        }
        content = json.dumps(payload, indent=2) + "\n"
    elif fmt == ExportFormat.MARKDOWN:
        content = _to_markdown(result)
    else:
        raise ValueError(f"Unsupported export format: {fmt}")

    if output_path is not None:
        output_path.write_text(content, encoding="utf-8")

    return content
