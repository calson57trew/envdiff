"""CLI entry-point for the rename sub-command."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.renamer import rename_keys, has_renames


def build_rename_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="envdiff rename",
        description="Rename keys inside a .env file.",
    )
    parser = parent.add_parser("rename", **kwargs) if parent else argparse.ArgumentParser(**kwargs)

    parser.add_argument("file", help="Path to the .env file to rename keys in.")
    parser.add_argument(
        "--map",
        metavar="OLD=NEW",
        action="append",
        default=[],
        help="Key rename pair, e.g. --map OLD_KEY=NEW_KEY. Repeatable.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        default=False,
        help="Allow renaming even when the new key already exists.",
    )
    parser.add_argument(
        "--format",
        choices=["env", "json"],
        default="env",
        help="Output format (default: env).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 when any rename was skipped.",
    )
    return parser


def _parse_map(pairs: list[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for pair in pairs:
        if "=" not in pair:
            raise SystemExit(f"Invalid --map value {pair!r}: expected OLD=NEW")
        old, new = pair.split("=", 1)
        mapping[old.strip()] = new.strip()
    return mapping


def run_rename(args: argparse.Namespace) -> int:
    env = parse_env_file(Path(args.file))
    mapping = _parse_map(args.map)
    result = rename_keys(env, mapping, overwrite=args.overwrite)

    if args.format == "json":
        payload = {
            "output": {k: v for k, v in sorted(result.output.items())},
            "renamed": result.renamed,
            "skipped": result.skipped,
        }
        print(json.dumps(payload, indent=2))
    else:
        for key, value in sorted(result.output.items()):
            print(f"{key}={value or ''}")

    if result.skipped:
        print(f"# skipped: {', '.join(result.skipped)}", file=sys.stderr)

    if args.exit_code and result.skipped:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_rename_parser()
    sys.exit(run_rename(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
