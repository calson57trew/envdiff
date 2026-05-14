"""CLI entry-point for the pairwise diff matrix command."""
from __future__ import annotations

import argparse
import json
import sys
from typing import List

from envdiff.differ_matrix import DiffMatrix, build_matrix


def build_matrix_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-matrix",
        description="Show a pairwise diff matrix across multiple .env files.",
    )
    p.add_argument(
        "files",
        nargs="+",
        metavar="NAME=PATH",
        help="Named env files, e.g. dev=.env.dev prod=.env.prod",
    )
    p.add_argument(
        "--no-values",
        action="store_true",
        help="Ignore value differences; check keys only.",
    )
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
    )
    p.add_argument(
        "--exit-code",
        action="store_true",
        help="Exit with code 1 when any pair has differences.",
    )
    return p


def _parse_pairs(args: List[str]) -> dict:
    result = {}
    for token in args:
        if "=" not in token:
            raise SystemExit(f"Invalid NAME=PATH token: {token!r}")
        name, _, path = token.partition("=")
        result[name.strip()] = path.strip()
    return result


def _render_text(matrix: DiffMatrix) -> str:
    lines: List[str] = []
    for cell in matrix.cells:
        status = "OK" if cell.is_clean else "DIFF"
        lines.append(f"{cell.base_name} vs {cell.compare_name}: {status}")
        if not cell.is_clean:
            for k in sorted(cell.result.missing_in_compare):
                lines.append(f"  missing_in_compare: {k}")
            for k in sorted(cell.result.missing_in_base):
                lines.append(f"  missing_in_base: {k}")
            for k in sorted(cell.result.mismatched):
                lines.append(f"  mismatch: {k}")
    return "\n".join(lines)


def _render_json(matrix: DiffMatrix) -> str:
    data = []
    for cell in matrix.cells:
        data.append({
            "base": cell.base_name,
            "compare": cell.compare_name,
            "clean": cell.is_clean,
            "missing_in_compare": sorted(cell.result.missing_in_compare),
            "missing_in_base": sorted(cell.result.missing_in_base),
            "mismatched": sorted(cell.result.mismatched),
        })
    return json.dumps(data, indent=2)


def run_matrix(argv: List[str] | None = None) -> int:
    parser = build_matrix_parser()
    args = parser.parse_args(argv)
    paths = _parse_pairs(args.files)
    matrix = build_matrix(paths, check_values=not args.no_values)

    if args.format == "json":
        print(_render_json(matrix))
    else:
        output = _render_text(matrix)
        if output:
            print(output)

    if args.exit_code and not matrix.is_fully_clean():
        return 1
    return 0


def main() -> None:
    sys.exit(run_matrix())


if __name__ == "__main__":
    main()
