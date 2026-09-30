# P5-D Production Binding And Operations Evidence

Status: `2026-09-23` — executable prerequisite slice; not a production
cutover or P5-D acceptance.

This packet closes one admission gap and adds the first runnable operations
contract for the supported local in-process row. A rollout decision in a
production state can no longer be committed through the maintained release
controller without a canonical release-manifest envelope and a durably
acknowledged RunReceipt that name the same release, plan, decision, package,
and wheel. A maintained adapter that requests production admission applies the
same binding before construction and on every admission refresh.

## Implemented boundary

- `tools/maintenance/commit_runtime_rollout_decision.py` pre-validates release
  and receipt evidence before writing `production-canary`,
  `adoption-expanding`, `rollback-window`, or `stable` decisions. Missing or
  mismatched evidence leaves the slot unwritten.
- `python/rl/runtime/rollout_evidence.py` exposes a pre-commit projection check
  in addition to the persisted-slot check, so the release controller does not
  publish first and discover a mismatch afterward.
- `RuntimeFacadeAdapter(require_production_admission=True)` now implies the
  release/RunReceipt binding requirement. Development and shadow construction
  remains unchanged.
- `tools/maintenance/p5d_rollout_operations.py` provides a secret-free,
  release/plan/epoch-tagged telemetry projection, initial P1-C SLO evaluation,
  and explicit prerequisite checks for both backout protocols:
  same-release checkpoint recovery and stop/restart N-1 package rollback. It
  is an evidence/runbook helper, not a runtime publication authority.

## Verification

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 `
  python -m pytest -q `
  tests/architecture/runtime_host/test_rollout_evidence_binding.py `
  tests/architecture/runtime_host/test_production_rollout_gate.py `
  tests/architecture/runtime_host/test_p5d_rollout_operations.py
python -m ruff check `
  python/rl/runtime/rollout_evidence.py `
  python/rl/runtime/world_batch/adapter.py `
  tools/maintenance/commit_runtime_rollout_decision.py `
  tools/maintenance/p5d_rollout_operations.py `
  tests/architecture/runtime_host/test_rollout_evidence_binding.py `
  tests/architecture/runtime_host/test_production_rollout_gate.py `
  tests/architecture/runtime_host/test_p5d_rollout_operations.py
```

Result: **17 passed** and Ruff passed. The tests cover pre-commit identity
checking, production-state rejection without evidence, strict adapter
construction/refresh, kill-switch resynchronization, telemetry/SLO failure
closure, same-release recovery prerequisites, package restart with and
without a checkpoint, and irreversible-boundary fail-stop.

## Remaining boundary

The production-state binding is now mandatory at the local release-controller
and maintained-adapter boundaries, but the local file slot is still not the
qualified ArtifactLedger controller. The rollback functions validate operator
prerequisites; they do not install a wheel, stop a real process, or publish a
native host replacement. P5-D still requires an ArtifactLedger-backed
production canary, real supported-row instance/package drills, measured
multi-run telemetry/SLO evidence, caller adoption, and rebuild retirement
after the rollback window. Unsupported remote/multi-process rows remain
fail-closed.
