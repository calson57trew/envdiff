"""Command-line interface for envdiff."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs, has_differences
from envdiff.parser import parse_env_file
from envdiff.reporter import OutputFormat, render


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff",
        description="Compare .env files across environments.",
    )
    p.add_argument("base", type=Path, help="Base .env file")
    p.add_argument("compare", type=Path, help="Comparison .env file")
    p.add_argument(
        "--format",
        "-f",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--no-values",
        action="store_true",
        default=False,
        help="Only check for missing keys, ignore value differences",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if differences are found",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.base.exists():
        print(f"envdiff: error: base file not found: {args.base}", file=sys.stderr)
        return 2
    if not args.compare.exists():
        print(f"envdiff: error: compare file not found: {args.compare}", file=sys.stderr)
        return 2

    base_env = parse_env_file(args.base)
    compare_env = parse_env_file(args.compare)

    result = diff_envs(base_env, compare_env, check_values=not args.no_values)

    render(
        result,
        base_name=str(args.base),
        compare_name=str(args.compare),
        fmt=OutputFormat(args.fmt),
    )

    if args.exit_code and has_differences(result):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
