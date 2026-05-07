"""CLI entry-point for the `envdiff template` command."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from envdiff.parser import parse_env_file
from envdiff.templater import build_template, render_template


def build_template_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-template",
        description="Generate a .env.example from an existing .env file.",
    )
    parser.add_argument("env_file", help="Path to the source .env file.")
    parser.add_argument(
        "-o",
        "--output",
        default=None,
        help="Write output to this file instead of stdout.",
    )
    parser.add_argument(
        "--placeholder",
        default="",
        metavar="TEXT",
        help="Placeholder text for sensitive values (default: empty string).",
    )
    return parser


def run_template(args: argparse.Namespace) -> int:
    source = Path(args.env_file)
    if not source.exists():
        print(f"error: file not found: {source}", file=sys.stderr)
        return 2

    env = parse_env_file(source)
    template = build_template(env, sensitive_placeholder=args.placeholder)
    output = render_template(template)

    if args.output:
        Path(args.output).write_text(output, encoding="utf-8")
    else:
        sys.stdout.write(output)

    return 0


def main() -> None:  # pragma: no cover
    parser = build_template_parser()
    args = parser.parse_args()
    sys.exit(run_template(args))


if __name__ == "__main__":  # pragma: no cover
    main()
