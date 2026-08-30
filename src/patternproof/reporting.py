"""Transactional, inspectable report generation."""

from __future__ import annotations

import base64
import csv
import html
import io
import json
import shutil
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw

from patternproof.model import AnalysisResult, CellResult, CellStatus, Pattern, Rgb

_ARTIFACT_NAMES = ("cells.csv", "overlay.png", "report.html", "report.json")
_STATUS_COLORS: dict[CellStatus, str] = {
    CellStatus.MATCH: "#22c55e",
    CellStatus.BACKGROUND: "#14b8a6",
    CellStatus.EMPTY: "#f97316",
    CellStatus.WRONG: "#ef4444",
    CellStatus.UNCERTAIN: "#eab308",
}


class ReportOutputError(OSError):
    """A stable user-facing output boundary error."""


def _hex_color(rgb: Rgb) -> str:
    return f"#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}"


def _coordinate(cell: CellResult) -> str:
    return f"R{cell.row}C{cell.column}"


def _cell_record(cell: CellResult) -> dict[str, object]:
    return {
        "coordinate": _coordinate(cell),
        "row": cell.row,
        "column": cell.column,
        "status": cell.status.value,
        "expected": cell.expected,
        "nearest": cell.nearest,
        "observed_rgb": list(cell.observed_rgb),
        "observed_hex": _hex_color(cell.observed_rgb),
        "expected_delta_e": round(cell.expected_delta_e, 4),
        "nearest_delta_e": round(cell.nearest_delta_e, 4),
    }


def _report_document(pattern: Pattern, result: AnalysisResult) -> dict[str, object]:
    return {
        "schema_version": 1,
        "pattern": {
            "name": pattern.name,
            "rows": pattern.rows,
            "columns": pattern.columns,
            "empty_color": _hex_color(pattern.empty_rgb),
            "palette": {
                key: {"name": entry.name, "color": _hex_color(entry.rgb)}
                for key, entry in sorted(pattern.palette.items())
            },
        },
        "capture": {"width": result.image_width, "height": result.image_height},
        "policy": {
            "color_space": "CIELAB D65",
            "distance": "CIE76",
            "delta_e_threshold": result.delta_e_threshold,
            "inset_fraction": result.inset_fraction,
        },
        "summary": {
            "clean": result.is_clean,
            "total_cells": len(result.cells),
            "counts": dict(result.counts),
        },
        "cells": [_cell_record(cell) for cell in result.cells],
    }


def _write_json(path: Path, pattern: Pattern, result: AnalysisResult) -> None:
    path.write_text(
        json.dumps(_report_document(pattern, result), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )


def _write_csv(path: Path, result: AnalysisResult) -> None:
    fieldnames = [
        "coordinate",
        "row",
        "column",
        "status",
        "expected",
        "nearest",
        "observed_hex",
        "expected_delta_e",
        "nearest_delta_e",
    ]
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for cell in result.cells:
            record = _cell_record(cell)
            writer.writerow({field: record[field] for field in fieldnames})


def _render_overlay(capture: Image.Image, pattern: Pattern, result: AnalysisResult) -> Image.Image:
    overlay = capture.convert("RGB")
    draw = ImageDraw.Draw(overlay)
    cell_width = overlay.width / pattern.columns
    cell_height = overlay.height / pattern.rows
    line_width = max(1, round(min(cell_width, cell_height) / 12))
    for cell in result.cells:
        left = round((cell.column - 1) * cell_width)
        top = round((cell.row - 1) * cell_height)
        right = round(cell.column * cell_width) - 1
        bottom = round(cell.row * cell_height) - 1
        draw.rectangle(
            (left, top, right, bottom),
            outline=_STATUS_COLORS[cell.status],
            width=line_width,
        )
    return overlay


def _png_bytes(image: Image.Image) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, format="PNG", optimize=False)
    return buffer.getvalue()


def _write_html(
    path: Path,
    pattern: Pattern,
    result: AnalysisResult,
    overlay_png: bytes,
) -> None:
    summary = " ".join(
        f'<span class="pill {html.escape(key)}">{html.escape(key)}={count}</span>'
        for key, count in result.counts.items()
    )
    rows = "\n".join(
        "<tr>"
        f"<td>{_coordinate(cell)}</td>"
        f'<td><span class="status {cell.status.value}">{cell.status.value}</span></td>'
        f"<td>{html.escape(cell.expected or 'background')}</td>"
        f"<td>{html.escape(cell.nearest or 'empty')}</td>"
        f"<td><code>{_hex_color(cell.observed_rgb)}</code></td>"
        f"<td>{cell.expected_delta_e:.2f}</td>"
        f"<td>{cell.nearest_delta_e:.2f}</td>"
        "</tr>"
        for cell in result.cells
    )
    overlay_data = base64.b64encode(overlay_png).decode("ascii")
    title = html.escape(pattern.name)
    verdict = "PASS" if result.is_clean else "REVIEW"
    document = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PatternProof — {title}</title>
<style>
:root {{ color-scheme: dark; font-family: Inter, ui-sans-serif, system-ui, sans-serif; }}
body {{ margin: 0; background: #0d1117; color: #e6edf3; }}
main {{ width: min(1100px, calc(100% - 32px)); margin: 32px auto 64px; }}
h1 {{ margin-bottom: 4px; }} .muted {{ color: #9da7b3; }}
.summary {{ display: flex; gap: 8px; flex-wrap: wrap; margin: 20px 0; }}
.pill, .status {{ border-radius: 999px; padding: 4px 9px; background: #21262d; }}
.wrong, .empty {{ color: #ff938a; }} .uncertain {{ color: #eac54f; }}
.match {{ color: #56d364; }} .background {{ color: #39c5cf; }}
figure {{ margin: 24px 0; }}
img {{ max-width: 100%; image-rendering: pixelated; border: 1px solid #30363d; }}
table {{ width: 100%; border-collapse: collapse; background: #161b22; }}
th, td {{ padding: 9px 10px; border: 1px solid #30363d; text-align: left; }}
th {{ background: #21262d; }} code {{ color: #a5d6ff; }}
</style>
</head>
<body><main>
<p class="muted">
PatternProof schema 1 · CIELAB D65 / CIE76 · threshold {result.delta_e_threshold:g}
</p>
<h1>{verdict}: {title}</h1>
<p>{len(result.cells)} cells from a {pattern.rows} x {pattern.columns} declared grid.</p>
<div class="summary">{summary}</div>
<figure>
<img alt="Capture with cell status outlines" src="data:image/png;base64,{overlay_data}">
</figure>
<h2>Cell evidence</h2>
<table><thead><tr>
<th>Cell</th><th>Status</th><th>Expected</th><th>Nearest</th><th>Observed</th>
<th>ΔE expected</th><th>ΔE nearest</th>
</tr></thead>
<tbody>{rows}</tbody></table>
<p class="muted">
A report is evidence from one controlled capture, not a guarantee about the physical craft.
</p>
</main></body></html>
"""
    path.write_text(document, encoding="utf-8", newline="\n")


def _populate_reports(
    directory: Path,
    pattern: Pattern,
    capture: Image.Image,
    result: AnalysisResult,
) -> None:
    overlay_png = _png_bytes(_render_overlay(capture, pattern, result))
    (directory / "overlay.png").write_bytes(overlay_png)
    _write_json(directory / "report.json", pattern, result)
    _write_csv(directory / "cells.csv", result)
    _write_html(directory / "report.html", pattern, result, overlay_png)


def write_reports(
    pattern: Pattern,
    capture: Image.Image,
    result: AnalysisResult,
    output: Path,
) -> tuple[Path, ...]:
    """Write all reports atomically and refuse to replace an existing path."""

    if output.exists():
        raise ReportOutputError(f"output path already exists: {output}")
    try:
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = Path(tempfile.mkdtemp(prefix=f".{output.name}-", dir=output.parent))
    except OSError as error:
        raise ReportOutputError(f"cannot prepare output path {output}: {error}") from error

    try:
        _populate_reports(temporary, pattern, capture, result)
        temporary.rename(output)
    except OSError as error:
        raise ReportOutputError(f"cannot write report directory {output}: {error}") from error
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
    return tuple(output / name for name in _ARTIFACT_NAMES)
