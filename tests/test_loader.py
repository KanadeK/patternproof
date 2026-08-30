from __future__ import annotations

import json
from pathlib import Path

import pytest

from patternproof.loader import PatternInputError, load_pattern


def write_pattern(path: Path, data: object) -> Path:
    path.write_text(json.dumps(data), encoding="utf-8")
    return path


def valid_pattern() -> dict[str, object]:
    return {
        "version": 1,
        "name": "Tiny flower",
        "empty_color": "#f2eee8",
        "palette": {
            "R": {"name": "Rose", "color": "#d84a62"},
            "G": {"name": "Leaf", "color": "#4f8a55"},
        },
        "cells": [["R", None], ["G", "R"]],
    }


def test_load_pattern_returns_immutable_rectangular_model(tmp_path: Path) -> None:
    pattern = load_pattern(write_pattern(tmp_path / "pattern.json", valid_pattern()))

    assert pattern.name == "Tiny flower"
    assert pattern.rows == 2
    assert pattern.columns == 2
    assert pattern.cells == (("R", None), ("G", "R"))
    assert pattern.palette["R"].rgb == (216, 74, 98)
    assert pattern.empty_rgb == (242, 238, 232)


@pytest.mark.parametrize(
    ("mutate", "message"),
    [
        (lambda data: data.update(version=2), "version"),
        (lambda data: data.update(extra=True), "unknown field"),
        (lambda data: data.update(cells=[["R"], ["G", "R"]]), "rectangular"),
        (lambda data: data.update(cells=[["UNKNOWN"]]), "unknown palette key"),
        (lambda data: data.update(palette={}), "palette"),
        (lambda data: data.pop("name"), "missing field"),
        (lambda data: data.update(name=""), "name"),
        (lambda data: data.update(empty_color="not-a-color"), "empty_color"),
        (lambda data: data.update(cells=[]), "non-empty array"),
        (lambda data: data.update(cells=[[]]), "non-empty array"),
        (
            lambda data: data.update(
                palette={
                    "R": {"name": "Rose", "color": "#d84a62"},
                    "G": {"name": "Leaf", "color": "#d84a62"},
                }
            ),
            "duplicates palette color",
        ),
    ],
)
def test_load_pattern_rejects_invalid_schema(
    tmp_path: Path,
    mutate: object,
    message: str,
) -> None:
    data = valid_pattern()
    assert callable(mutate)
    mutate(data)

    with pytest.raises(PatternInputError, match=message):
        load_pattern(write_pattern(tmp_path / "bad.json", data))


def test_load_pattern_rejects_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "bad.json"
    path.write_text("{not json", encoding="utf-8")

    with pytest.raises(PatternInputError, match="valid JSON"):
        load_pattern(path)


def test_load_pattern_rejects_non_object_root(tmp_path: Path) -> None:
    with pytest.raises(PatternInputError, match="pattern: must be an object"):
        load_pattern(write_pattern(tmp_path / "array.json", []))


def test_load_pattern_reports_unreadable_path(tmp_path: Path) -> None:
    with pytest.raises(PatternInputError, match="cannot read UTF-8 pattern"):
        load_pattern(tmp_path / "missing.json")
