# P5-D Local Rollout Admission Evidence

Status: `2026-09-22` — implementation slice, not P5-D acceptance.

This packet records the first executable P5-D boundary after P5-A/P5-B/P5-C:
the maintained Python runtime can now require a durable, signed local
`RolloutDecision` before constructing a production-mode facade adapter. The
default development/shadow path remains unchanged and no production caller has
been switched implicitly.

## Implemented boundary

- `python/rl/runtime/rollout_gate.py` owns a local in-process decision slot.
- The slot uses an exclusive lock, canonical JSON, HMAC-SHA256 operator
  attestation, atomic replacement, file flush, and directory flush where the
  platform exposes it.
- The slot enforces the accepted monotonic state graph, adjacent writer
  generations, immutable release-manifest binding, compare-and-swap predecessor
  identity, kill-switch closure, and typed backout at the `none` irreversible
  write boundary only.
- `RuntimeFacadeAdapter` and `WorldBatchVecEnv` accept an explicit rollout slot
  and verification key. `require_production_admission=True` fails closed when
  the slot is absent, unauthenticated, closed, or not in a production state.
- `tools/maintenance/commit_runtime_rollout_decision.py` is the explicit local
  release-controller entry point. It does not select remote or multi-process
  execution and does not alter the default runtime mode.

## Verification

Executed in the isolated `codex/long-horizon-governance-architecture`
worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
python -m pytest -q tests/architecture/runtime_host/test_production_rollout_gate.py
python -m ruff check python/rl/runtime/rollout_gate.py `
  python/rl/runtime/world_batch/adapter.py `
  python/rl/runtime/world_batch/vec_env.py `
  tools/maintenance/commit_runtime_rollout_decision.py `
  tests/architecture/runtime_host/test_production_rollout_gate.py
```

Result: **6 passed** and Ruff passed.

The test row covers durable restart, monotonic `prepared → shadow →
canary-ready → production-canary`, stale-writer/CAS rejection, kill-switch
closure, typed backout, tamper and wrong-key rejection, the explicit
maintained-adapter gate, and the release-controller CLI.

The real local CPU-canonical VecEnv was then started with a temporary signed
`production-canary` slot, `require_production_admission=True`, and the exact
facade-only build. It completed reset and one step with visual tensors shaped
`(1, 24, 48, 10)` on both paths; the returned step tuple length was `4`.

## Scope and remaining P5-D work

This is not a production cutover. The slot currently proves the local
single-process admission boundary only. P5-D still must bind the slot to the
actual release manifest/package and RunReceipt/ArtifactLedger records, migrate
the inventoried maintained callers, rehearse same-release checkpoint recovery
and stop/restart package rollback, collect support-row telemetry/SLO evidence,
and retire the in-kernel production rebuild authority after the rollback
window. Remote/multi-process and unsupported platform rows remain fail-closed.
