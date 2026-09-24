# P8-A Acceptance Baseline Evidence

Status: `2026-09-24` — acceptance matrix and local governance baseline; P8 is
not accepted.

## Scope

`p8_acceptance_matrix_20260924.json` is the derived checklist for the six P8
requirements and five platform/process rows defined by the maintained
acceptance contract. It deliberately records partial/open residuals rather
than turning existing local evidence into a closure claim.

The current decision is `not_eligible` because production cutover,
representative release cadence, production rollback-window operation,
provider restore drills, and independent P8-B review remain open. Unsupported
multi-process, external-host, and CUDA-canonical rows are explicitly
fail-closed.

## Verification

```powershell
python -m pytest -q `
  tests/architecture/governance/test_p8_acceptance_matrix.py `
  tests/runners/test_pytest_suite_manifests.py
```

Result: **17 passed**.

The matrix now binds each topology row to an executable admission gate, and
the unsupported rows are checked against the actual fail-closed implementation
rather than only carrying a documentation assertion.

```powershell
$paths=(Get-Content -Raw tests/suites/governance_audit_suite.json | ConvertFrom-Json).paths
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q $paths
```

Result: **76 passed**. This includes the P2-B sustainability baseline,
candidate teardown/state-transfer guards, archive/lifecycle checks, P6
authority checks, P7 retention checks, and the P8 matrix validator.

The candidate teardown/state-transfer subset independently passed **25 tests**.
The P2-B baseline now observes all four check groups passing and reports
`passed` for the local sample; representative release cadence remains open by
the matrix and is not inferred from this one local run.

## Boundary

This evidence does not establish:

- production truth publication or maintained caller cutover;
- Linux/package qualification beyond the recorded partial row;
- production rollback-window operation or rebuild retirement;
- an admitted external evidence provider or production rollback-window restore
  drill; the bounded local SQLite restore drill is recorded separately; or
- independent P8-B review.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p8_acceptance_baseline_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-24`
