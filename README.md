# PatternProof

Compare a physical square-grid craft with its intended color-cell pattern, entirely
offline.

PatternProof reads a versioned JSON grid and a rectified, tightly cropped photograph or
scan. It samples every cell, compares the observed color with the declared palette in
CIELAB space, and classifies the cell as matching, empty, wrong, background, or
uncertain. Reports retain the evidence instead of hiding ambiguous captures.

> PatternProof is under active v0.1 development. The supported command, examples, and
> release acceptance instructions will be added as their tested implementation lands.

The product contract is in [SPEC.md](SPEC.md), and the selection evidence is in
[docs/RESEARCH.md](docs/RESEARCH.md).

## License

MIT © 2026 KanadeK
