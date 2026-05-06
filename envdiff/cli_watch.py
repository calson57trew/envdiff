"""CLI entry-point for the ``envdiff watch`` sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List, Optional

from envdiff.differ import DiffResult
from envdiff.reporter import render, OutputFormat
from envdiff.watcher import watch


def build_watch_parser(parent: Optional[argparse._SubParsersAction] = None) -> argparse.ArgumentParser:  # noqa: SLF001
    kwargs = dict(
        description="Watch two .env files and report diffs on change.",
    )
    if parent is not None:
        parser = parent.add_parser("watch", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-watch", **kwargs)

    parser.add_argument("base", help="Base .env file")
    parser.add_argument("compare", help="Comparison .env file")
    parser.add_argument(
        "--interval",
        type=float,
        default=1.0,
        metavar="SECONDS",
        help="Polling interval in seconds (default: 1.0)",
    )
    parser.add_argument(
        "--format",
        dest="output_format",
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TEXT.value,
        help="Output format (default: text)",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        help="Skip value comparison; report only missing keys",
    )
    return parser


def run_watch(args: argparse.Namespace) -> None:
    fmt = OutputFormat(args.output_format)
    check_values = not args.no_values

    def _on_change(result: DiffResult) -> None:
        render(result, fmt=fmt, file=sys.stdout)

    print(f"Watching {args.base!r} vs {args.compare!r} …  (Ctrl-C to stop)", file=sys.stderr)
    try:
        watch(
            base_path=args.base,
            compare_path=args.compare,
            callback=_on_change,
            interval=args.interval,
            check_values=check_values,
        )
    except KeyboardInterrupt:
        print("\nStopped.", file=sys.stderr)


def main(argv: Optional[List[str]] = None) -> None:
    parser = build_watch_parser()
    args = parser.parse_args(argv)
    run_watch(args)


if __name__ == "__main__":  # pragma: no cover
    main()
