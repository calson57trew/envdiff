"""Tests for envdiff.cli_matrix."""
from __future__ import annotations

import json
import pytest

from envdiff.cli_matrix import build_matrix_parser, run_matrix, _parse_pairs


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    path.write_text(content)
    return str(path)


def _run(argv):
    return run_matrix(argv)


# ---------------------------------------------------------------------------
# Parser
# ---------------------------------------------------------------------------

def test_build_matrix_parser_defaults():
    p = build_matrix_parser()
    args = p.parse_args(["a=x", "b=y"])
    assert args.format == "text"
    assert not args.no_values
    assert not args.exit_code


def test_parse_pairs_valid():
    result = _parse_pairs(["dev=.env.dev", "prod=.env.prod"])
    assert result == {"dev": ".env.dev", "prod": ".env.prod"}


def test_parse_pairs_invalid_raises():
    with pytest.raises(SystemExit):
        _parse_pairs(["nodivider"])


# ---------------------------------------------------------------------------
# run_matrix
# ---------------------------------------------------------------------------

def test_cli_identical_exits_zero(env_dir):
    a = _write(env_dir / "a.env", "FOO=bar\n")
    b = _write(env_dir / "b.env", "FOO=bar\n")
    assert _run([f"a={a}", f"b={b}"]) == 0


def test_cli_diff_exits_zero_without_flag(env_dir):
    a = _write(env_dir / "a.env", "FOO=bar\nEXTRA=1\n")
    b = _write(env_dir / "b.env", "FOO=bar\n")
    assert _run([f"a={a}", f"b={b}"]) == 0


def test_cli_diff_exits_one_with_exit_code_flag(env_dir):
    a = _write(env_dir / "a.env", "FOO=bar\nEXTRA=1\n")
    b = _write(env_dir / "b.env", "FOO=bar\n")
    assert _run([f"a={a}", f"b={b}", "--exit-code"]) == 1


def test_cli_json_output_is_valid(env_dir, capsys):
    a = _write(env_dir / "a.env", "FOO=1\n")
    b = _write(env_dir / "b.env", "FOO=2\n")
    _run([f"a={a}", f"b={b}", "--format", "json"])
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert data[0]["base"] == "a"
    assert data[0]["compare"] == "b"


def test_cli_text_output_shows_diff(env_dir, capsys):
    a = _write(env_dir / "a.env", "EXTRA=1\n")
    b = _write(env_dir / "b.env", "")
    _run([f"a={a}", f"b={b}"])
    captured = capsys.readouterr()
    assert "DIFF" in captured.out
    assert "EXTRA" in captured.out


def test_cli_no_values_flag_ignores_mismatch(env_dir):
    a = _write(env_dir / "a.env", "FOO=one\n")
    b = _write(env_dir / "b.env", "FOO=two\n")
    assert _run([f"a={a}", f"b={b}", "--no-values", "--exit-code"]) == 0
