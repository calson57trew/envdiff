"""CLI entry-point for the env dependency grapher."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from envdiff.grapher import build_graph
from envdiff.parser import parse_env_file


def build_graph_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="envdiff-graph",
        description="Show key reference dependencies inside a .env file.",
    )
    p.add_argument("file", type=Path, help="Path to .env file")
    p.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        dest="fmt",
        help="Output format (default: text)",
    )
    p.add_argument(
        "--roots-only",
        action="store_true",
        help="Only print root keys (no dependencies)",
    )
    return p


def _render_text(graph, roots_only: bool) -> str:
    lines: list[str] = []
    keys = graph.roots() if roots_only else sorted(graph.nodes)
    for key in keys:
        node = graph.nodes[key]
        deps = ", ".join(sorted(node.depends_on)) or "—"
        used_by = ", ".join(sorted(node.depended_by)) or "—"
        lines.append(f"{key}")
        lines.append(f"  depends_on : {deps}")
        lines.append(f"  depended_by: {used_by}")
    return "\n".join(lines)


def run_graph(args: argparse.Namespace) -> int:
    try:
        env = parse_env_file(args.file)
    except FileNotFoundError:
        print(f"error: file not found: {args.file}", file=sys.stderr)
        return 2

    graph = build_graph(env)

    if args.fmt == "json":
        data = graph.as_dict()
        if args.roots_only:
            data = {k: v for k, v in data.items() if k in graph.roots()}
        print(json.dumps(data, indent=2))
    else:
        print(_render_text(graph, args.roots_only))

    return 0


def main() -> None:
    parser = build_graph_parser()
    args = parser.parse_args()
    sys.exit(run_graph(args))


if __name__ == "__main__":
    main()
