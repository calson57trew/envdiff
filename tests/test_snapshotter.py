"""Tests for envdiff.snapshotter."""

from __future__ import annotations

import json
import os
import pytest

from envdiff.differ import DiffResult
from envdiff.snapshotter import load_snapshot, save_snapshot


@pytest.fixture()
def diff_result() -> DiffResult:
    return DiffResult(
        missing_in_compare={"ALPHA", "BETA"},
        missing_in_base={"GAMMA"},
        mismatched={"PORT": ("8080", "9090")},
    )


@pytest.fixture()
def snapshot_path(tmp_path) -> str:
    return str(tmp_path / "snapshots" / "snap.json")


def test_save_creates_file(diff_result, snapshot_path):
    save_snapshot(diff_result, snapshot_path)
    assert os.path.isfile(snapshot_path)


def test_save_creates_intermediate_directories(diff_result, tmp_path):
    """save_snapshot should create parent directories if they don't exist."""
    nested_path = str(tmp_path / "a" / "b" / "c" / "snap.json")
    save_snapshot(diff_result, nested_path)
    assert os.path.isfile(nested_path)


def test_save_snapshot_structure(diff_result, snapshot_path):
    save_snapshot(diff_result, snapshot_path, label="prod-vs-staging")
    with open(snapshot_path) as fh:
        data = json.load(fh)

    assert data["version"] == 1
    assert data["label"] == "prod-vs-staging"
    assert "created_at" in data
    assert sorted(data["missing_in_compare"]) == ["ALPHA", "BETA"]
    assert data["missing_in_base"] == ["GAMMA"]
    assert data["mismatched"]["PORT"] == {"base": "8080", "compare": "9090"}


def test_round_trip_preserves_data(diff_result, snapshot_path):
    save_snapshot(diff_result, snapshot_path)
    loaded, meta = load_snapshot(snapshot_path)

    assert loaded.missing_in_compare == diff_result.missing_in_compare
    assert loaded.missing_in_base == diff_result.missing_in_base
    assert loaded.mismatched == diff_result.mismatched


def test_load_returns_metadata(diff_result, snapshot_path):
    save_snapshot(diff_result, snapshot_path, label="ci")
    _, meta = load_snapshot(snapshot_path)

    assert meta["version"] == 1
    assert meta["label"] == "ci"
    assert meta["created_at"]  # non-empty string


def test_load_raises_on_bad_version(snapshot_path, diff_result):
    save_snapshot(diff_result, snapshot_path)
    with open(snapshot_path) as fh:
        data = json.load(fh)
    data["version"] = 99
    with open(snapshot_path, "w") as fh:
        json.dump(data, fh)

    with pytest.raises(ValueError, match="Unsupported snapshot version"):
        load_snapshot(snapshot_path)


def test_load_raises_on_missing_file(tmp_path):
    """load_snapshot should raise FileNotFoundError for a non-existent path."""
    missing = str(tmp_path / "does_not_exist.json")
    with pytest.raises(FileNotFoundError):
        load_snapshot(missing)


def test_save_empty_result(snapshot_path):
    empty = DiffResult(missing_in_compare=set(), missing_in_base=set(), mismatched={})
    save_snapshot(empty, snapshot_path)
    loaded, _ = load_snapshot(snapshot_path)

    assert loaded.missing_in_compare == set()
    assert loaded.missing_in_base == set()
    assert loaded.mismatched == {}
