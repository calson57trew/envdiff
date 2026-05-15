"""Tests for envdiff.cli_group."""
from __future__ import annotations

import json
import os
import textwrap
from pathlib import Path

import pytest

from envdiff.cli_group import build_group_parser, run_group


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content))
    return path


@pytest.fixture()
def sample_file(env_dir):
    return _write(
        env_dir / ".env",
        """
        DB_HOST=localhost
        DB_PORT=5432
        AWS_KEY=abc
        AWS_SECRET=xyz
        PORT=8080
        """,
    )


def test_build_group_parser_defaults():
    p = build_group_parser()
    args = p.parse_args(["some.env"])
    assert args.sep == "_"
    assert args.min_size == 1
    assert args.fmt == "text"


def test_build_group_parser_custom_sep():
    p = build_group_parser()
    args = p.parse_args(["some.env", "--sep", "."])
    assert args.sep == "."


def test_run_group_text_output(sample_file, capsys):
    p = build_group_parser()
    args = p.parse_args([str(sample_file)])
    rc = run_group(args)
    assert rc == 0
    out = capsys.readouterr().out
    assert "[DB]" in out
    assert "[AWS]" in out
    assert "DB_HOST" in out


def test_run_group_json_output(sample_file, capsys):
    p = build_group_parser()
    args = p.parse_args([str(sample_file), "--format", "json"])
    rc = run_group(args)
    assert rc == 0
    data = json.loads(capsys.readouterr().out)
    assert "groups" in data
    assert "DB" in data["groups"]
    assert data["total_groups"] == 2


def test_run_group_min_size_hides_small_groups(env_dir, capsys):
    f = _write(env_dir / "small.env", "DB_HOST=x\nDB_PORT=y\nSOLO_KEY=z\n")
    p = build_group_parser()
    args = p.parse_args([str(f), "--min-size", "2"])
    run_group(args)
    out = capsys.readouterr().out
    assert "[DB]" in out
    assert "[SOLO]" not in out
    assert "SOLO_KEY" in out  # appears under ungrouped


def test_run_group_ungrouped_shown_in_text(sample_file, capsys):
    p = build_group_parser()
    args = p.parse_args([str(sample_file)])
    run_group(args)
    out = capsys.readouterr().out
    assert "[ungrouped]" in out
    assert "PORT" in out
