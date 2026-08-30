# Spec: PatternProof v0.1.0

## Objective

PatternProof is a local-first CLI that compares a known color-cell pattern with a
rectified, tightly cropped photograph or scan of the physical grid craft. It reports
which cells match, appear empty, contain a different known palette color, or cannot be
classified confidently. The first audience is makers of fuse-bead, diamond-painting,
and other square-grid crafts who already have a digital pattern.

The product is evidence, not a verdict: every classification retains the observed RGB,
expected color, nearest candidate, and CIELAB distance, and every finding is visible in
an overlay.

## Tech Stack

- Python 3.11+
- Pillow as the only runtime dependency
- `uv` for locked development and release environments
- pytest, pytest-cov, Ruff, mypy, build, and pip-audit for quality gates

## Commands

```console
uv sync --locked --all-groups
uv run pytest --cov=patternproof --cov-branch --cov-fail-under=90
uv run ruff format --check src tests scripts
uv run ruff check src tests scripts
uv run mypy src tests scripts
uv run python scripts/check.py
uv build
uv run patternproof analyze examples/pattern.json examples/capture.png --out build/demo
```

## Project Structure

```text
src/patternproof/       package source and CLI
tests/                  unit, integration, and CLI tests
examples/               deterministic pattern and capture fixture
docs/                   research, architecture, acceptance, and repair guides
scripts/                example generation and release-equivalent gate
tasks/                  implementation plan and checklist
.github/workflows/      cross-platform CI and tag release automation
```

## Code Style

Use immutable typed data at the domain boundary and pure functions for measurement:

```python
@dataclass(frozen=True, slots=True)
class CellResult:
    row: int
    column: int
    expected: str | None
    nearest: str | None
    status: CellStatus
    delta_e: float
```

Names describe domain behavior. Filesystem and CLI code may orchestrate; they do not
own color classification rules. Errors are explicit and are never converted to silent
defaults.

## Testing Strategy

- Unit tests cover strict schema validation, coordinate sampling, color conversion,
  classification, and status summaries.
- Integration tests analyze deterministic generated captures and inspect every artifact.
- CLI tests prove exit 0 for a clean capture, exit 1 for findings, and exit 2 for invalid
  input without an output directory.
- The full gate requires at least 90% branch coverage plus format, lint, strict typing,
  dependency audit, build, archive inspection, and clean-wheel execution.

Tests are written before the behavior they specify. Generated examples are calibration
fixtures, not claims about uncontrolled phone photography.

## Boundaries

### Always

- Validate external JSON, image dimensions, output paths, and bounded grid/image sizes.
- Preserve the exact observed evidence behind every status.
- Write reports only after inputs and analysis are complete.
- Keep outputs deterministic for the same decoded pixels and options.

### Ask first

- Changing the versioned input or report schema.
- Adding a runtime dependency or a network feature.
- Replacing the transparent threshold model with learned classification.

### Never

- Upload captures, bundle proprietary brand palettes, or infer a pattern from artwork.
- Claim that uncontrolled lighting, glare, perspective, or camera processing is corrected.
- Call an uncertain cell correct or wrong merely to avoid an inconclusive result.
- Leave partial output after invalid input or overwrite an existing report directory.

## Input Contract

The pattern is JSON schema version 1 with a rectangular `cells` array. Each cell is a
palette key or `null` for intentional background. Palette keys are 1–32 ASCII letters,
digits, dots, dashes, or underscores and begin with a letter or digit. Palette colors
and `empty_color` are six-digit hexadecimal sRGB values. The capture must be PNG, JPEG,
or WebP and already be cropped to the outside edge of the rectangular grid.

The center of each physical cell is sampled after an explicit inset. Its median RGB is
compared in CIELAB space against every palette color and `empty_color` using Delta E 76.

Statuses:

- `match`: expected is the nearest candidate and within the threshold;
- `empty`: a non-empty expected cell is nearest to the declared empty color;
- `wrong`: another known palette color is nearest and within the threshold;
- `uncertain`: no candidate is within the threshold;
- `background`: an intentional `null` cell is nearest to the empty color.

## Exit Codes

- `0`: all cells are `match` or `background`;
- `1`: at least one cell is `empty`, `wrong`, or `uncertain`; reports are written;
- `2`: CLI, input, image, or filesystem error; no new report directory remains.

## Success Criteria

- A deterministic clean fixture reports every cell correct and exits 0.
- A deterministic defect fixture identifies one empty cell, one wrong known color, and
  one uncertain cell at their exact one-based row and column, then exits 1.
- Invalid/ragged patterns and mismatched image constraints exit 2 without report output.
- JSON, CSV, overlay PNG, and self-contained HTML agree on counts and coordinates.
- The released wheel installs in a clean environment and reproduces clean/defect/invalid
  behavior through the `patternproof` console command.
- Public `main` and annotated `v0.1.0` tag CI pass; the non-draft Release contains wheel,
  sdist, example bundle, and `SHA256SUMS`.

## Open Questions

No blocking product questions. Real-capture tolerance tuning remains post-release user
validation and is explicitly outside the automated acceptance claim.
