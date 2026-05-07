"""Tests for envdiff.templater."""
from __future__ import annotations

import pytest

from envdiff.templater import (
    EnvTemplate,
    TemplateEntry,
    _make_placeholder,
    build_template,
    render_template,
)


@pytest.fixture()
def sample_env():
    return {
        "APP_NAME": "myapp",
        "DATABASE_URL": "postgres://localhost/db",
        "SECRET_KEY": "supersecret",
        "API_PASSWORD": "hunter2",
        "DEBUG": "true",
        "EMPTY_VAR": "",
        "NONE_VAR": None,
    }


def test_build_template_keys_are_sorted(sample_env):
    tmpl = build_template(sample_env)
    keys = [e.key for e in tmpl.entries]
    assert keys == sorted(keys)


def test_build_template_sensitive_values_redacted(sample_env):
    tmpl = build_template(sample_env)
    by_key = {e.key: e.placeholder for e in tmpl.entries}
    assert by_key["SECRET_KEY"] == ""
    assert by_key["API_PASSWORD"] == ""


def test_build_template_non_sensitive_values_preserved(sample_env):
    tmpl = build_template(sample_env)
    by_key = {e.key: e.placeholder for e in tmpl.entries}
    assert by_key["APP_NAME"] == "myapp"
    assert by_key["DEBUG"] == "true"


def test_build_template_empty_and_none_become_empty_string(sample_env):
    tmpl = build_template(sample_env)
    by_key = {e.key: e.placeholder for e in tmpl.entries}
    assert by_key["EMPTY_VAR"] == ""
    assert by_key["NONE_VAR"] == ""


def test_build_template_custom_placeholder(sample_env):
    tmpl = build_template(sample_env, sensitive_placeholder="CHANGE_ME")
    by_key = {e.key: e.placeholder for e in tmpl.entries}
    assert by_key["SECRET_KEY"] == "CHANGE_ME"
    assert by_key["DATABASE_URL"] == "postgres://localhost/db"


def test_render_template_produces_key_equals_value(sample_env):
    tmpl = build_template(sample_env)
    output = render_template(tmpl)
    assert "APP_NAME=myapp" in output
    assert "DEBUG=true" in output


def test_render_template_ends_with_newline(sample_env):
    tmpl = build_template(sample_env)
    assert render_template(tmpl).endswith("\n")


def test_render_template_empty_is_empty_string():
    tmpl = EnvTemplate(entries=[])
    assert render_template(tmpl) == ""


def test_render_template_includes_comment():
    tmpl = EnvTemplate(
        entries=[TemplateEntry(key="FOO", placeholder="bar", comment="A comment")]
    )
    output = render_template(tmpl)
    assert "# A comment" in output
    assert "FOO=bar" in output


def test_make_placeholder_sensitive_returns_empty():
    assert _make_placeholder("SECRET_KEY", "abc") == ""


def test_make_placeholder_non_sensitive_returns_value():
    assert _make_placeholder("APP_NAME", "myapp") == "myapp"


def test_make_placeholder_none_value_returns_empty():
    assert _make_placeholder("APP_NAME", None) == ""
