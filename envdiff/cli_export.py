"""CLI sub-command: envdiff export — write diff results to a file."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.exporter import ExportFormat, export_diff
from envdiff.parser import parse_env_file


def build_export_parser(subparsers: "argparse._SubParsersAction") -> argparse.ArgumentParser:  # type: ignore[type-arg]
    """Register the *export* sub-command on *subparsers*."""
    p = subparsers.add_parser(
        "export",
        help="Export diff results to dotenv, JSON, or Markdown.",
    )
    p.add_argument("base", metavar="BASE", help="Base .env file.")
    p.add_argument("compare", metavar="COMPARE", help="Compare .env file.")
    p.add_argument(
        "-f",
        "--format",
        choices=[f.value for f in ExportFormat],
        default=ExportFormat.MARKDOWN.value,
        help="Output format (default: markdown).",
    )
    p.add_argument(
        "-o",
        "--output",
        metavar="FILE",
        help="Write output to FILE instead of stdout.",
    )
    p.add_argument(
        "--check-values",
        action="store_true",
        default=False,
        help="Include value mismatches in the diff (default: keys only).",
    )
    return p


def run_export(args: argparse.Namespace) -> int:
    """Execute the export sub-command. Returns an exit code."""
    try:
        base_env = parse_env_file(Path(args.base))
        compare_env = parse_env_file(Path(args.compare))
    except FileNotFoundError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    result = diff_envs(base_env, compare_env, check_values=args.check_values)
    fmt = ExportFormat(args.format)
    output_path = Path(args.output) if args.output else None

    content = export_diff(result, fmt, output_path=output_path)

    if output_path is None:
        print(content, end="")
    else:
        print(f"Exported to {output_path}", file=sys.stderr)

    return 0


def main(argv: list[str] | None = None) -> int:  # pragma: no cover
    """Standalone entry point for the export command."""
    parser = argparse.ArgumentParser(prog="envdiff-export")
    subs = parser.add_subparsers(dest="command")
    build_export_parser(subs)
    args = parser.parse_args(argv)
    if args.command is None:
        parser.print_help()
        return 1
    return run_export(args)
