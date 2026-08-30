# Acceptance

These checks separate automated engineering evidence from real-capture validation.

## Release-equivalent gate

From the repository root with `uv` installed:

```console
uv sync --locked --all-groups
uv run python scripts/check.py
```

The gate must finish with `PATTERNPROOF_GATE=PASS`. It proves formatting, lint, strict
typing, at least 90% branch coverage, dependency audit, build archive inspection, and
clean-wheel execution.

## Example behavior

```console
uv run patternproof analyze examples/pattern.json examples/clean.png --out build/clean
uv run patternproof analyze examples/pattern.json examples/defects.png --out build/defects
```

Expected results:

- clean: exit `0`, `background=22`, `match=42`;
- defects: exit `1`, `background=22`, `empty=1`, `match=39`, `uncertain=1`, `wrong=1`;
- defect coordinates: `R3C3=wrong`, `R4C3=empty`, `R7C5=uncertain`;
- each new output contains `cells.csv`, `overlay.png`, `report.html`, and `report.json`.

Run each command against a new output path because overwrite refusal is intentional.

## Real-capture owner check

Automated fixtures do not establish performance under a phone camera. Before relying on
PatternProof in a real workflow, the owner should capture one known-good and one
deliberately altered craft under their usual lighting, then verify:

1. the crop follows the exact outer grid boundary and rows/columns align with the
   overlay;
2. known-good cells are not systematically marked `uncertain`;
3. the deliberate wrong and missing cells appear at the correct coordinates;
4. observed colors in the report agree with the visible central cell colors;
5. a threshold adjustment, if needed, is documented for that capture setup.

Passing this checklist is user acceptance for a capture setup. It is not implied by CI.
