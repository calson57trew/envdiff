"""CLI sub-command: summarize a diff between two .env files."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.summarizer import summarize


def build_summary_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        prog="envdiff summary",
        description="Print a high-level summary of differences between two .env files.",
    )
    if parent is not None:
        parser = parent.add_parser("summary", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("compare", help="Comparison .env file")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when differences are found",
    )
    return parser


def _render_text(summary_data: dict) -> str:  # type: ignore[type-arg]
    lines = [
        f"Total keys   : {summary_data['total_keys']}",
        f"Identical    : {summary_data['identical']}",
        f"Missing (cmp): {summary_data['missing_in_compare']}",
        f"Missing (base): {summary_data['missing_in_base']}",
        f"Mismatched   : {summary_data['mismatched']}",
        f"Total issues : {summary_data['total_issues']}",
    ]
    return "\n".join(lines)


def run_summary(args: argparse.Namespace) -> int:
    base_env = parse_env_file(Path(args.base))
    cmp_env = parse_env_file(Path(args.compare))
    result = diff_envs(base_env, cmp_env)
    summary = summarize(result)
    data = summary.as_dict()

    if args.fmt == "json":
        print(json.dumps(data, indent=2))
    else:
        print(_render_text(data))

    if args.exit_code and not summary.is_clean:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_summary_parser()
    args = parser.parse_args()
    sys.exit(run_summary(args))


if __name__ == "__main__":  # pragma: no cover
    main()
