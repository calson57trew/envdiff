"""Tests for envdiff.cli_patch."""

from __future__ import annotations

from pathlib import Path

import pytest

from envdiff.cli_patch import build_patch_parser, run_patch


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(content, encoding="utf-8")
    return path


def _run(args_list, env_dir):
    parser = build_patch_parser()
    args = parser.parse_args(args_list)
    return run_patch(args)


def test_patch_adds_missing_key(env_dir):
    base = _write(env_dir / ".env.base", "HOST=localhost\n")
    comp = _write(env_dir / ".env.comp", "HOST=localhost\nSECRET=xyz\n")
    out = env_dir / ".env.out"
    rc = _run([str(base), str(comp), "--output", str(out)], env_dir)
    assert rc == 0
    text = out.read_text()
    assert "SECRET=xyz" in text
    assert "HOST=localhost" in text


def test_patch_no_add_missing_flag(env_dir):
    base = _write(env_dir / ".env.base", "HOST=localhost\n")
    comp = _write(env_dir / ".env.comp", "HOST=localhost\nSECRET=xyz\n")
    out = env_dir / ".env.out"
    rc = _run([str(base), str(comp), "--no-add-missing", "--output", str(out)], env_dir)
    assert rc == 0
    text = out.read_text()
    assert "SECRET" not in text


def test_patch_fix_mismatched(env_dir):
    base = _write(env_dir / ".env.base", "PORT=5432\n")
    comp = _write(env_dir / ".env.comp", "PORT=6543\n")
    out = env_dir / ".env.out"
    rc = _run([str(base), str(comp), "--fix-mismatched", "--output", str(out)], env_dir)
    assert rc == 0
    assert "PORT=6543" in out.read_text()


def test_patch_skip_key(env_dir):
    base = _write(env_dir / ".env.base", "HOST=localhost\n")
    comp = _write(env_dir / ".env.comp", "HOST=localhost\nSECRET=xyz\n")
    out = env_dir / ".env.out"
    rc = _run([str(base), str(comp), "--skip", "SECRET", "--output", str(out)], env_dir)
    assert rc == 0
    assert "SECRET" not in out.read_text()


def test_patch_dry_run_no_file_written(env_dir, capsys):
    base = _write(env_dir / ".env.base", "HOST=localhost\n")
    comp = _write(env_dir / ".env.comp", "HOST=localhost\nSECRET=xyz\n")
    out = env_dir / ".env.out"
    rc = _run([str(base), str(comp), "--dry-run", "--output", str(out)], env_dir)
    assert rc == 0
    assert not out.exists()
    captured = capsys.readouterr()
    assert "SECRET" in captured.out


def test_patch_dry_run_no_changes(env_dir, capsys):
    base = _write(env_dir / ".env.base", "HOST=localhost\n")
    comp = _write(env_dir / ".env.comp", "HOST=localhost\n")
    rc = _run([str(base), str(comp), "--dry-run"], env_dir)
    assert rc == 0
    assert "No changes" in capsys.readouterr().out


def test_build_patch_parser_defaults():
    parser = build_patch_parser()
    args = parser.parse_args([".env", ".env.prod"])
    assert args.add_missing is True
    assert args.fix_mismatched is False
    assert args.dry_run is False
    assert args.skip == []
