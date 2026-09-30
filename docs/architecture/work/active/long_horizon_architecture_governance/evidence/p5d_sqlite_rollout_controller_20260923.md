# P5-D SQLite Rollout Controller Evidence

Status: `2026-09-23` — durable local-controller implementation slice; not a
production cutover or P5-D acceptance.

This packet records the first ArtifactLedger-backed RolloutDecision path on the
already qualified local SQLite backend. It closes the gap between the signed
file-slot admission and the durable ledger that P5-D must use before any
truth-changing production decision. The supported boundary remains the local,
single-process, in-process CPU-canonical row.

## Implemented boundary

- `SQLiteArtifactLedger.commit_rollout_admission` validates the signed
  `RolloutDecision`, release-manifest authority, complete RunReceipt, and the
  release/plan/decision/package/wheel evidence projection before opening a
  durable transaction.
- Release, decision, receipt, and evidence blobs are content-addressed and
  committed atomically with the decision and evidence CAS slots. A missing
  predecessor, stale fence, invalid transition, changed release envelope, or
  mismatched evidence aborts the whole transaction.
- `read_rollout_admission` revalidates the stored authority graph and every
  evidence identity on restart. `trip_rollout_kill_switch` closes admission by
  a separate evidence-slot CAS without rewriting the signed decision.
- `read_rollout_snapshot` projects the durable record into the existing
  `RolloutAdmission` slot shape. `RuntimeFacadeAdapter` and
  `WorldBatchVecEnv` can consume that snapshot through an explicit reader and
  re-read it before the next production mutation.
- The adapter path does not make SQLite a second publication authority: the
  ledger reader supplies the already committed decision, while the runtime
  still owns host publication and execution truth.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q tests/architecture/runtime_host/test_sqlite_rollout_admission.py
python -m pytest -q tests/architecture/runtime_host/test_production_rollout_gate.py tests/architecture/runtime_host/test_rollout_evidence_binding.py
python -m pytest -q tests/architecture/composition/test_runtime_run_receipt.py tests/architecture/composition/test_runtime_artifact_ledger.py
python -m ruff check python/rl/runtime/rollout_evidence.py python/rl/runtime/rollout_gate.py python/rl/runtime/world_batch/adapter.py python/rl/runtime/world_batch/vec_env.py tools/maintenance/runtime_durable_artifact_ledger.py tests/architecture/runtime_host/test_sqlite_rollout_admission.py
git diff --check
```

Results:

- SQLite controller, restart, CAS, evidence-drift, immutable-release,
  kill-switch/backout, and facade snapshot tests: **5 passed**;
- production admission and release/receipt binding regression tests:
  **12 passed**;
- existing durable RunReceipt/ArtifactLedger qualification regression tests:
  **41 passed**;
- Ruff and the diff whitespace check passed.

## Remaining boundary

This is a durable local controller and reader integration, not authorization
to publish production truth. No remote or multi-process topology is admitted;
the release-controller API still requires the caller to provide the signed
authorities and verification key. Real installed-wheel stop/restart and
same-release instance rollback drills, measured multi-run SLO/adoption data,
rebuild retirement, and the sole production-canary cutover remain open P5-D
work. A focused test green result does not substitute for those operational
gates.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_sqlite_rollout_controller_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
