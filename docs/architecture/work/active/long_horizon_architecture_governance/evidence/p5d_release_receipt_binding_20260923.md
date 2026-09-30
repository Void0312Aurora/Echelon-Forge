# P5-D Release and RunReceipt Binding Evidence

Status: 2026-09-23 — initial release-evidence binding slice; superseded for
the production-state commit boundary by [P5-D production binding and
operations evidence](p5d_production_binding_operations_20260923.md). This is
not a production cutover or P5-D acceptance.

The maintained runtime first gained an opt-in, package-compatible projection
that binds a local RolloutDecision to an actual release-manifest envelope and
a durably acknowledged RunReceipt. The projection checks canonical envelope
bytes, release identity and manifest digest, plan digest, rollout decision
identity and payload digest, receipt terminal/completion state, and package
and wheel digests. The release-controller production states and
`RuntimeFacadeAdapter(require_production_admission=True)` now require this
binding; development and shadow callers remain unchanged.

## Verification

Executed in the isolated codex/long-horizon-governance-architecture worktree:

    $env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 python -m pytest -q tests/architecture/runtime_host/test_rollout_evidence_binding.py tests/architecture/runtime_host/test_production_rollout_gate.py
    powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 python -m pytest -q tests/architecture/runtime_facade/test_runtime_escape_hatches.py tests/architecture/runtime_spine/test_web_viz_facade_caller.py
    python -m ruff check python/rl/runtime/rollout_evidence.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/vec_env.py tests/architecture/runtime_host/test_rollout_evidence_binding.py

Results:

- release/receipt and production admission gates: 10 passed;
- facade escape-hatch and web-viz caller gates: 29 passed;
- Ruff passed.

The binding test uses canonical release and receipt records, verifies exact
release/plan/decision/package identity, rejects a receipt decision drift, and
constructs an adapter with evidence binding required.

## Remaining boundary

This projection does not itself publish an ArtifactLedger record or perform a
package restart. The follow-up operations packet records the strict
pre-commit boundary and drill prerequisites. P5-D still requires the durable
ledger controller and actual supported-row same-release checkpoint and
stop/restart-package rollback drills, measured telemetry/SLO evidence, and
rebuild retirement before any production cutover.
