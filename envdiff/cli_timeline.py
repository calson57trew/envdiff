"""CLI entry-point for the timeline diff command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ_timeline import build_timeline


def build_timeline_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="envdiff-timeline",
        description="Compare a sequence of .env snapshots and report changes over time.",
    )
    parser.add_argument(
        "snapshots",
        nargs="+",
        metavar="SNAPSHOT",
        help="Two or more snapshot files in chronological order.",
    )
    parser.add_argument(
        "--no-values",
        action="store_true",
        default=False,
        help="Compare keys only; ignore value differences.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--exit-code",
        action="store_true",
        default=False,
        help="Exit with code 1 if any changes are detected.",
    )
    return parser


def _render_text(timeline) -> str:
    lines: List[str] = []
    for entry in timeline.entries:
        label_from = entry.from_label or entry.from_path
        label_to = entry.to_label or entry.to_path
        lines.append(f"[{label_from}] -> [{label_to}]")
        if not entry.has_changes:
            lines.append("  No changes.")
        else:
            for key in sorted(entry.diff.missing_in_compare):
                lines.append(f"  - REMOVED:   {key}")
            for key in sorted(entry.diff.missing_in_base):
                lines.append(f"  + ADDED:     {key}")
            for key in sorted(entry.diff.mismatched):
                lines.append(f"  ~ CHANGED:   {key}")
        lines.append("")
    summary = (
        f"Steps: {timeline.total_steps}  "
        f"Steps with changes: {timeline.steps_with_changes}"
    )
    lines.append(summary)
    return "\n".join(lines)


def run_timeline(args: argparse.Namespace) -> int:
    if len(args.snapshots) < 2:
        print("error: at least two snapshot files are required.", file=sys.stderr)
        return 2

    timeline = build_timeline(
        snapshot_paths=args.snapshots,
        check_values=not args.no_values,
    )

    if args.format == "json":
        print(json.dumps(timeline.as_dict(), indent=2))
    else:
        print(_render_text(timeline))

    if args.exit_code and timeline.steps_with_changes > 0:
        return 1
    return 0


def main() -> None:  # pragma: no cover
    parser = build_timeline_parser()
    args = parser.parse_args()
    sys.exit(run_timeline(args))


if __name__ == "__main__":  # pragma: no cover
    main()
