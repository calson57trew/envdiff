"""Pairwise diff matrix across multiple .env files."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from envdiff.differ import DiffResult, diff_envs
from envdiff.parser import parse_env_file


@dataclass
class MatrixCell:
    base_name: str
    compare_name: str
    result: DiffResult

    @property
    def is_clean(self) -> bool:
        return (
            not self.result.missing_in_compare
            and not self.result.missing_in_base
            and not self.result.mismatched
        )


@dataclass
class DiffMatrix:
    names: List[str]
    cells: List[MatrixCell] = field(default_factory=list)

    def get(self, base: str, compare: str) -> MatrixCell | None:
        for cell in self.cells:
            if cell.base_name == base and cell.compare_name == compare:
                return cell
        return None

    def dirty_pairs(self) -> List[Tuple[str, str]]:
        return [
            (c.base_name, c.compare_name)
            for c in self.cells
            if not c.is_clean
        ]

    def is_fully_clean(self) -> bool:
        return all(c.is_clean for c in self.cells)


def build_matrix(
    paths: Dict[str, str],
    check_values: bool = True,
) -> DiffMatrix:
    """Build a pairwise diff matrix from a name->path mapping."""
    names = list(paths.keys())
    envs = {name: parse_env_file(path) for name, path in paths.items()}
    cells: List[MatrixCell] = []

    for i, base_name in enumerate(names):
        for compare_name in names[i + 1 :]:
            result = diff_envs(
                envs[base_name],
                envs[compare_name],
                check_values=check_values,
            )
            cells.append(MatrixCell(base_name, compare_name, result))

    return DiffMatrix(names=names, cells=cells)
