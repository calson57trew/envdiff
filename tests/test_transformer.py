"""Tests for envdiff.transformer and envdiff.cli_transform."""
from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from envdiff.transformer import (
    TransformResult,
    available_operations,
    transform_env,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def sample_env():
    return {
        "db_host": "localhost",
        "DB_PORT": "5432",
        "SECRET_KEY": "abc 123",
        "EMPTY_VAR": "",
        "NONE_VAR": None,
    }


# ---------------------------------------------------------------------------
# available_operations
# ---------------------------------------------------------------------------

def test_available_operations_returns_list():
    ops = available_operations()
    assert isinstance(ops, list)
    assert "uppercase_keys" in ops
    assert "strip_values" in ops
    assert "remove_empty" in ops
    assert "quote_spaces" in ops


# ---------------------------------------------------------------------------
# transform_env — individual ops
# ---------------------------------------------------------------------------

def test_uppercase_keys(sample_env):
    result = transform_env(sample_env, ["uppercase_keys"])
    assert "db_host" not in result.transformed
    assert "DB_HOST" in result.transformed
    assert result.applied == ["uppercase_keys"]


def test_strip_values():
    env = {"KEY": "  hello  ", "OTHER": "clean"}
    result = transform_env(env, ["strip_values"])
    assert result.transformed["KEY"] == "hello"
    assert result.transformed["OTHER"] == "clean"


def test_remove_empty(sample_env):
    result = transform_env(sample_env, ["remove_empty"])
    assert "EMPTY_VAR" not in result.transformed
    assert "NONE_VAR" not in result.transformed
    assert "DB_PORT" in result.transformed


def test_quote_spaces():
    env = {"MSG": "hello world", "PLAIN": "nospace"}
    result = transform_env(env, ["quote_spaces"])
    assert result.transformed["MSG"] == '"hello world"'
    assert result.transformed["PLAIN"] == "nospace"


def test_quote_spaces_already_quoted():
    env = {"MSG": '"already quoted"'}
    result = transform_env(env, ["quote_spaces"])
    assert result.transformed["MSG"] == '"already quoted"'


# ---------------------------------------------------------------------------
# transform_env — chaining & metadata
# ---------------------------------------------------------------------------

def test_chained_ops(sample_env):
    result = transform_env(sample_env, ["uppercase_keys", "remove_empty"])
    assert "DB_HOST" in result.transformed
    assert "EMPTY_VAR" not in result.transformed
    assert result.applied == ["uppercase_keys", "remove_empty"]


def test_no_ops_is_unchanged(sample_env):
    result = transform_env(sample_env, [])
    assert result.is_unchanged
    assert result.changed_keys == []


def test_changed_keys_reported():
    env = {"KEY": "  value  "}
    result = transform_env(env, ["strip_values"])
    assert "KEY" in result.changed_keys


def test_unknown_op_raises():
    with pytest.raises(ValueError, match="Unknown operation"):
        transform_env({}, ["nonexistent_op"])


# ---------------------------------------------------------------------------
# TransformResult.as_dict
# ---------------------------------------------------------------------------

def test_as_dict_structure():
    env = {"A": "1", "B": ""}
    result = transform_env(env, ["remove_empty"])
    d = result.as_dict()
    assert "applied" in d
    assert "changed_keys" in d
    assert "is_unchanged" in d
    assert "transformed" in d


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path: Path, content: str) -> Path:
    path.write_text(textwrap.dedent(content))
    return path


def _run(argv):
    from envdiff.cli_transform import build_transform_parser, run_transform
    parser = build_transform_parser()
    args = parser.parse_args(argv)
    return run_transform(args)


def test_cli_dotenv_output(env_dir):
    f = _write(env_dir / ".env", """\
        db_host=localhost
        db_port=5432
    """)
    rc = _run([str(f), "--ops", "uppercase_keys"])
    assert rc == 0


def test_cli_json_output(env_dir, capsys):
    f = _write(env_dir / ".env", "KEY=value\n")
    rc = _run([str(f), "--format", "json", "--ops", "uppercase_keys"])
    assert rc == 0
    captured = capsys.readouterr()
    data = json.loads(captured.out)
    assert "KEY" in data


def test_cli_show_diff(env_dir, capsys):
    f = _write(env_dir / ".env", "key=value\n")
    rc = _run([str(f), "--ops", "uppercase_keys", "--show-diff"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "key" in captured.out


def test_cli_no_ops_show_diff_unchanged(env_dir, capsys):
    f = _write(env_dir / ".env", "KEY=value\n")
    rc = _run([str(f), "--show-diff"])
    assert rc == 0
    captured = capsys.readouterr()
    assert "No changes" in captured.out


def test_cli_unknown_op_returns_2(env_dir):
    f = _write(env_dir / ".env", "KEY=value\n")
    rc = _run([str(f), "--ops", "bad_op"])
    assert rc == 2
