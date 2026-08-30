# Contributing

Thank you for improving PatternProof. Open an issue before changing a public schema,
classification rule, or runtime dependency so the compatibility and evidence impact is
explicit.

## Local workflow

1. Install `uv` and use Python 3.11 or newer.
2. Run `uv sync --locked --all-groups`.
3. Add a failing test that describes the intended behavior.
4. Make the smallest complete change in the authoritative module.
5. Run `uv run python scripts/check.py`.

Do not add automatic correction, fallbacks, or a second classification path to hide an
input-contract problem. New reports must remain inspectable and agree with the single
`AnalysisResult`.

Bug reports should include the command, exit code, pattern JSON, capture dimensions,
and relevant report cells. Remove private imagery or palette names before posting a
public issue.
