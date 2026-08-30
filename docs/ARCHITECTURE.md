# Architecture

PatternProof has one authoritative path from external evidence to report artifacts:

```text
pattern JSON ─> strict loader ─┐
                              ├─> per-cell sampling ─> CIELAB classification ─> result
capture image ─> bounded load ┘                                      │
                                                                      └─> atomic reports
```

## Module ownership

- `loader.py` owns the version-one pattern boundary and rejects unknown, missing, or
  out-of-range input before a domain object exists.
- `model.py` owns immutable pattern and result data. A `Pattern` and `AnalysisResult`
  are the only domain truth used downstream.
- `color.py` owns sRGB-to-CIELAB D65 conversion and CIE76 distance.
- `analysis.py` divides the already rectified capture into declared cells, takes the
  central median, and assigns exactly one status.
- `reporting.py` renders the one analysis result into four agreeing artifacts. It
  writes a temporary sibling directory and renames only after every artifact succeeds.
- `cli.py` owns process exit codes and stable user-facing boundary errors.

There is no second classifier in the overlay, HTML, or CLI. Reports display the result;
they do not reinterpret it.

## Classification policy

For one observed cell, candidates are `empty_color` plus every declared palette color.
The nearest CIE76 candidate is deterministic; palette keys break exact-distance ties in
sorted order. A candidate farther than the configured threshold produces `uncertain`.
Otherwise the candidate and the expected cell determine `match`, `background`, `empty`,
or `wrong`.

The inset excludes cell borders before the channel median is measured. It is a visible
policy value in the report, not hidden image correction.

## Failure model

Validation happens at the two external boundaries: pattern/image input and report
output. Grid size, palette size, decoded image pixels, option ranges, and output
replacement are bounded. Internal domain objects are trusted after construction.

An invalid input exits before report creation. A write failure removes its temporary
directory. An output path that already exists is never replaced. Unexpected programmer
errors are not swallowed.

## Determinism and privacy

The program performs no network requests and stores no global state. For identical
decoded pixels, pattern JSON, and options, cell classifications and structured report
values are deterministic. PNG container bytes may depend on the installed Pillow
version, so release checks compare behavior and contents rather than claiming universal
binary identity.
