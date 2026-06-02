# Test Suites

`tests/suites/` stores advisory suite metadata that can be reviewed and evolved without changing CI wiring.

## Files

- `test_system_matrix.json`
  - Machine-readable draft matrix for mapping test surfaces to governance tiers.
  - Tracks pytest paths and JSON contract paths together so ownership and promotion discussions have one index.
- `focused_runtime_suite.json`
  - Draft focused/local pytest manifest for representative runtime coverage.
  - Compatible with `tools/runners/run_pytest_suite.py`, but not referenced by CI.

## Tiers

- `smoke`
  - Fast, high-signal checks allowed to gate CI.
- `focused`
  - Small domain-oriented suites for local pre-merge checks and targeted ownership review.
- `local`
  - Developer-run suites that may be broader or more environment-sensitive than focused suites.
- `manual`
  - Human-invoked checks, diagnostics, or workflows that need judgment or special setup.
- `nightly`
  - Candidate long-running or broad regression coverage for scheduled automation after stabilization.

CI now runs the maintained pytest smoke suite in `tests/smoke/ci_smoke_suite.json`,
the C++ CTest smoke target, and the maintained JSON contract smoke suite in
`tests/smoke/ci_contract_suite.json`. The suite and matrix files here remain
governance metadata until a separate CI change explicitly promotes them.
