# Troubleshooting

## Many cells are uncertain

The capture or palette is outside the default CIE76 threshold. First correct glare,
shadow, white balance, and crop alignment. Confirm that the JSON colors describe the
actual material under the same lighting. Only then try a small explicit threshold
change such as `--delta-e 15`; a larger threshold also makes distinct colors easier to
confuse.

## Findings shift by one row or column

The image is not cropped to the exact outside grid boundary, or it still has perspective
distortion. PatternProof divides the entire image evenly; it does not search for grid
lines. Rectify and recrop rather than editing the pattern to compensate.

## Correct cells appear empty

Check `empty_color` and the cell center. Transparent, reflective, very small, or hollow
materials may expose too much background inside the default sample. A smaller `--inset`
samples more of the cell; a larger inset samples less edge/background. Keep it below
`0.5`.

## `output path already exists`

Reports are immutable evidence for one run. Choose a new directory or deliberately move
the old report elsewhere; PatternProof will not merge or overwrite it.

## Capture is too small

Every declared cell needs at least 4 by 4 decoded pixels before the inset. Use a larger
rectified crop or a smaller declared grid. Images above 40,000,000 decoded pixels are
rejected; resize them before analysis.

## Exit code 1 in automation

Exit `1` means the analysis completed and wrote findings. Read `report.json` or
`cells.csv`. Exit `2` means the analysis could not complete; stderr contains the stable
boundary error and no new report directory should remain.
