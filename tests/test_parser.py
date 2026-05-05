"""Tests for envdiff.parser module."""

import textwrap
from pathlib import Path

import pytest

from envdiff.parser import parse_env_file, _strip_quotes


@pytest.fixture()
def env_file(tmp_path: Path):
    """Factory fixture that writes content to a temp .env file."""
    def _write(content: str) -> Path:
        p = tmp_path / ".env"
        p.write_text(textwrap.dedent(content), encoding="utf-8")
        return p
    return _write


def test_parse_simple_key_value(env_file):
    path = env_file("""
        APP_NAME=myapp
        DEBUG=true
    """)
    result = parse_env_file(path)
    assert result == {"APP_NAME": "myapp", "DEBUG": "true"}


def test_parse_ignores_comments_and_blanks(env_file):
    path = env_file("""
        # This is a comment
        APP_ENV=production

        # Another comment
        PORT=8080
    """)
    result = parse_env_file(path)
    assert result == {"APP_ENV": "production", "PORT": "8080"}


def test_parse_quoted_values(env_file):
    path = env_file("""
        SECRET="my secret value"
        SINGLE='another value'
    """)
    result = parse_env_file(path)
    assert result["SECRET"] == "my secret value"
    assert result["SINGLE"] == "another value"


def test_parse_empty_value(env_file):
    path = env_file("EMPTY=\n")
    result = parse_env_file(path)
    assert result["EMPTY"] is None


def test_parse_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        parse_env_file(tmp_path / "nonexistent.env")


@pytest.mark.parametrize("raw,expected", [
    ('"hello"', 'hello'),
    ("'world'", 'world'),
    ('no_quotes', 'no_quotes'),
    ('"mismatched\'', '"mismatched\''),
])
def test_strip_quotes(raw, expected):
    assert _strip_quotes(raw) == expected
