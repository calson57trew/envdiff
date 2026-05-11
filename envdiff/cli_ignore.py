"""CLI sub-command: diff two .env files with an ignore list applied."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs, has_differences
from envdiff.ignorer import apply_ignore, load_ignore_list
from envdiff.parser import parse_env_file
from envdiff.reporter import OutputFormat, render


def build_ignore_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        description="Diff two .env files, skipping keys matched by an ignore list.",
    )
    if parent is not None:
        parser = parent.add_parser("ignore", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-ignore", **kwargs)

    parser.add_argument("base", help="Base .env file.")
    parser.add_argument("compare", help="Comparison .env file.")
    parser.add_argument(
        "--ignore-file",
        metavar="FILE",
        help="Path to a .txt or .json file containing key patterns to ignore.",
    )
    parser.add_argument(
        "--ignore",
        metavar="PATTERN",
        action="append",
        default=[],
        help="Glob pattern to ignore (repeatable). Combined with --ignore-file.",
    )
    parser.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        help="Hide values in output.",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when differences are found.",
    )
    return parser


def run_ignore(args: argparse.Namespace) -> int:
    base_env = parse_env_file(args.base)
    compare_env = parse_env_file(args.compare)

    result = diff_envs(base_env, compare_env)

    patterns: list[str] = list(args.ignore)
    if args.ignore_file:
        try:
            patterns.extend(load_ignore_list(args.ignore_file))
        except (FileNotFoundError, ValueError) as exc:
            print(f"error: {exc}", file=sys.stderr)
            return 2

    result = apply_ignore(result, patterns)

    fmt = OutputFormat(args.format)
    render(result, fmt=fmt, show_values=not args.no_values)

    if args.exit_code and has_differences(result):
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_ignore_parser()
    args = parser.parse_args()
    sys.exit(run_ignore(args))


if __name__ == "__main__":  # pragma: no cover
    main()
