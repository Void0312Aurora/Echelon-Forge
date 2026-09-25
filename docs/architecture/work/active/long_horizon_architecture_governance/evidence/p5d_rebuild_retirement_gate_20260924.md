# P5-D Rebuild Retirement Gate Evidence

Status: `2026-09-25` — the post-rollback-window gate is implemented and
fail-closed, but it has not been activated for production authority.

## Gate boundary

`tools/maintenance/p5d_rebuild_retirement_gate.py` is deliberately separate
from the pre-cutover reachability inventory. It requires all of the following
before it emits a retirement proof:

- a durable rollout admission in `stable`, still open and unfrozen;
- a matching durable retention check whose release, slot version, and blob
  classes are intact;
- a fresh `runtime_rebuild_unreachability` inventory with zero maintained
  production callers and zero Python binding references; and
- an exact, identity-bound attestation for the production caller cutover,
  adoption evidence, and rollback-window evidence.

The gate is read-only. It does not publish a rollout slot, delete the native
method, or alter the pre-cutover inventory. Its proof scope is explicitly
`production_rebuild_authority_only`; the native test/fault-injection capability
remains retained.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q `
  tests/architecture/runtime_host/test_p5d_rebuild_retirement_gate.py `
  tests/architecture/runtime_host/test_runtime_rebuild_unreachability.py `
  tests/architecture/runtime_host/test_sqlite_rollout_admission.py
python -m ruff check `
  tools/maintenance/p5d_rebuild_retirement_gate.py `
  tests/architecture/runtime_host/test_p5d_rebuild_retirement_gate.py `
  tests/architecture/runtime_host/test_sqlite_rollout_admission.py
git diff --check
```

Results: **18 tests passed**, Ruff passed, and the diff check passed. The
positive gate test now consumes an actual durable SQLite `stable` admission
and retention projection, in addition to the contract-fixture checks. The
tests reject pre-stable admissions, missing or mismatched attestation,
unretained or misclassified attestation evidence, retention projection drift,
and inventory drift; the positive case only produces a
production-authority-only proof and retains the native test capability.

## Remaining boundary

No production cutover or retirement is claimed by this packet. The positive
case uses local contract fixtures to exercise the gate. A real release still
needs the authorized production-canary decision, representative release
cadence, actual rollback-window observation, and operator-supplied cutover
attestation before this gate can be run against production evidence.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_rebuild_retirement_gate_20260924.md`
Owner: `release/runtime integration`
Last verified: `2026-09-25`
