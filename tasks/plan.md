# PatternProof implementation plan

1. Freeze the schema, status model, thresholds, exit codes, and non-goals.
2. Build the strict pattern loader and color math with failing tests first.
3. Add bounded image sampling and classification with clean/defect fixtures.
4. Add transactional reporting and CLI exit behavior.
5. Generate reproducible examples and user-facing acceptance/repair documentation.
6. Add locked tooling, cross-platform CI, packaging, and release automation.
7. Run the full local gate, review the complete diff, and commit atomic slices.
8. Publish, wait for CI, tag/release, verify public assets in a fresh install, then email.

Risks are controlled at the boundary: v0.1 requires a rectified crop, uses no automatic
perspective correction, and emits `uncertain` rather than hiding lighting ambiguity.
