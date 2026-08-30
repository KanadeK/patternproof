"""Immutable domain models for patterns and analysis results."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType
from typing import TypeVar

Rgb = tuple[int, int, int]


class CellStatus(StrEnum):
    """Inspectable classification for one pattern cell."""

    MATCH = "match"
    BACKGROUND = "background"
    EMPTY = "empty"
    WRONG = "wrong"
    UNCERTAIN = "uncertain"


@dataclass(frozen=True, slots=True)
class PaletteEntry:
    """One named sRGB palette color."""

    name: str
    rgb: Rgb


@dataclass(frozen=True, slots=True)
class Pattern:
    """Version-one rectangular pattern after external input validation."""

    name: str
    palette: Mapping[str, PaletteEntry]
    empty_rgb: Rgb
    cells: tuple[tuple[str | None, ...], ...]

    @property
    def rows(self) -> int:
        return len(self.cells)

    @property
    def columns(self) -> int:
        return len(self.cells[0])


@dataclass(frozen=True, slots=True)
class CellResult:
    """Evidence and classification for one one-based grid coordinate."""

    row: int
    column: int
    expected: str | None
    nearest: str | None
    status: CellStatus
    observed_rgb: Rgb
    expected_delta_e: float
    nearest_delta_e: float


@dataclass(frozen=True, slots=True)
class AnalysisResult:
    """Complete deterministic result for one capture."""

    pattern_name: str
    image_width: int
    image_height: int
    delta_e_threshold: float
    inset_fraction: float
    cells: tuple[CellResult, ...]
    counts: Mapping[str, int]

    @property
    def is_clean(self) -> bool:
        return all(cell.status in {CellStatus.MATCH, CellStatus.BACKGROUND} for cell in self.cells)


_Value = TypeVar("_Value")


def immutable_mapping(values: Mapping[str, _Value]) -> Mapping[str, _Value]:
    """Return a read-only copy so parsed external objects cannot mutate the model."""

    return MappingProxyType(dict(values))
