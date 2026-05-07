"""CLI entry-point for the patch sub-command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.patcher import patch_env, write_patched_env


def build_patch_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: E501
    kwargs = dict(
        prog="envdiff patch",
        description="Patch a base .env file using a compare .env as the source of truth.",
    )
    parser = (
        parent.add_parser("patch", **kwargs) if parent else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("base", help="Path to the base .env file to patch.")
    parser.add_argument("compare", help="Path to the compare .env file.")
    parser.add_argument(
        "--output", "-o", default=None,
        help="Write patched result to this file (default: overwrite base).",
    )
    parser.add_argument(
        "--add-missing", action="store_true", default=True,
        help="Add keys present in compare but missing in base (default: on).",
    )
    parser.add_argument(
        "--no-add-missing", dest="add_missing", action="store_false",
        help="Do not add missing keys.",
    )
    parser.add_argument(
        "--fix-mismatched", action="store_true", default=False,
        help="Overwrite mismatched values in base with compare values.",
    )
    parser.add_argument(
        "--skip", nargs="*", metavar="KEY", default=[],
        help="Keys to leave untouched.",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print what would change without writing any file.",
    )
    return parser


def run_patch(args: argparse.Namespace) -> int:
    base_path = Path(args.base)
    compare_path = Path(args.compare)

    base_env = parse_env_file(base_path)
    compare_env = parse_env_file(compare_path)
    diff = diff_envs(base_env, compare_env)

    result = patch_env(
        base_env,
        diff,
        add_missing=args.add_missing,
        fix_mismatched=args.fix_mismatched,
        skip_keys=args.skip,
    )

    if args.dry_run:
        if result.added:
            print("Would add:", ", ".join(sorted(result.added)))
        if result.updated:
            print("Would update:", ", ".join(sorted(result.updated)))
        if result.skipped:
            print("Would skip:", ", ".join(sorted(result.skipped)))
        if not result.added and not result.updated:
            print("No changes.")
        return 0

    out_path = Path(args.output) if args.output else base_path
    write_patched_env(result.patched, out_path)
    print(f"Patched {out_path} (+{len(result.added)} added, ~{len(result.updated)} updated).")
    return 0


def main() -> None:  # pragma: no cover
    parser = build_patch_parser()
    sys.exit(run_patch(parser.parse_args()))


if __name__ == "__main__":  # pragma: no cover
    main()
