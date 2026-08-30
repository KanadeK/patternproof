# Research and differentiation

Research date: 2026-08-30.

## Observed workflow gap

Existing craft tools mostly turn artwork into a grid pattern. PatternProof starts after
that step: the maker already has the intended grid and needs to compare it with a
physical work-in-progress or finished piece.

Recent diamond-painting discussions show repeated practical failures: makers discover
missing colors, run short after placing a color under the wrong symbol, or receive a
different color than the chart specifies. These reports establish a real checking
problem; they do not establish that a photograph can always resolve it automatically.

## Representative public projects

- [Perler Studio](https://github.com/real-jiakai/perler-studio) converts images into
  fuse-bead patterns, maps to commercial palettes, and produces shopping lists.
- [Perler Beads Generator](https://github.com/Jett-Wu/Perler_Beads_Generator) is a rich
  pattern editor with layers, palette tools, usage counts, and exports.
- [3x3 Proxy Maker](https://github.com/dogbiscuits23/3x3-Proxy-Maker) and
  [PnPInk](https://github.com/xoellijo/pnpink) demonstrate that print layout generation
  is already well served and is not this project's problem.
- Community examples include reports of [using the wrong symbol and then running out of
  drills](https://www.reddit.com/r/diamondpainting/comments/1s74omy/ran_out_of_diamonds_half_way_through/)
  and [kits containing a wrong color](https://www.reddit.com/r/diamondpainting/comments/1jt9zsc/kit_sends_wrong_drills/).

Multiple GitHub and web queries for diamond-painting, fuse-bead, physical pixel-art,
and mosaic *verification from a capture* did not find a representative repository with
PatternProof's same input-to-output contract. Search absence is not proof of global
novelty, so the claim is deliberately narrower: no highly similar project was found in
the reviewed results on the research date.

## Local and prior-work distinction

The local workspace already contains pattern generators, stock matchers, image
measurement tools, and many offline auditors. PatternProof does not regenerate artwork,
plan inventory, or segment unknown objects:

- `crumbscope` segments and measures unknown pores in bread images; PatternProof samples
  known grid cells and compares each against an explicit expected color.
- `pixelpeel` compares digital UI screenshots; PatternProof uses a semantic craft grid,
  an empty-cell reference, and physical-capture uncertainty.
- `skeinplan`, `keysetfit`, and `recall-match` solve inventory/requirement matching;
  PatternProof inspects observed placement after materials have been used.
- `floatlint` and `chartplain` analyze knitting charts; PatternProof is craft-agnostic and
  verifies a capture against an already approved chart.

## v0.1 product decision

Ship a CLI and inspectable evidence artifacts before considering a browser editor. The
hard value is the owned classification pipeline and failure model. Automatic crop,
perspective correction, OCR, brand palettes, mobile capture, and cloud storage are
explicitly excluded because they would add new ambiguity or duplicate mature tools.
