"""Tests for envdiff.cli_snapshot."""

from __future__ import annotations

import json
import os
import pytest

from envdiff.cli_snapshot import build_snapshot_parser, run_snapshot


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: str, content: str) -> str:
    with open(path, "w") as fh:
        fh.write(content)
    return path


def test_save_creates_snapshot(env_dir):
    base = _write(str(env_dir / ".env.base"), "KEY=value\nFOO=bar\n")
    cmp = _write(str(env_dir / ".env.cmp"), "KEY=value\n")
    out = str(env_dir / "snap.json")

    code = run_snapshot(["save", base, cmp, out])

    assert code == 0
    assert os.path.isfile(out)
    with open(out) as fh:
        data = json.load(fh)
    assert "FOO" in data["missing_in_compare"]


def test_save_with_label(env_dir):
    base = _write(str(env_dir / ".env.base"), "A=1\n")
    cmp = _write(str(env_dir / ".env.cmp"), "A=1\n")
    out = str(env_dir / "snap.json")

    run_snapshot(["save", base, cmp, out, "--label", "my-label"])

    with open(out) as fh:
        data = json.load(fh)
    assert data["label"] == "my-label"


def test_save_no_values_flag(env_dir):
    base = _write(str(env_dir / ".env.base"), "KEY=one\n")
    cmp = _write(str(env_dir / ".env.cmp"), "KEY=two\n")
    out = str(env_dir / "snap.json")

    run_snapshot(["save", base, cmp, out, "--no-values"])

    with open(out) as fh:
        data = json.load(fh)
    assert data["mismatched"] == {}


def test_compare_exits_zero_when_no_diff(env_dir, capsys):
    base = _write(str(env_dir / ".env.base"), "KEY=val\n")
    cmp = _write(str(env_dir / ".env.cmp"), "KEY=val\n")
    out = str(env_dir / "snap.json")
    run_snapshot(["save", base, cmp, out])

    code = run_snapshot(["compare", base, out])
    assert code == 0


def test_compare_exit_code_flag(env_dir):
    base = _write(str(env_dir / ".env.base"), "KEY=val\nEXTRA=x\n")
    cmp = _write(str(env_dir / ".env.cmp"), "KEY=val\n")
    out = str(env_dir / "snap.json")
    run_snapshot(["save", base, cmp, out])

    code = run_snapshot(["compare", base, out, "--exit-code"])
    assert code == 1


def test_build_snapshot_parser_returns_parser():
    parser = build_snapshot_parser()
    assert parser.prog == "envdiff-snapshot"
