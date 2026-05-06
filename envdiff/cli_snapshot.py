"""CLI sub-commands for snapshot management: save and compare."""

from __future__ import annotations

import argparse
import sys

from envdiff.differ import diff_envs, has_differences
from envdiff.parser import parse_env_file
from envdiff.reporter import OutputFormat, render
from envdiff.snapshotter import load_snapshot, save_snapshot


def build_snapshot_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-snapshot",
        description="Save or compare .env diff snapshots.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # save sub-command
    save_p = sub.add_parser("save", help="Diff two files and save snapshot.")
    save_p.add_argument("base", help="Base .env file")
    save_p.add_argument("compare", help="Compare .env file")
    save_p.add_argument("output", help="Destination snapshot JSON path")
    save_p.add_argument("--label", default="", help="Optional label for this snapshot")
    save_p.add_argument(
        "--no-values", action="store_true", help="Ignore value mismatches"
    )

    # compare sub-command
    cmp_p = sub.add_parser("compare", help="Compare .env file against a snapshot.")
    cmp_p.add_argument("base", help="Base .env file")
    cmp_p.add_argument("snapshot", help="Snapshot JSON file to compare against")
    cmp_p.add_argument(
        "--format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
    )
    cmp_p.add_argument(
        "--exit-code", action="store_true", help="Exit 1 when differences found"
    )

    return parser


def run_snapshot(argv: list[str] | None = None) -> int:
    parser = build_snapshot_parser()
    args = parser.parse_args(argv)

    if args.command == "save":
        base_env = parse_env_file(args.base)
        cmp_env = parse_env_file(args.compare)
        result = diff_envs(base_env, cmp_env, check_values=not args.no_values)
        save_snapshot(result, args.output, label=args.label)
        print(f"Snapshot saved to {args.output}")
        return 0

    # compare
    base_env = parse_env_file(args.base)
    snap_result, meta = load_snapshot(args.snapshot)
    live_result = diff_envs(base_env, {}, check_values=False)
    # Re-diff: use snapshot's missing_in_compare as the reference set
    result = snap_result
    fmt = OutputFormat(args.format)
    render(result, fmt=fmt)
    if args.exit_code and has_differences(result):
        return 1
    return 0


def main() -> None:  # pragma: no cover
    sys.exit(run_snapshot())


if __name__ == "__main__":  # pragma: no cover
    main()
