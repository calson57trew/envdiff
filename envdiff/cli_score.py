"""CLI entry-point for the *score* sub-command."""

from __future__ import annotations

import argparse
import json
import sys

from envdiff.differ import diff_envs
from envdiff.parser import parse_env_file
from envdiff.scorer import score_diff


def build_score_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        prog="envdiff score",
        description="Score two .env files and report a health grade.",
    )
    parser = (
        parent.add_parser("score", **kwargs)  # type: ignore[arg-type]
        if parent is not None
        else argparse.ArgumentParser(**kwargs)
    )
    parser.add_argument("base", help="Base .env file")
    parser.add_argument("compare", help="Comparison .env file")
    parser.add_argument(
        "--no-values",
        action="store_true",
        default=False,
        help="Ignore value mismatches; only check key presence.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--min-score",
        type=int,
        default=None,
        metavar="N",
        help="Exit with code 1 if the score is below N.",
    )
    return parser


def run_score(args: argparse.Namespace) -> int:
    base_env = parse_env_file(args.base)
    compare_env = parse_env_file(args.compare)
    result = diff_envs(base_env, compare_env, check_values=not args.no_values)
    env_score = score_diff(result)

    if args.format == "json":
        print(json.dumps(env_score.as_dict(), indent=2))
    else:
        print(f"Score : {env_score.score}/100  (Grade {env_score.grade})")
        print(f"Keys  : {env_score.total_keys} total")
        if env_score.missing_in_compare:
            print(f"  Missing in compare : {env_score.missing_in_compare}")
        if env_score.missing_in_base:
            print(f"  Missing in base    : {env_score.missing_in_base}")
        if env_score.mismatched:
            print(f"  Mismatched values  : {env_score.mismatched}")
        if env_score.score == 100:
            print("  No issues found.")

    if args.min_score is not None and env_score.score < args.min_score:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_score_parser()
    args = parser.parse_args()
    sys.exit(run_score(args))


if __name__ == "__main__":  # pragma: no cover
    main()
