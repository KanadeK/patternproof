"""Deterministic per-cell capture analysis."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from PIL import Image, ImageStat

from patternproof.color import delta_e76, rgb_to_lab
from patternproof.model import (
    AnalysisResult,
    CellResult,
    CellStatus,
    Pattern,
    Rgb,
    immutable_mapping,
)

MAX_IMAGE_PIXELS = 40_000_000
_MIN_CELL_PIXELS = 4


@dataclass(frozen=True, slots=True)
class AnalysisOptions:
    """Explicit classification policy for one run."""

    delta_e_threshold: float = 12.0
    inset_fraction: float = 0.2


_DEFAULT_OPTIONS = AnalysisOptions()


def _validate_options(options: AnalysisOptions) -> None:
    if not 0 < options.delta_e_threshold <= 100:
        raise ValueError("delta_e_threshold must be greater than 0 and at most 100")
    if not 0 <= options.inset_fraction < 0.5:
        raise ValueError("inset_fraction must be at least 0 and less than 0.5")


def _sample_cell(
    image: Image.Image,
    *,
    row: int,
    column: int,
    rows: int,
    columns: int,
    inset_fraction: float,
) -> Rgb:
    left = column * image.width // columns
    right = (column + 1) * image.width // columns
    top = row * image.height // rows
    bottom = (row + 1) * image.height // rows
    cell_width = right - left
    cell_height = bottom - top
    if cell_width < _MIN_CELL_PIXELS or cell_height < _MIN_CELL_PIXELS:
        raise ValueError(
            "capture is too small for the declared grid; every cell must be at least "
            f"{_MIN_CELL_PIXELS} by {_MIN_CELL_PIXELS} pixels"
        )

    x_inset = int(cell_width * inset_fraction)
    y_inset = int(cell_height * inset_fraction)
    crop = image.crop((left + x_inset, top + y_inset, right - x_inset, bottom - y_inset))
    median = ImageStat.Stat(crop).median
    return (round(median[0]), round(median[1]), round(median[2]))


def _classify(
    pattern: Pattern,
    expected: str | None,
    observed: Rgb,
    threshold: float,
) -> tuple[str | None, CellStatus, float, float]:
    observed_lab = rgb_to_lab(observed)
    expected_rgb = pattern.empty_rgb if expected is None else pattern.palette[expected].rgb
    expected_delta = delta_e76(observed_lab, rgb_to_lab(expected_rgb))

    candidates: list[tuple[str | None, Rgb]] = [(None, pattern.empty_rgb)]
    candidates.extend((key, pattern.palette[key].rgb) for key in sorted(pattern.palette))
    distances = [
        (delta_e76(observed_lab, rgb_to_lab(rgb)), "" if key is None else key, key)
        for key, rgb in candidates
    ]
    nearest_delta, _, nearest = min(distances)

    if nearest_delta > threshold:
        status = CellStatus.UNCERTAIN
    elif nearest is None:
        status = CellStatus.BACKGROUND if expected is None else CellStatus.EMPTY
    elif nearest == expected:
        status = CellStatus.MATCH
    else:
        status = CellStatus.WRONG
    return nearest, status, expected_delta, nearest_delta


def analyze(
    pattern: Pattern,
    capture: Image.Image,
    options: AnalysisOptions = _DEFAULT_OPTIONS,
) -> AnalysisResult:
    """Compare every declared grid cell with the median color in its capture region."""

    _validate_options(options)
    if capture.width <= 0 or capture.height <= 0:
        raise ValueError("capture must have positive dimensions")
    if capture.width * capture.height > MAX_IMAGE_PIXELS:
        raise ValueError(f"capture must contain no more than {MAX_IMAGE_PIXELS} decoded pixels")

    image = capture.convert("RGB")
    cell_results: list[CellResult] = []
    for row_index, row in enumerate(pattern.cells):
        for column_index, expected in enumerate(row):
            observed = _sample_cell(
                image,
                row=row_index,
                column=column_index,
                rows=pattern.rows,
                columns=pattern.columns,
                inset_fraction=options.inset_fraction,
            )
            nearest, status, expected_delta, nearest_delta = _classify(
                pattern, expected, observed, options.delta_e_threshold
            )
            cell_results.append(
                CellResult(
                    row=row_index + 1,
                    column=column_index + 1,
                    expected=expected,
                    nearest=nearest,
                    status=status,
                    observed_rgb=observed,
                    expected_delta_e=expected_delta,
                    nearest_delta_e=nearest_delta,
                )
            )

    counts = Counter(cell.status.value for cell in cell_results)
    return AnalysisResult(
        pattern_name=pattern.name,
        image_width=image.width,
        image_height=image.height,
        delta_e_threshold=options.delta_e_threshold,
        inset_fraction=options.inset_fraction,
        cells=tuple(cell_results),
        counts=immutable_mapping({key: counts[key] for key in sorted(counts)}),
    )
