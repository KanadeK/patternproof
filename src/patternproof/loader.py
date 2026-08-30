"""Strict loading for the versioned PatternProof JSON contract."""

from __future__ import annotations

import json
from pathlib import Path
from typing import NoReturn

from patternproof.color import parse_hex_color
from patternproof.model import PaletteEntry, Pattern, Rgb, immutable_mapping

_ROOT_FIELDS = {"version", "name", "empty_color", "palette", "cells"}
_PALETTE_FIELDS = {"name", "color"}
_MAX_GRID_SIDE = 512
_MAX_GRID_CELLS = 65_536


class PatternInputError(ValueError):
    """A stable user-facing pattern validation error."""


def _fail(path: str, message: str) -> NoReturn:
    raise PatternInputError(f"{path}: {message}")


def _as_object(value: object, path: str) -> dict[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        _fail(path, "must be an object")
    return value


def _parse_color(value: object, path: str) -> Rgb:
    try:
        return parse_hex_color(value)
    except ValueError as error:
        raise PatternInputError(f"{path}: {error}") from error


def _parse_palette(value: object) -> dict[str, PaletteEntry]:
    source = _as_object(value, "palette")
    if not source:
        _fail("palette", "must contain at least one color")
    if len(source) > 256:
        _fail("palette", "must contain no more than 256 colors")

    result: dict[str, PaletteEntry] = {}
    seen_colors: dict[Rgb, str] = {}
    for key, raw_entry in source.items():
        if not key or len(key) > 32:
            _fail("palette", "keys must contain 1 to 32 characters")
        entry = _as_object(raw_entry, f"palette.{key}")
        unknown = set(entry) - _PALETTE_FIELDS
        missing = _PALETTE_FIELDS - set(entry)
        if unknown:
            _fail(f"palette.{key}", f"unknown field(s): {', '.join(sorted(unknown))}")
        if missing:
            _fail(f"palette.{key}", f"missing field(s): {', '.join(sorted(missing))}")

        name = entry["name"]
        if not isinstance(name, str) or not name.strip() or len(name) > 120:
            _fail(f"palette.{key}.name", "must contain 1 to 120 characters")
        rgb = _parse_color(entry["color"], f"palette.{key}.color")
        if rgb in seen_colors:
            _fail(f"palette.{key}.color", f"duplicates palette color '{seen_colors[rgb]}'")
        seen_colors[rgb] = key
        result[key] = PaletteEntry(name=name.strip(), rgb=rgb)
    return result


def _parse_cells(
    value: object, palette: dict[str, PaletteEntry]
) -> tuple[tuple[str | None, ...], ...]:
    if not isinstance(value, list) or not value:
        _fail("cells", "must be a non-empty array of rows")
    if len(value) > _MAX_GRID_SIDE:
        _fail("cells", f"must contain no more than {_MAX_GRID_SIDE} rows")

    rows: list[tuple[str | None, ...]] = []
    columns: int | None = None
    for row_index, raw_row in enumerate(value):
        if not isinstance(raw_row, list) or not raw_row:
            _fail(f"cells[{row_index}]", "must be a non-empty array")
        if columns is None:
            columns = len(raw_row)
            if columns > _MAX_GRID_SIDE:
                _fail("cells", f"must contain no more than {_MAX_GRID_SIDE} columns")
        elif len(raw_row) != columns:
            _fail("cells", "must be rectangular")

        row: list[str | None] = []
        for column_index, cell in enumerate(raw_row):
            if cell is not None and (not isinstance(cell, str) or cell not in palette):
                _fail(
                    f"cells[{row_index}][{column_index}]",
                    f"unknown palette key {cell!r}",
                )
            row.append(cell)
        rows.append(tuple(row))

    assert columns is not None
    if len(rows) * columns > _MAX_GRID_CELLS:
        _fail("cells", f"must contain no more than {_MAX_GRID_CELLS} cells")
    return tuple(rows)


def load_pattern(path: Path) -> Pattern:
    """Load and strictly validate a version-one pattern file."""

    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        raise PatternInputError(f"{path}: cannot read UTF-8 pattern: {error}") from error

    try:
        raw = json.loads(text)
    except json.JSONDecodeError as error:
        raise PatternInputError(
            f"{path}: must contain valid JSON (line {error.lineno}, column {error.colno})"
        ) from error

    source = _as_object(raw, "pattern")
    unknown = set(source) - _ROOT_FIELDS
    missing = _ROOT_FIELDS - set(source)
    if unknown:
        _fail("pattern", f"unknown field(s): {', '.join(sorted(unknown))}")
    if missing:
        _fail("pattern", f"missing field(s): {', '.join(sorted(missing))}")
    if source["version"] != 1:
        _fail("version", "must be 1")

    name = source["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 160:
        _fail("name", "must contain 1 to 160 characters")
    palette = _parse_palette(source["palette"])
    cells = _parse_cells(source["cells"], palette)
    return Pattern(
        name=name.strip(),
        palette=immutable_mapping(palette),
        empty_rgb=_parse_color(source["empty_color"], "empty_color"),
        cells=cells,
    )
