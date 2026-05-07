"""Tests for envdiff.scorer and envdiff.cli_score."""

from __future__ import annotations

import json
import os
import textwrap
from io import StringIO
from pathlib import Path

import pytest

from envdiff.differ import DiffResult
from envdiff.scorer import EnvScore, score_diff


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def clean_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=[],
        missing_in_base=[],
        mismatched={},
        common=["KEY_A", "KEY_B"],
    )


@pytest.fixture()
def dirty_result() -> DiffResult:
    return DiffResult(
        missing_in_compare=["ALPHA", "BETA"],
        missing_in_base=["GAMMA"],
        mismatched={"DELTA": ("old", "new")},
        common=["SHARED"],
    )


# ---------------------------------------------------------------------------
# scorer unit tests
# ---------------------------------------------------------------------------

def test_score_clean_result_is_100(clean_result):
    s = score_diff(clean_result)
    assert s.score == 100


def test_score_clean_grade_is_A(clean_result):
    s = score_diff(clean_result)
    assert s.grade == "A"


def test_score_dirty_result_below_100(dirty_result):
    s = score_diff(dirty_result)
    assert s.score < 100


def test_score_counts_match_result(dirty_result):
    s = score_diff(dirty_result)
    assert s.missing_in_compare == 2
    assert s.missing_in_base == 1
    assert s.mismatched == 1


def test_score_total_keys_includes_all(dirty_result):
    s = score_diff(dirty_result)
    # ALPHA, BETA, GAMMA, DELTA, SHARED
    assert s.total_keys == 5


def test_score_as_dict_keys(clean_result):
    d = score_diff(clean_result).as_dict()
    assert set(d.keys()) == {"score", "grade", "penalty", "total_keys",
                              "missing_in_compare", "missing_in_base", "mismatched"}


def test_grade_boundaries():
    def _score(n):
        # Build a fake EnvScore with a given score value
        return EnvScore(score=n, penalty=0, total_keys=1,
                        missing_in_compare=0, missing_in_base=0, mismatched=0)

    assert _score(95).grade == "A"
    assert _score(80).grade == "B"
    assert _score(65).grade == "C"
    assert _score(45).grade == "D"
    assert _score(30).grade == "F"


# ---------------------------------------------------------------------------
# cli_score integration tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content))
    return path


def _run(args, capsys):
    from envdiff.cli_score import build_score_parser, run_score
    parser = build_score_parser()
    ns = parser.parse_args(args)
    code = run_score(ns)
    captured = capsys.readouterr()
    return code, captured.out


def test_cli_score_identical_exits_zero(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=value\n")
    b = _write(env_dir / "b.env", "KEY=value\n")
    code, out = _run([str(a), str(b)], capsys)
    assert code == 0
    assert "100" in out


def test_cli_score_json_output(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=val\n")
    b = _write(env_dir / "b.env", "KEY=val\n")
    code, out = _run([str(a), str(b), "--format", "json"], capsys)
    data = json.loads(out)
    assert data["score"] == 100
    assert data["grade"] == "A"


def test_cli_min_score_triggers_exit_one(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=val\nOTHER=x\n")
    b = _write(env_dir / "b.env", "KEY=val\n")
    code, _ = _run([str(a), str(b), "--min-score", "100"], capsys)
    assert code == 1


def test_cli_min_score_passes_when_above_threshold(env_dir, capsys):
    a = _write(env_dir / "a.env", "KEY=val\n")
    b = _write(env_dir / "b.env", "KEY=val\n")
    code, _ = _run([str(a), str(b), "--min-score", "80"], capsys)
    assert code == 0
