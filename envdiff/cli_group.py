"""CLI entry-point for the grouper feature."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.grouper import group_env
from envdiff.parser import parse_env_file


def build_group_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-group",
        description="Group .env keys by shared prefix.",
    )
    p.add_argument("file", help="Path to the .env file to analyse.")
    p.add_argument(
        "--sep",
        default="_",
        metavar="SEP",
        help="Separator character used to detect prefixes (default: '_').",
    )
    p.add_argument(
        "--min-size",
        type=int,
        default=1,
        metavar="N",
        help="Minimum number of keys required to form a group (default: 1).",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    return p


def _render_text(report) -> str:
    lines: List[str] = []
    for prefix, group in sorted(report.groups.items()):
        lines.append(f"[{prefix}] ({len(group.keys)} keys)")
        for k in sorted(group.keys):
            lines.append(f"  {k}")
    if report.ungrouped:
        lines.append(f"[ungrouped] ({len(report.ungrouped)} keys)")
        for k in sorted(report.ungrouped):
            lines.append(f"  {k}")
    if not lines:
        lines.append("No keys found.")
    return "\n".join(lines)


def run_group(args: argparse.Namespace) -> int:
    env = parse_env_file(args.file)
    report = group_env(env, sep=args.sep, min_group_size=args.min_size)
    if args.fmt == "json":
        print(json.dumps(report.as_dict(), indent=2))
    else:
        print(_render_text(report))
    return 0


def main(argv=None) -> None:
    parser = build_group_parser()
    args = parser.parse_args(argv)
    sys.exit(run_group(args))


if __name__ == "__main__":
    main()
