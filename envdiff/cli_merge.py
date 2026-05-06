"""CLI sub-command: ``envdiff merge`` — merge env files and report conflicts."""

from __future__ import annotations

import json
import sys
from argparse import ArgumentParser, Namespace
from pathlib import Path
from typing import List

from envdiff.merger import MergeConflict, MergeResult, merge_envs
from envdiff.parser import parse_env_file


def build_merge_parser(parent: ArgumentParser) -> None:
    """Attach *merge* sub-command to *parent* subparsers."""
    sub = parent.add_subparsers(dest="subcommand")
    p = sub.add_parser("merge", help="Merge multiple .env files into one.")
    p.add_argument("files", nargs="+", metavar="FILE", help=".env files to merge")
    p.add_argument(
        "--prefer",
        metavar="LABEL",
        default=None,
        help="Source label (file path) whose values win on conflict.",
    )
    p.add_argument(
        "--output", "-o", metavar="FILE", default=None,
        help="Write merged result to FILE (default: stdout).",
    )
    p.add_argument(
        "--format", choices=["env", "json"], default="env",
        dest="fmt", help="Output format (default: env).",
    )
    p.add_argument(
        "--exit-code", action="store_true",
        help="Exit with code 1 when conflicts are detected.",
    )


def _render_env(result: MergeResult) -> str:
    lines = [f"{k}={v}" if v is not None else f"{k}=" for k, v in sorted(result.merged.items())]
    return "\n".join(lines) + "\n"


def _render_json(result: MergeResult) -> str:
    payload = {
        "merged": result.merged,
        "conflicts": [
            {"key": c.key, "values": c.values} for c in result.conflicts
        ],
    }
    return json.dumps(payload, indent=2)


def run_merge(args: Namespace) -> int:
    """Execute the merge sub-command; return exit code."""
    sources = []
    for path_str in args.files:
        path = Path(path_str)
        env = parse_env_file(path)
        sources.append((path_str, env))

    result = merge_envs(sources, prefer=args.prefer)

    if result.has_conflicts:
        for conflict in result.conflicts:
            vals = ", ".join(f"{s}={v!r}" for s, v in conflict.values.items())
            print(f"CONFLICT {conflict.key}: {vals}", file=sys.stderr)

    rendered = _render_json(result) if args.fmt == "json" else _render_env(result)

    if args.output:
        Path(args.output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")

    return 1 if (args.exit_code and result.has_conflicts) else 0
