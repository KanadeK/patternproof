from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from patternproof.cli import main


def write_inputs(tmp_path: Path, *, defect: bool = False) -> tuple[Path, Path]:
    pattern = {
        "version": 1,
        "name": "Tiny proof",
        "empty_color": "#eeebe1",
        "palette": {
            "R": {"name": "Red", "color": "#d22832"},
            "G": {"name": "Green", "color": "#28aa50"},
        },
        "cells": [["R", "G"]],
    }
    pattern_path = tmp_path / "pattern.json"
    pattern_path.write_text(json.dumps(pattern), encoding="utf-8")

    capture = Image.new("RGB", (40, 20), (40, 170, 80) if defect else (210, 40, 50))
    capture.paste((40, 170, 80), (20, 0, 40, 20))
    capture_path = tmp_path / "capture.png"
    capture.save(capture_path)
    return pattern_path, capture_path


def test_cli_clean_capture_exits_zero_and_writes_report(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pattern, capture = write_inputs(tmp_path)
    output = tmp_path / "clean-report"

    exit_code = main(["analyze", str(pattern), str(capture), "--out", str(output)])

    assert exit_code == 0
    assert (output / "report.html").is_file()
    captured = capsys.readouterr()
    assert "PASS" in captured.out
    assert "2 cells" in captured.out


def test_cli_findings_exit_one_with_exact_summary(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pattern, capture = write_inputs(tmp_path, defect=True)
    output = tmp_path / "defect-report"

    exit_code = main(
        [
            "analyze",
            str(pattern),
            str(capture),
            "--out",
            str(output),
            "--delta-e",
            "8",
        ]
    )

    assert exit_code == 1
    report = json.loads((output / "report.json").read_text(encoding="utf-8"))
    assert report["summary"]["counts"] == {"match": 1, "wrong": 1}
    captured = capsys.readouterr()
    assert "REVIEW" in captured.out
    assert "wrong=1" in captured.out


def test_cli_invalid_pattern_exits_two_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pattern = tmp_path / "invalid.json"
    pattern.write_text("[]", encoding="utf-8")
    capture = tmp_path / "capture.png"
    Image.new("RGB", (20, 20)).save(capture)
    output = tmp_path / "report"

    exit_code = main(["analyze", str(pattern), str(capture), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "ERROR" in captured.err
    assert "pattern" in captured.err


def test_cli_invalid_image_exits_two_without_output(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pattern, _ = write_inputs(tmp_path)
    capture = tmp_path / "not-an-image.png"
    capture.write_text("not an image", encoding="utf-8")
    output = tmp_path / "report"

    exit_code = main(["analyze", str(pattern), str(capture), "--out", str(output)])

    assert exit_code == 2
    assert not output.exists()
    captured = capsys.readouterr()
    assert "cannot decode capture" in captured.err


def test_cli_refuses_to_overwrite_report_directory(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    pattern, capture = write_inputs(tmp_path)
    output = tmp_path / "report"
    output.mkdir()

    exit_code = main(["analyze", str(pattern), str(capture), "--out", str(output)])

    assert exit_code == 2
    captured = capsys.readouterr()
    assert "already exists" in captured.err
