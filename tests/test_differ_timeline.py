"""Tests for differ_timeline and cli_timeline."""
from __future__ import annotations

import json
import pathlib

import pytest

from envdiff.differ_timeline import build_timeline, DiffTimeline, TimelineEntry
from envdiff.differ import DiffResult
from envdiff.snapshotter import save_snapshot
from envdiff.cli_timeline import build_timeline_parser, run_timeline


@pytest.fixture()
def snap_dir(tmp_path: pathlib.Path):
    return tmp_path


def _save(directory: pathlib.Path, name: str, env: dict, label: str = None) -> str:
    path = str(directory / name)
    # Build a minimal DiffResult so save_snapshot is happy
    result = DiffResult(
        missing_in_compare=set(),
        missing_in_base=set(),
        mismatched=set(),
        base=env,
        compare=env,
    )
    save_snapshot(path, result, label=label, include_values=True)
    return path


def test_build_timeline_fewer_than_two_returns_empty(snap_dir):
    p = _save(snap_dir, "a.json", {"KEY": "val"})
    timeline = build_timeline([p])
    assert timeline.total_steps == 0
    assert timeline.entries == []


def test_build_timeline_two_identical_snapshots(snap_dir):
    env = {"KEY": "val", "OTHER": "x"}
    p1 = _save(snap_dir, "s1.json", env, label="v1")
    p2 = _save(snap_dir, "s2.json", env, label="v2")
    timeline = build_timeline([p1, p2])
    assert timeline.total_steps == 1
    assert timeline.steps_with_changes == 0
    assert not timeline.entries[0].has_changes


def test_build_timeline_detects_added_key(snap_dir):
    p1 = _save(snap_dir, "s1.json", {"A": "1"})
    p2 = _save(snap_dir, "s2.json", {"A": "1", "B": "2"})
    timeline = build_timeline([p1, p2])
    entry = timeline.entries[0]
    assert entry.has_changes
    assert "B" in entry.diff.missing_in_base


def test_build_timeline_detects_removed_key(snap_dir):
    p1 = _save(snap_dir, "s1.json", {"A": "1", "B": "2"})
    p2 = _save(snap_dir, "s2.json", {"A": "1"})
    timeline = build_timeline([p1, p2])
    entry = timeline.entries[0]
    assert "B" in entry.diff.missing_in_compare


def test_build_timeline_three_snapshots_produces_two_entries(snap_dir):
    p1 = _save(snap_dir, "s1.json", {"A": "1"})
    p2 = _save(snap_dir, "s2.json", {"A": "2"})
    p3 = _save(snap_dir, "s3.json", {"A": "2", "C": "3"})
    timeline = build_timeline([p1, p2, p3])
    assert timeline.total_steps == 2
    assert timeline.steps_with_changes == 2


def test_as_dict_structure(snap_dir):
    p1 = _save(snap_dir, "s1.json", {"X": "a"}, label="first")
    p2 = _save(snap_dir, "s2.json", {"X": "b"}, label="second")
    d = build_timeline([p1, p2]).as_dict()
    assert d["total_steps"] == 1
    assert d["steps_with_changes"] == 1
    entry = d["entries"][0]
    assert entry["from_label"] == "first"
    assert entry["to_label"] == "second"
    assert "mismatched" in entry


def test_cli_run_timeline_too_few_snapshots(snap_dir):
    p = _save(snap_dir, "only.json", {})
    parser = build_timeline_parser()
    args = parser.parse_args([p])
    code = run_timeline(args)
    assert code == 2


def test_cli_run_timeline_text_no_changes(snap_dir, capsys):
    env = {"K": "v"}
    p1 = _save(snap_dir, "s1.json", env)
    p2 = _save(snap_dir, "s2.json", env)
    parser = build_timeline_parser()
    args = parser.parse_args([p1, p2])
    code = run_timeline(args)
    out = capsys.readouterr().out
    assert code == 0
    assert "No changes" in out


def test_cli_run_timeline_json_format(snap_dir, capsys):
    p1 = _save(snap_dir, "s1.json", {"A": "1"})
    p2 = _save(snap_dir, "s2.json", {"A": "1", "B": "2"})
    parser = build_timeline_parser()
    args = parser.parse_args(["--format", "json", p1, p2])
    run_timeline(args)
    data = json.loads(capsys.readouterr().out)
    assert data["total_steps"] == 1


def test_cli_exit_code_flag(snap_dir):
    p1 = _save(snap_dir, "s1.json", {"A": "1"})
    p2 = _save(snap_dir, "s2.json", {"A": "2"})
    parser = build_timeline_parser()
    args = parser.parse_args(["--exit-code", p1, p2])
    code = run_timeline(args)
    assert code == 1
