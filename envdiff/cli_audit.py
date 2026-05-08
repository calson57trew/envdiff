"""CLI: envdiff audit — show the audit log for past comparisons."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.auditor import load_audit_log

DEFAULT_AUDIT_FILE = ".envdiff_audit.jsonl"


def build_audit_parser(parent: argparse._SubParsersAction | None = None) -> argparse.ArgumentParser:  # type: ignore[type-arg]
    kwargs = dict(description="Display the envdiff audit log.")
    if parent is not None:
        parser = parent.add_parser("audit", **kwargs)
    else:
        parser = argparse.ArgumentParser(prog="envdiff-audit", **kwargs)
    parser.add_argument(
        "--audit-file",
        default=DEFAULT_AUDIT_FILE,
        metavar="PATH",
        help="Path to the audit log file (default: %(default)s).",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text).",
    )
    parser.add_argument(
        "--last",
        type=int,
        default=0,
        metavar="N",
        help="Show only the last N entries (0 = all).",
    )
    return parser


def _render_text(entries: list) -> str:
    if not entries:
        return "No audit entries found.\n"
    lines = []
    for e in entries:
        label = f" [{e.label}]" if e.label else ""
        lines.append(
            f"{e.timestamp}{label}\n"
            f"  base:    {e.base_file}\n"
            f"  compare: {e.compare_file}\n"
            f"  missing_in_compare={e.missing_in_compare}  "
            f"missing_in_base={e.missing_in_base}  "
            f"mismatched={e.mismatched}\n"
        )
    return "\n".join(lines)


def run_audit(args: argparse.Namespace, out=sys.stdout) -> int:
    log = load_audit_log(Path(args.audit_file))
    entries = log.entries
    if args.last > 0:
        entries = entries[-args.last :]
    if args.format == "json":
        out.write(json.dumps([e.as_dict() for e in entries], indent=2))
        out.write("\n")
    else:
        out.write(_render_text(entries))
    return 0


def main(argv=None) -> None:
    parser = build_audit_parser()
    args = parser.parse_args(argv)
    sys.exit(run_audit(args))


if __name__ == "__main__":  # pragma: no cover
    main()
