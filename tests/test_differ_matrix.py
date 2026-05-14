"""Tests for envdiff.differ_matrix."""
from __future__ import annotations

import os
import pytest

from envdiff.differ import DiffResult
from envdiff.differ_matrix import MatrixCell, DiffMatrix, build_matrix


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

@pytest.fixture()
def env_dir(tmp_path):
    return tmp_path


def _write(path, content: str) -> str:
    p = path
    p.write_text(content)
    return str(p)


# ---------------------------------------------------------------------------
# MatrixCell
# ---------------------------------------------------------------------------

def _make_cell(mic=(), mib=(), mm=()) -> MatrixCell:
    result = DiffResult(
        missing_in_compare=set(mic),
        missing_in_base=set(mib),
        mismatched=set(mm),
    )
    return MatrixCell(base_name="a", compare_name="b", result=result)


def test_matrix_cell_clean_when_no_diffs():
    assert _make_cell().is_clean


def test_matrix_cell_dirty_when_missing_in_compare():
    assert not _make_cell(mic=["KEY"]).is_clean


def test_matrix_cell_dirty_when_mismatch():
    assert not _make_cell(mm=["KEY"]).is_clean


# ---------------------------------------------------------------------------
# DiffMatrix
# ---------------------------------------------------------------------------

def test_diff_matrix_get_returns_correct_cell():
    cell = _make_cell()
    matrix = DiffMatrix(names=["a", "b"], cells=[cell])
    assert matrix.get("a", "b") is cell


def test_diff_matrix_get_returns_none_for_unknown():
    matrix = DiffMatrix(names=["a", "b"], cells=[])
    assert matrix.get("a", "b") is None


def test_diff_matrix_dirty_pairs():
    clean = _make_cell()
    dirty = MatrixCell("c", "d", DiffResult(missing_in_compare={"X"}, missing_in_base=set(), mismatched=set()))
    matrix = DiffMatrix(names=["a", "b", "c", "d"], cells=[clean, dirty])
    assert matrix.dirty_pairs() == [("c", "d")]


def test_diff_matrix_is_fully_clean_true():
    matrix = DiffMatrix(names=["a", "b"], cells=[_make_cell()])
    assert matrix.is_fully_clean()


def test_diff_matrix_is_fully_clean_false():
    dirty = MatrixCell("a", "b", DiffResult(missing_in_compare={"K"}, missing_in_base=set(), mismatched=set()))
    matrix = DiffMatrix(names=["a", "b"], cells=[dirty])
    assert not matrix.is_fully_clean()


# ---------------------------------------------------------------------------
# build_matrix
# ---------------------------------------------------------------------------

def test_build_matrix_identical_files_are_clean(env_dir):
    content = "FOO=bar\nBAZ=qux\n"
    a = _write(env_dir / "a.env", content)
    b = _write(env_dir / "b.env", content)
    matrix = build_matrix({"a": a, "b": b})
    assert matrix.is_fully_clean()


def test_build_matrix_detects_missing_key(env_dir):
    a = _write(env_dir / "a.env", "FOO=bar\nEXTRA=1\n")
    b = _write(env_dir / "b.env", "FOO=bar\n")
    matrix = build_matrix({"a": a, "b": b})
    cell = matrix.get("a", "b")
    assert cell is not None
    assert "EXTRA" in cell.result.missing_in_compare


def test_build_matrix_no_values_ignores_mismatch(env_dir):
    a = _write(env_dir / "a.env", "FOO=one\n")
    b = _write(env_dir / "b.env", "FOO=two\n")
    matrix = build_matrix({"a": a, "b": b}, check_values=False)
    assert matrix.is_fully_clean()


def test_build_matrix_three_files_produces_three_cells(env_dir):
    content = "KEY=val\n"
    paths = {
        name: _write(env_dir / f"{name}.env", content)
        for name in ("dev", "staging", "prod")
    }
    matrix = build_matrix(paths)
    assert len(matrix.cells) == 3
