"""Tests for envdiff.cli_template."""
from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from envdiff.cli_template import build_template_parser, run_template


@pytest.fixture()
def env_dir(tmp_path: Path) -> Path:
    return tmp_path


def _write(directory: Path, name: str, content: str) -> Path:
    p = directory / name
    p.write_text(textwrap.dedent(content), encoding="utf-8")
    return p


def _run(args: list[str]):
    parser = build_template_parser()
    return parser.parse_args(args)


def test_build_template_parser_defaults():
    ns = _run(["some.env"])
    assert ns.env_file == "some.env"
    assert ns.output is None
    assert ns.placeholder == ""


def test_build_template_parser_custom_placeholder():
    ns = _run(["some.env", "--placeholder", "CHANGE_ME"])
    assert ns.placeholder == "CHANGE_ME"


def test_run_template_missing_file_returns_2(env_dir, capsys):
    ns = _run([str(env_dir / "nonexistent.env")])
    code = run_template(ns)
    assert code == 2
    captured = capsys.readouterr()
    assert "not found" in captured.err


def test_run_template_stdout(env_dir, capsys):
    src = _write(env_dir, ".env", """\
        APP_NAME=myapp
        SECRET_KEY=supersecret
        DEBUG=true
    """)
    ns = _run([str(src)])
    code = run_template(ns)
    assert code == 0
    captured = capsys.readouterr()
    assert "APP_NAME=myapp" in captured.out
    assert "SECRET_KEY=" in captured.out
    # sensitive value must not appear
    assert "supersecret" not in captured.out


def test_run_template_writes_output_file(env_dir):
    src = _write(env_dir, ".env", "FOO=bar\nBAZ=qux\n")
    out_path = env_dir / ".env.example"
    ns = _run([str(src), "-o", str(out_path)])
    code = run_template(ns)
    assert code == 0
    assert out_path.exists()
    content = out_path.read_text()
    assert "FOO=bar" in content


def test_run_template_custom_placeholder_in_output(env_dir, capsys):
    src = _write(env_dir, ".env", "PASSWORD=hunter2\nAPP=myapp\n")
    ns = _run([str(src), "--placeholder", "CHANGE_ME"])
    run_template(ns)
    captured = capsys.readouterr()
    assert "CHANGE_ME" in captured.out
    assert "hunter2" not in captured.out
