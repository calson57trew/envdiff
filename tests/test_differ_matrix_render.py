"""Focused tests for cli_matrix rendering helpers."""
from __future__ import annotations

import json

from envdiff.differ import DiffResult
from envdiff.differ_matrix import DiffMatrix, MatrixCell
from envdiff.cli_matrix import _render_text, _render_json


def _cell(base, compare, mic=(), mib=(), mm=()) -> MatrixCell:
    return MatrixCell(
        base_name=base,
        compare_name=compare,
        result=DiffResult(
            missing_in_compare=set(mic),
            missing_in_base=set(mib),
            mismatched=set(mm),
        ),
    )


def _matrix(*cells) -> DiffMatrix:
    names = list({n for c in cells for n in (c.base_name, c.compare_name)})
    return DiffMatrix(names=names, cells=list(cells))


# ---------------------------------------------------------------------------
# _render_text
# ---------------------------------------------------------------------------

def test_render_text_clean_shows_ok():
    m = _matrix(_cell("dev", "prod"))
    out = _render_text(m)
    assert "OK" in out
    assert "dev vs prod" in out


def test_render_text_dirty_shows_diff():
    m = _matrix(_cell("dev", "prod", mic=["SECRET"]))
    out = _render_text(m)
    assert "DIFF" in out
    assert "missing_in_compare: SECRET" in out


def test_render_text_mismatch_shown():
    m = _matrix(_cell("a", "b", mm=["KEY"]))
    out = _render_text(m)
    assert "mismatch: KEY" in out


def test_render_text_empty_matrix():
    m = DiffMatrix(names=[], cells=[])
    assert _render_text(m) == ""


# ---------------------------------------------------------------------------
# _render_json
# ---------------------------------------------------------------------------

def test_render_json_structure():
    m = _matrix(_cell("x", "y", mic=["A"], mib=["B"], mm=["C"]))
    data = json.loads(_render_json(m))
    assert len(data) == 1
    entry = data[0]
    assert entry["base"] == "x"
    assert entry["compare"] == "y"
    assert entry["clean"] is False
    assert "A" in entry["missing_in_compare"]
    assert "B" in entry["missing_in_base"]
    assert "C" in entry["mismatched"]


def test_render_json_clean_cell():
    m = _matrix(_cell("a", "b"))
    data = json.loads(_render_json(m))
    assert data[0]["clean"] is True
    assert data[0]["missing_in_compare"] == []


def test_render_json_keys_are_sorted():
    m = _matrix(_cell("a", "b", mic=["Z", "A", "M"]))
    data = json.loads(_render_json(m))
    assert data[0]["missing_in_compare"] == ["A", "M", "Z"]
