# PatternProof tasks

- [x] Task: Research local/history overlap and representative public competitors
  - Acceptance: Selected concept has a documented, evidence-backed distinction.
  - Verify: `docs/RESEARCH.md` names local and public comparators and limitations.
  - Files: `docs/RESEARCH.md`
- [x] Task: Implement strict pattern loading and color classification
  - Acceptance: Clean, wrong, empty, uncertain, and invalid cases have tests.
  - Verify: focused pytest files pass after their initial RED runs.
  - Files: `src/patternproof/model.py`, `loader.py`, `color.py`, `analysis.py`, tests
- [x] Task: Implement artifact generation and CLI
  - Acceptance: four outputs agree and exit codes are stable.
  - Verify: integration and CLI tests pass.
  - Files: `reporting.py`, `cli.py`, tests
- [x] Task: Complete examples, documentation, CI, and packaging
  - Acceptance: release-equivalent gate passes at >=90% branch coverage.
  - Verify: `uv run python scripts/check.py`.
  - Files: examples, docs, workflows, `pyproject.toml`, `uv.lock`, scripts
- [ ] Task: Publish and independently verify v0.1.0
  - Acceptance: public CI, immutable tag, Release assets, fresh install, contributor
    hygiene, and Gmail self-notification are all evidenced.
  - Verify: public API/CLI checks plus Gmail send result.
  - Files: remote repository and release state; no additional product source expected
