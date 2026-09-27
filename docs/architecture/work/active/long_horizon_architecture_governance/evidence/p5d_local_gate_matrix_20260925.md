# P5-D Local Gate Matrix Evidence

Status: `2026-09-27` — branch-side P5-D implementation matrix, superseded for
acceptance by the explicit owner decision in the [owner acceptance packet](p5d_owner_acceptance_and_rebuild_retirement_20260927.md).

## Completed local gates

The current branch has executable evidence for all implementation gates that
can be exercised in the supported Windows/MSVC CPU/in-process topology:

- bounded maintained-caller parity and native `src/main.cpp` facade routing;
- local signed RolloutDecision admission and durable ArtifactLedger lifecycle;
- release/plan/RunReceipt/evidence identity binding;
- process restart and same-release/package rollback with caller resynchronization;
- admission-bound facade VecEnv reset/step;
- three-cycle supported-row telemetry/SLO/adoption measurement;
- rollback prerequisite drills and long-lived local rollback-window recheck;
- zero maintained production rebuild callers and the fail-closed retirement gate;
- owner-authorized retirement of production rebuild authority with the test seam retained.

## Verification

The focused P5-D matrix was rerun after the caller-parity changes:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
powershell -NoProfile -ExecutionPolicy Bypass -File tools/maintenance/cmo_env.ps1 `
  python -m pytest -q `
  tests/architecture/runtime_host/test_p5d_maintained_caller_parity.py `
  tests/architecture/composition/test_runtime_composition_migration_closure.py `
  tests/architecture/runtime_host/test_p5d_facade_vecenv_canary.py `
  tests/architecture/runtime_host/test_p5d_real_process_package_rollback.py `
  tests/architecture/runtime_host/test_p5d_rebuild_retirement_gate.py `
  tests/architecture/runtime_host/test_p5d_rollout_operations.py `
  tests/architecture/runtime_host/test_p5d_supported_row_measurement.py `
  tests/architecture/runtime_host/test_sqlite_rollout_admission.py `
  tests/architecture/runtime_host/test_production_rollout_gate.py `
  tests/architecture/runtime_host/test_rollout_evidence_binding.py
```

Result: **55 passed**. The composition closure validator also passed directly,
and Ruff plus `git diff --check` passed for the changed implementation/tests.
The governance audit suite remains **79 passed**.

## Explicit residuals

The branch does not claim the following as live telemetry because they require
an authorized post-merge operational environment rather than repository-local
fixtures:

- the sole real production-canary RolloutDecision and caller-cutover
  attestation;
- representative release cadence and owner-approved long-term budget;
- a real production rollback-window observation; and
- live post-merge observation of those operational inputs.

The project owner nevertheless accepted P5-D for main-plan continuation and
authorized production-authority retirement; that decision is recorded in the
owner acceptance packet linked above.

Unsupported Linux/package, multi-process, external-host, and CUDA-canonical
rows continue to fail closed.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_local_gate_matrix_20260925.md`
Owner: `release/runtime integration`
Last verified: `2026-09-25`
