"""Tests for envdiff.cli_watch."""

from __future__ import annotations

import time
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from envdiff.cli_watch import build_watch_parser, run_watch
from envdiff.differ import DiffResult


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> None:
    path.write_text(content, encoding="utf-8")


def test_build_watch_parser_defaults() -> None:
    parser = build_watch_parser()
    args = parser.parse_args(["base.env", "compare.env"])
    assert args.base == "base.env"
    assert args.compare == "compare.env"
    assert args.interval == 1.0
    assert args.output_format == "text"
    assert args.no_values is False


def test_build_watch_parser_custom_interval() -> None:
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env", "--interval", "0.5"])
    assert args.interval == 0.5


def test_build_watch_parser_no_values_flag() -> None:
    parser = build_watch_parser()
    args = parser.parse_args(["a.env", "b.env", "--no-values"])
    assert args.no_values is True


def test_run_watch_invokes_watch(env_dir: Path) -> None:
    base = env_dir / "base.env"
    compare = env_dir / "compare.env"
    _write(base, "X=1\n")
    _write(compare, "X=1\n")

    parser = build_watch_parser()
    args = parser.parse_args([str(base), str(compare)])

    called_with: List[dict] = []

    def _fake_watch(**kwargs):  # type: ignore[override]
        called_with.append(kwargs)

    with patch("envdiff.cli_watch.watch", side_effect=_fake_watch):
        run_watch(args)

    assert len(called_with) == 1
    kw = called_with[0]
    assert kw["base_path"] == str(base)
    assert kw["compare_path"] == str(compare)
    assert kw["interval"] == 1.0
    assert kw["check_values"] is True


def test_run_watch_keyboard_interrupt_exits_gracefully(env_dir: Path, capsys) -> None:
    base = env_dir / "base.env"
    compare = env_dir / "compare.env"
    _write(base, "A=1\n")
    _write(compare, "A=1\n")

    parser = build_watch_parser()
    args = parser.parse_args([str(base), str(compare)])

    with patch("envdiff.cli_watch.watch", side_effect=KeyboardInterrupt):
        run_watch(args)  # should NOT raise

    captured = capsys.readouterr()
    assert "Stopped" in captured.err
