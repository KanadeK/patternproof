from __future__ import annotations

import csv
import json
from pathlib import Path

import pytest
from PIL import Image

from patternproof.analysis import AnalysisOptions, analyze
from patternproof.model import PaletteEntry, Pattern
from patternproof.reporting import ReportOutputError, write_reports


def report_fixture() -> tuple[Pattern, Image.Image]:
    pattern = Pattern(
        name="Garden <grid> & proof",
        palette={
            "R": PaletteEntry(name="Rose", rgb=(210, 40, 50)),
            "G": PaletteEntry(name="Leaf", rgb=(40, 170, 80)),
        },
        empty_rgb=(238, 235, 225),
        cells=(("R", "G"), (None, "R")),
    )
    image = Image.new("RGB", (40, 40), pattern.empty_rgb)
    image.paste(pattern.palette["G"].rgb, (0, 0, 20, 20))
    image.paste(pattern.palette["G"].rgb, (20, 0, 40, 20))
    image.paste(pattern.palette["R"].rgb, (20, 20, 40, 40))
    return pattern, image


def test_write_reports_creates_consistent_self_contained_artifacts(tmp_path: Path) -> None:
    pattern, image = report_fixture()
    result = analyze(pattern, image, AnalysisOptions(delta_e_threshold=8))
    output = tmp_path / "report"

    artifacts = write_reports(pattern, image, result, output)

    assert {path.name for path in artifacts} == {
        "cells.csv",
        "overlay.png",
        "report.html",
        "report.json",
    }
    assert {path.name for path in output.iterdir()} == {path.name for path in artifacts}

    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["schema_version"] == 1
    assert report["summary"]["counts"] == {"background": 1, "match": 2, "wrong": 1}
    assert report["cells"][0]["coordinate"] == "R1C1"
    assert report["cells"][0]["status"] == "wrong"

    with (output / "cells.csv").open(encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 4
    assert rows[0]["coordinate"] == "R1C1"
    assert rows[0]["nearest"] == "G"

    with Image.open(output / "overlay.png") as overlay:
        assert overlay.size == image.size
        assert overlay.mode == "RGB"

    html = (output / "report.html").read_text(encoding="utf-8")
    assert "Garden &lt;grid&gt; &amp; proof" in html
    assert "data:image/png;base64," in html
    assert "R1C1" in html
    assert "<script" not in html.lower()


def test_write_reports_refuses_existing_output_without_modifying_it(tmp_path: Path) -> None:
    pattern, image = report_fixture()
    result = analyze(pattern, image)
    output = tmp_path / "report"
    output.mkdir()
    marker = output / "keep.txt"
    marker.write_text("owner data", encoding="utf-8")

    with pytest.raises(ReportOutputError, match="already exists"):
        write_reports(pattern, image, result, output)

    assert marker.read_text(encoding="utf-8") == "owner data"
    assert list(tmp_path.iterdir()) == [output]
