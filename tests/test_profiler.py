"""Tests for envdiff.profiler."""
from __future__ import annotations

import os
import pytest

from envdiff.profiler import profile_env, EnvProfile


@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    full = os.path.join(path, ".env")
    with open(full, "w") as fh:
        fh.write(content)
    return full


def test_profile_empty_file(env_dir):
    p = _write(env_dir, "")
    result = profile_env(p)
    assert result.total_keys == 0
    assert result.empty_values == []
    assert result.duplicate_keys == []
    assert result.longest_key is None
    assert result.avg_value_length == 0.0


def test_profile_counts_keys(env_dir):
    p = _write(env_dir, "A=1\nB=2\nC=3\n")
    result = profile_env(p)
    assert result.total_keys == 3


def test_profile_detects_empty_values(env_dir):
    p = _write(env_dir, "PRESENT=hello\nEMPTY=\nALSO_EMPTY=\n")
    result = profile_env(p)
    assert "EMPTY" in result.empty_values
    assert "ALSO_EMPTY" in result.empty_values
    assert "PRESENT" not in result.empty_values


def test_profile_longest_key(env_dir):
    p = _write(env_dir, "SHORT=1\nVERY_LONG_KEY_NAME=2\n")
    result = profile_env(p)
    assert result.longest_key == "VERY_LONG_KEY_NAME"


def test_profile_longest_value_key(env_dir):
    p = _write(env_dir, "A=hi\nB=a_very_long_value_string\n")
    result = profile_env(p)
    assert result.longest_value_key == "B"


def test_profile_avg_value_length(env_dir):
    p = _write(env_dir, "A=ab\nB=abcd\n")  # lengths 2 and 4 -> avg 3.0
    result = profile_env(p)
    assert result.avg_value_length == pytest.approx(3.0)


def test_profile_detects_duplicate_keys(env_dir):
    p = _write(env_dir, "KEY=first\nOTHER=x\nKEY=second\n")
    result = profile_env(p)
    assert "KEY" in result.duplicate_keys
    assert "OTHER" not in result.duplicate_keys


def test_profile_comments_and_blanks_ignored(env_dir):
    p = _write(env_dir, "# comment\n\nREAL=value\n")
    result = profile_env(p)
    assert result.total_keys == 1


def test_profile_key_and_value_length_dicts(env_dir):
    p = _write(env_dir, "AB=xyz\n")
    result = profile_env(p)
    assert result.key_lengths["AB"] == 2
    assert result.value_lengths["AB"] == 3
