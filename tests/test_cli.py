"""Tests for envdiff.cli."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.cli import main


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content)
    return path


def test_cli_identical_files_exits_zero(env_dir, capsys):
    base = _write(env_dir / ".env.base", "FOO=bar\nBAZ=qux\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=bar\nBAZ=qux\n")
    code = main([str(base), str(cmp)])
    assert code == 0
    assert "No differences" in capsys.readouterr().out


def test_cli_missing_key_reported(env_dir, capsys):
    base = _write(env_dir / ".env.base", "FOO=bar\nSECRET=x\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=bar\n")
    main([str(base), str(cmp)])
    assert "SECRET" in capsys.readouterr().out


def test_cli_exit_code_flag_returns_one_on_diff(env_dir):
    base = _write(env_dir / ".env.base", "FOO=bar\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=different\n")
    code = main([str(base), str(cmp), "--exit-code"])
    assert code == 1


def test_cli_exit_code_flag_returns_zero_when_identical(env_dir):
    base = _write(env_dir / ".env.base", "FOO=bar\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=bar\n")
    code = main([str(base), str(cmp), "--exit-code"])
    assert code == 0


def test_cli_no_values_flag_ignores_mismatch(env_dir, capsys):
    base = _write(env_dir / ".env.base", "FOO=bar\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=different\n")
    code = main([str(base), str(cmp), "--no-values", "--exit-code"])
    assert code == 0


def test_cli_json_format(env_dir, capsys):
    import json
    base = _write(env_dir / ".env.base", "FOO=bar\n")
    cmp = _write(env_dir / ".env.cmp", "FOO=bar\n")
    main([str(base), str(cmp), "--format", "json"])
    data = json.loads(capsys.readouterr().out)
    assert "missing_in_compare" in data


def test_cli_missing_base_file_returns_two(env_dir, capsys):
    code = main([str(env_dir / "nonexistent.env"), str(env_dir / "also.env")])
    assert code == 2
    assert "error" in capsys.readouterr().err


def test_cli_missing_compare_file_returns_two(env_dir, capsys):
    base = _write(env_dir / ".env.base", "FOO=bar\n")
    code = main([str(base), str(env_dir / "nonexistent.env")])
    assert code == 2
