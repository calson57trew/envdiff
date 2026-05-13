"""Tests for envdiff.renamer and envdiff.cli_rename."""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.renamer import rename_keys, has_renames, RenameResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def base_env() -> dict:
    return {"OLD_KEY": "value1", "KEEP": "value2", "ANOTHER": "value3"}


# ---------------------------------------------------------------------------
# Unit tests – renamer module
# ---------------------------------------------------------------------------

def test_rename_single_key(base_env):
    result = rename_keys(base_env, {"OLD_KEY": "NEW_KEY"})
    assert "NEW_KEY" in result.output
    assert "OLD_KEY" not in result.output
    assert result.renamed == {"OLD_KEY": "NEW_KEY"}
    assert result.skipped == []


def test_rename_preserves_value(base_env):
    result = rename_keys(base_env, {"OLD_KEY": "NEW_KEY"})
    assert result.output["NEW_KEY"] == "value1"


def test_rename_missing_key_goes_to_skipped(base_env):
    result = rename_keys(base_env, {"MISSING": "NEW_KEY"})
    assert "MISSING" in result.skipped
    assert not result.renamed


def test_rename_no_overwrite_skips_existing_target(base_env):
    env = {"A": "1", "B": "2"}
    result = rename_keys(env, {"A": "B"}, overwrite=False)
    assert "A" in result.skipped
    assert result.output["B"] == "2"  # original value preserved


def test_rename_overwrite_replaces_existing_target():
    env = {"A": "1", "B": "2"}
    result = rename_keys(env, {"A": "B"}, overwrite=True)
    assert result.output["B"] == "1"
    assert "A" not in result.output
    assert result.renamed == {"A": "B"}


def test_has_renames_true_when_renamed():
    r = RenameResult(renamed={"X": "Y"}, skipped=[], output={})
    assert has_renames(r) is True


def test_has_renames_false_when_empty():
    r = RenameResult(renamed={}, skipped=["X"], output={})
    assert has_renames(r) is False


def test_rename_multiple_keys(base_env):
    mapping = {"OLD_KEY": "NEW_KEY", "KEEP": "RETAINED"}
    result = rename_keys(base_env, mapping)
    assert set(result.renamed.keys()) == {"OLD_KEY", "KEEP"}
    assert "ANOTHER" in result.output  # untouched key still present


# ---------------------------------------------------------------------------
# CLI tests
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content))
    return path


def _run(args: list[str]):
    """Run run_rename with parsed args; return (exit_code, stdout, stderr)."""
    import io
    import sys
    from envdiff.cli_rename import build_rename_parser, run_rename

    parser = build_rename_parser()
    namespace = parser.parse_args(args)
    captured_out = io.StringIO()
    captured_err = io.StringIO()
    old_out, old_err = sys.stdout, sys.stderr
    sys.stdout, sys.stderr = captured_out, captured_err
    try:
        code = run_rename(namespace)
    finally:
        sys.stdout, sys.stderr = old_out, old_err
    return code, captured_out.getvalue(), captured_err.getvalue()


def test_cli_env_output(env_dir):
    f = _write(env_dir / ".env", "OLD_KEY=hello\nKEEP=world\n")
    code, out, _ = _run([str(f), "--map", "OLD_KEY=NEW_KEY"])
    assert code == 0
    assert "NEW_KEY=hello" in out
    assert "KEEP=world" in out


def test_cli_json_output(env_dir):
    f = _write(env_dir / ".env", "FOO=bar\n")
    code, out, _ = _run([str(f), "--map", "FOO=BAZ", "--format", "json"])
    assert code == 0
    data = json.loads(out)
    assert data["renamed"] == {"FOO": "BAZ"}
    assert "BAZ" in data["output"]


def test_cli_skipped_reported_to_stderr(env_dir):
    f = _write(env_dir / ".env", "A=1\n")
    _, _, err = _run([str(f), "--map", "MISSING=NEW"])
    assert "MISSING" in err


def test_cli_exit_code_flag_on_skip(env_dir):
    f = _write(env_dir / ".env", "A=1\n")
    code, _, _ = _run([str(f), "--map", "MISSING=NEW", "--exit-code"])
    assert code == 1


def test_cli_exit_code_zero_when_no_skips(env_dir):
    f = _write(env_dir / ".env", "A=1\n")
    code, _, _ = _run([str(f), "--map", "A=B", "--exit-code"])
    assert code == 0
