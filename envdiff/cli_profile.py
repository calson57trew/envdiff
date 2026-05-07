"""CLI entry-point for the `envdiff profile` sub-command."""
from __future__ import annotations

import argparse
import json
import sys

from envdiff.profiler import profile_env


def build_profile_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    description = "Display statistics and diagnostics for a single .env file."
    if parent is not None:
        parser = parent.add_parser("profile", help=description, description=description)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-profile", description=description)

    parser.add_argument("file", help="Path to the .env file to profile.")
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text).",
    )
    return parser


def _render_text(profile, path: str) -> str:
    lines = [
        f"Profile: {path}",
        f"  Total keys       : {profile.total_keys}",
        f"  Empty values     : {len(profile.empty_values)}",
        f"  Duplicate keys   : {len(profile.duplicate_keys)}",
        f"  Longest key      : {profile.longest_key or '-'}",
        f"  Longest value key: {profile.longest_value_key or '-'}",
        f"  Avg value length : {profile.avg_value_length:.1f}",
    ]
    if profile.empty_values:
        lines.append("  Empty: " + ", ".join(profile.empty_values))
    if profile.duplicate_keys:
        lines.append("  Duplicates: " + ", ".join(profile.duplicate_keys))
    return "\n".join(lines)


def _render_json(profile, path: str) -> str:
    data = {
        "file": path,
        "total_keys": profile.total_keys,
        "empty_values": profile.empty_values,
        "duplicate_keys": profile.duplicate_keys,
        "longest_key": profile.longest_key,
        "longest_value_key": profile.longest_value_key,
        "avg_value_length": round(profile.avg_value_length, 2),
    }
    return json.dumps(data, indent=2)


def run_profile(args: argparse.Namespace) -> int:
    profile = profile_env(args.file)
    if args.fmt == "json":
        print(_render_json(profile, args.file))
    else:
        print(_render_text(profile, args.file))
    return 0


def main(argv=None) -> None:
    parser = build_profile_parser()
    args = parser.parse_args(argv)
    sys.exit(run_profile(args))


if __name__ == "__main__":  # pragma: no cover
    main()
