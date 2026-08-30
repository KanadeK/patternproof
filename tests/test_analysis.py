from __future__ import annotations

import pytest
from PIL import Image, ImageDraw

from patternproof.analysis import AnalysisOptions, analyze
from patternproof.model import CellStatus, PaletteEntry, Pattern


def make_pattern(cells: tuple[tuple[str | None, ...], ...]) -> Pattern:
    return Pattern(
        name="Test grid",
        palette={
            "R": PaletteEntry(name="Red", rgb=(210, 40, 50)),
            "G": PaletteEntry(name="Green", rgb=(40, 170, 80)),
            "B": PaletteEntry(name="Blue", rgb=(40, 80, 210)),
        },
        empty_rgb=(238, 235, 225),
        cells=cells,
    )


def grid_image(colors: list[list[tuple[int, int, int]]], cell_size: int = 20) -> Image.Image:
    rows = len(colors)
    columns = len(colors[0])
    image = Image.new("RGB", (columns * cell_size, rows * cell_size))
    draw = ImageDraw.Draw(image)
    for row, values in enumerate(colors):
        for column, color in enumerate(values):
            left = column * cell_size
            top = row * cell_size
            draw.rectangle((left, top, left + cell_size - 1, top + cell_size - 1), fill=color)
    return image


def test_analyze_reports_clean_grid() -> None:
    pattern = make_pattern((("R", "G"), ("B", None)))
    capture = grid_image([[(210, 40, 50), (40, 170, 80)], [(40, 80, 210), (238, 235, 225)]])

    result = analyze(pattern, capture, AnalysisOptions(delta_e_threshold=8, inset_fraction=0.2))

    assert result.is_clean is True
    assert result.counts == {"background": 1, "match": 3}
    assert [cell.status for cell in result.cells] == [
        CellStatus.MATCH,
        CellStatus.MATCH,
        CellStatus.MATCH,
        CellStatus.BACKGROUND,
    ]


def test_analyze_distinguishes_wrong_empty_and_uncertain_cells() -> None:
    pattern = make_pattern((("R", "G", "B"),))
    capture = grid_image([[(40, 170, 80), (238, 235, 225), (115, 100, 118)]])

    result = analyze(pattern, capture, AnalysisOptions(delta_e_threshold=8, inset_fraction=0.2))

    assert [cell.status for cell in result.cells] == [
        CellStatus.WRONG,
        CellStatus.EMPTY,
        CellStatus.UNCERTAIN,
    ]
    assert result.cells[0].nearest == "G"
    assert result.cells[1].nearest is None
    assert result.cells[2].nearest_delta_e > 8
    assert result.is_clean is False


@pytest.mark.parametrize(
    "options",
    [
        AnalysisOptions(delta_e_threshold=0, inset_fraction=0.2),
        AnalysisOptions(delta_e_threshold=8, inset_fraction=0.5),
    ],
)
def test_analyze_rejects_invalid_options(options: AnalysisOptions) -> None:
    with pytest.raises(ValueError):
        analyze(make_pattern((("R",),)), grid_image([[(210, 40, 50)]]), options)


def test_analyze_rejects_cells_too_small_for_sampling() -> None:
    pattern = make_pattern((("R", "G", "B"),))

    with pytest.raises(ValueError, match="too small"):
        analyze(pattern, Image.new("RGB", (2, 1)), AnalysisOptions())
