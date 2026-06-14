# Test Suites

`tests/suites/` previously stored advisory suite/matrix metadata. The draft
`test_system_matrix.json`, `contract_system_matrix.json`, and
`focused_runtime_suite.json` files have been removed: they were not wired into
any runner or CI step, and the meta-tests policing their cross-file consistency
were enforcing documentation rather than behavior.

## Current CI Wiring

CI runs three test surfaces, all gated through `tools/runners/`:

- `tests/smoke/ci_smoke_suite.json` — the maintained pytest smoke gate.
- `tests/smoke/ci_contract_suite.json` — the maintained JSON contract smoke gate.
- The C++ `ctest ef_test_all` smoke target.

These live under `tests/smoke/`, not `tests/suites/`.

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

These tiers are advisory labels for discussing suite intent; no runner currently
selects a tier automatically. Promotion into CI happens by editing
`tests/smoke/ci_smoke_suite.json` or `tests/smoke/ci_contract_suite.json`
directly.

Pytest suite manifests may list directories, files, or pytest node IDs. The CI
smoke suite is intentionally explicit (files and node IDs only, no directory
entries) so new tests are promoted deliberately rather than auto-discovered.

Fast meta-tests under `tests/runners/test_pytest_suite_manifests.py` validate
that smoke path entries remain resolvable and that the runtime-facade layering
guard keeps node IDs rather than broad directory entries.

Architecture guard promotion should add files or node IDs to
`tests/smoke/ci_smoke_suite.json` directly. Broad source scans,
release-package generation, retained-artifact verification, and source-admission
workflows are local/manual by default until a cheap smoke-safe subset is split
out and listed explicitly.
