"""Tests for envdiff.cli_summary."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from envdiff.cli_summary import build_summary_parser, run_summary


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_summary_identical_files_exits_zero(env_dir):
    base = _write(env_dir / ".env.base", "KEY=value\nOTHER=x\n")
    cmp = _write(env_dir / ".env.cmp", "KEY=value\nOTHER=x\n")
    parser = build_summary_parser()
    args = parser.parse_args([str(base), str(cmp)])
    assert run_summary(args) == 0


def test_summary_exit_code_flag_on_diff(env_dir):
    base = _write(env_dir / ".env.base", "KEY=value\n")
    cmp = _write(env_dir / ".env.cmp", "OTHER=value\n")
    parser = build_summary_parser()
    args = parser.parse_args(["--exit-code", str(base), str(cmp)])
    assert run_summary(args) == 1


def test_summary_no_exit_code_flag_always_zero(env_dir):
    base = _write(env_dir / ".env.base", "KEY=value\n")
    cmp = _write(env_dir / ".env.cmp", "OTHER=value\n")
    parser = build_summary_parser()
    args = parser.parse_args([str(base), str(cmp)])
    assert run_summary(args) == 0


def test_summary_json_output(env_dir, capsys):
    base = _write(env_dir / ".env.base", "KEY=val\nGONE=x\n")
    cmp = _write(env_dir / ".env.cmp", "KEY=different\nNEW=y\n")
    parser = build_summary_parser()
    args = parser.parse_args(["--format", "json", str(base), str(cmp)])
    run_summary(args)
    captured = capsys.readouterr().out
    data = json.loads(captured)
    assert data["total_keys"] == 3
    assert data["mismatched"] == 1
    assert data["missing_in_compare"] == 1
    assert data["missing_in_base"] == 1
    assert data["total_issues"] == 3


def test_summary_text_output_contains_labels(env_dir, capsys):
    base = _write(env_dir / ".env.base", "A=1\nB=2\n")
    cmp = _write(env_dir / ".env.cmp", "A=1\nB=2\n")
    parser = build_summary_parser()
    args = parser.parse_args([str(base), str(cmp)])
    run_summary(args)
    out = capsys.readouterr().out
    assert "Total keys" in out
    assert "Identical" in out
    assert "Total issues" in out


def test_build_summary_parser_defaults():
    parser = build_summary_parser()
    args = parser.parse_args(["a.env", "b.env"])
    assert args.fmt == "text"
    assert args.exit_code is False
