"""CLI entry-point for the env-transform subcommand."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.parser import parse_env_file
from envdiff.transformer import available_operations, transform_env


def build_transform_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(
        description="Apply transformation operations to a .env file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Available operations: " + ", ".join(available_operations()),
    )
    if parent is not None:
        parser = parent.add_parser("transform", **kwargs)
    else:
        parser = argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the .env file to transform.")
    parser.add_argument(
        "--ops",
        nargs="+",
        metavar="OP",
        default=[],
        help="One or more operations to apply in order.",
    )
    parser.add_argument(
        "--format",
        choices=["dotenv", "json"],
        default="dotenv",
        dest="fmt",
        help="Output format (default: dotenv).",
    )
    parser.add_argument(
        "--show-diff",
        action="store_true",
        default=False,
        help="Print only the changed keys instead of the full output.",
    )
    return parser


def _render_dotenv(env: dict) -> str:
    lines = []
    for k in sorted(env):
        v = env[k] if env[k] is not None else ""
        lines.append(f"{k}={v}")
    return "\n".join(lines)


def run_transform(args: argparse.Namespace) -> int:
    env = parse_env_file(args.file)

    try:
        result = transform_env(env, args.ops)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.show_diff:
        if result.is_unchanged:
            print("No changes.")
        else:
            for key in result.changed_keys:
                before = result.original.get(key)
                after = result.transformed.get(key)
                print(f"  {key}: {before!r} -> {after!r}")
        return 0

    if args.fmt == "json":
        print(json.dumps(result.transformed, indent=2, default=str))
    else:
        print(_render_dotenv(result.transformed))

    return 0


def main(argv: List[str] | None = None) -> None:
    parser = build_transform_parser()
    args = parser.parse_args(argv)
    sys.exit(run_transform(args))


if __name__ == "__main__":
    main()
