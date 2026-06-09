# Test Suites

`tests/suites/` stores advisory suite metadata that can be reviewed and evolved without changing CI wiring.

## Files

- `test_system_matrix.json`
  - Machine-readable draft matrix for mapping test surfaces to governance tiers.
  - Tracks pytest paths and JSON contract paths together so ownership and promotion discussions have one index.
  - Records architecture guard tiering before paths are promoted into concrete suite manifests.
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

Pytest suite manifests may list directories, files, or pytest node IDs. Node IDs
are preferred when a large guard file contains a small smoke-safe subset and a
broader focused/local subset.

Any matrix row that lists `tests/smoke/ci_smoke_suite.json` in
`suite_membership` must also enumerate its concrete `smoke_paths`.

Fast meta-tests under `tests/runners/` validate that suite and matrix path
entries remain resolvable and that manual-tier architecture roots do not leak
back into CI smoke.

Architecture guard promotion should follow the matrix first. Broad source scans,
release-package generation, retained-artifact verification, and source-admission
workflows are local/manual by default until a cheap smoke-safe subset is split
out and listed explicitly.
