# Known Test Infrastructure Residuals

Language:
- English canonical: `known_test_infrastructure_residuals.md`
- Chinese companion: [known_test_infrastructure_residuals.zh.md](known_test_infrastructure_residuals.zh.md)

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/engineering/testing/reference/known_test_infrastructure_residuals.md`
Owner: `engineering/testing`
Last verified: `2026-08-08`
Content status: current owner-local index extracted from the completed T6
ledger; entries describe validation limitations, not product acceptance.

## Verification Boundary

This page retains only test-harness, dependency-snapshot, and contract-runner
limitations from the archived ledger. Product calibration belongs to
`systems/effects`; C++ dependency decisions belong to `architecture`.

## Current Residuals

- Five compatibility/runtime-spine collection checks can be conditionally
  skipped when a local build contains a dependency build directory without the
  corresponding source tree (the recorded example is `flecs`). A matching
  build snapshot with dependency sources is required before treating the skip
  as evidence.
- The platform-spawn contract has the same build-snapshot limitation for
  `spdlog`; the skip does not establish a product failure or a green contract.
- The CUDA import-order test is conditional when `build-gpu/` and its `ef_py`
  artifact are absent. CPU-only worktrees do not provide CUDA evidence.
- The diagnostics top-level-entrypoint governance check remains a strict
  xfail until the approved consolidation boundary is actually implemented.
- The leader-phase-manager scenario contract has a lineage mismatch between
  the harness fixture and the current arming gate; the JSON contract and
  runner require an owner decision before the red is reclassified.

## Safe Use

Conditional skips and strict xfails must remain visible in reports. They are
not interchangeable with passing validation and must not be removed merely to
improve a smoke count. A residual closes only when the named environment,
runner, or governance change is present and the focused check is rerun.

## Source And Retention

The detailed dated reproductions and already-fixed repairs remain in the
completed T6 ledger (`git show 77610218:docs/plan/archive/unified_architecture_program_completed_20260727/t6_residual_ledger.md`).
This page is the current route for test maintainers; it does not duplicate the
ledger's historical iteration narrative.
