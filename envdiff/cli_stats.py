"""CLI entry point: compute diff statistics across multiple .env file pairs."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from envdiff.differ import diff_envs
from envdiff.differ_stats import compute_stats
from envdiff.parser import parse_env_file


def build_stats_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-stats",
        description="Compute aggregate diff statistics across multiple env file pairs.",
    )
    parser.add_argument(
        "pairs",
        nargs="+",
        metavar="BASE:COMPARE",
        help="Colon-separated pairs of env files to compare (e.g. .env:.env.prod).",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        default=False,
        help="Ignore value mismatches; only report missing keys.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    return parser


def _parse_pairs(raw: List[str]) -> List[tuple[Path, Path]]:
    pairs = []
    for item in raw:
        parts = item.split(":", 1)
        if len(parts) != 2:
            raise SystemExit(f"Invalid pair (expected BASE:COMPARE): {item!r}")
        pairs.append((Path(parts[0]), Path(parts[1])))
    return pairs


def run_stats(args: argparse.Namespace) -> int:
    pairs = _parse_pairs(args.pairs)
    results = []
    for base_path, compare_path in pairs:
        base_env = parse_env_file(base_path)
        compare_env = parse_env_file(compare_path)
        results.append(diff_envs(base_env, compare_env, check_values=not args.no_values))

    stats = compute_stats(results)

    if args.format == "json":
        print(json.dumps(stats.as_dict(), indent=2))
    else:
        d = stats.as_dict()
        print(f"Snapshots compared : {d['total_snapshots']}")
        print(f"Total issues       : {d['total_issues']}")
        print(f"  Missing in compare: {d['total_missing_in_compare']}")
        print(f"  Missing in base   : {d['total_missing_in_base']}")
        print(f"  Mismatched values : {d['total_mismatched']}")
        if d["most_frequent_missing"]:
            print("Top missing keys   : " + ", ".join(d["most_frequent_missing"]))
        if d["most_frequent_mismatched"]:
            print("Top mismatched keys: " + ", ".join(d["most_frequent_mismatched"]))

    return 1 if stats.total_issues > 0 else 0


def main() -> None:  # pragma: no cover
    parser = build_stats_parser()
    args = parser.parse_args()
    sys.exit(run_stats(args))


if __name__ == "__main__":  # pragma: no cover
    main()
