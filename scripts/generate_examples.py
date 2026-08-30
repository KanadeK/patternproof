"""Generate the committed PatternProof example pattern and captures."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence
from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
CELL_SIZE = 64
EMPTY = "#eee9df"
COLORS = {
    "R": "#d84a62",
    "G": "#4f8a55",
    "Y": "#e4aa35",
}
CELLS: list[list[str | None]] = [
    [None, None, "Y", "Y", "Y", "Y", None, None],
    [None, "Y", "R", "R", "R", "R", "Y", None],
    ["Y", "R", "R", "R", "R", "R", "R", "Y"],
    ["Y", "R", "R", "Y", "Y", "R", "R", "Y"],
    [None, "Y", "R", "R", "R", "R", "Y", None],
    [None, None, "Y", "R", "R", "Y", None, None],
    [None, None, None, "G", "G", None, None, None],
    [None, None, "G", "G", "G", "G", None, None],
]


def _pattern_document() -> dict[str, object]:
    return {
        "version": 1,
        "name": "Pocket flower",
        "empty_color": EMPTY,
        "palette": {
            "G": {"name": "Leaf", "color": COLORS["G"]},
            "R": {"name": "Petal", "color": COLORS["R"]},
            "Y": {"name": "Outline", "color": COLORS["Y"]},
        },
        "cells": CELLS,
    }


def _render_capture(overrides: dict[tuple[int, int], str | None]) -> Image.Image:
    image = Image.new("RGB", (len(CELLS[0]) * CELL_SIZE, len(CELLS) * CELL_SIZE), EMPTY)
    draw = ImageDraw.Draw(image)
    for row, cells in enumerate(CELLS):
        for column, expected in enumerate(cells):
            observed = overrides.get((row, column), expected)
            if observed is None:
                continue
            color = COLORS.get(observed, observed)
            left = column * CELL_SIZE + 9
            top = row * CELL_SIZE + 9
            right = (column + 1) * CELL_SIZE - 10
            bottom = (row + 1) * CELL_SIZE - 10
            draw.ellipse((left + 2, top + 3, right + 2, bottom + 3), fill="#d8d0c3")
            draw.ellipse((left, top, right, bottom), fill=color, outline="#ffffff", width=2)
    return image


def main(argv: Sequence[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "examples")
    output = parser.parse_args(argv).output
    output.mkdir(parents=True, exist_ok=True)
    (output / "pattern.json").write_text(
        json.dumps(_pattern_document(), indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    _render_capture({}).save(output / "clean.png")
    _render_capture(
        {
            (2, 2): "G",  # wrong: a leaf-green bead replaces a petal
            (3, 2): None,  # empty: the expected petal is missing
            (6, 4): "#76569c",  # uncertain: this purple is outside the declared palette
        }
    ).save(output / "defects.png")


if __name__ == "__main__":
    main()
