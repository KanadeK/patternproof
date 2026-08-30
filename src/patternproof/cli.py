"""PatternProof command-line interface."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from PIL import Image

from patternproof import __version__
from patternproof.analysis import MAX_IMAGE_PIXELS, AnalysisOptions, analyze
from patternproof.loader import PatternInputError, load_pattern
from patternproof.reporting import ReportOutputError, write_reports


class CaptureInputError(ValueError):
    """A stable user-facing capture loading error."""


def _load_capture(path: Path) -> Image.Image:
    try:
        with Image.open(path) as source:
            if source.format not in {"PNG", "JPEG", "WEBP"}:
                raise CaptureInputError("capture must be a PNG, JPEG, or WebP image")
            if source.width * source.height > MAX_IMAGE_PIXELS:
                raise CaptureInputError(
                    f"capture contains more than {MAX_IMAGE_PIXELS} decoded pixels"
                )
            source.load()
            return source.convert("RGB")
    except (OSError, Image.DecompressionBombError) as error:
        raise CaptureInputError(f"cannot decode capture {path}: {error}") from error


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="patternproof",
        description="Compare a rectified physical grid-craft capture with a declared pattern.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    subparsers = parser.add_subparsers(dest="command", required=True)
    analyze_parser = subparsers.add_parser("analyze", help="classify every declared grid cell")
    analyze_parser.add_argument("pattern", type=Path, help="version-one pattern JSON")
    analyze_parser.add_argument("capture", type=Path, help="rectified and cropped PNG/JPEG/WebP")
    analyze_parser.add_argument("--out", type=Path, required=True, help="new report directory")
    analyze_parser.add_argument(
        "--delta-e",
        type=float,
        default=12.0,
        help="maximum CIE76 distance for a known classification (default: 12)",
    )
    analyze_parser.add_argument(
        "--inset",
        type=float,
        default=0.2,
        help="fraction excluded from each cell edge (default: 0.2)",
    )
    return parser


def _run_analyze(arguments: argparse.Namespace) -> int:
    pattern = load_pattern(arguments.pattern)
    capture = _load_capture(arguments.capture)
    result = analyze(
        pattern,
        capture,
        AnalysisOptions(
            delta_e_threshold=arguments.delta_e,
            inset_fraction=arguments.inset,
        ),
    )
    write_reports(pattern, capture, result, arguments.out)
    counts = ", ".join(f"{key}={value}" for key, value in result.counts.items())
    if result.is_clean:
        print(f"PASS {pattern.name}: {len(result.cells)} cells checked ({counts}).")
        return 0
    print(f"REVIEW {pattern.name}: {len(result.cells)} cells checked ({counts}).")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    """Run the CLI and return its stable process exit code."""

    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "analyze":
            return _run_analyze(arguments)
    except (CaptureInputError, PatternInputError, ReportOutputError, ValueError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2
    raise AssertionError(f"unhandled command: {arguments.command}")
