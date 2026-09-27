# P8-A Acceptance Baseline Evidence

Status: `2026-09-28` — bounded local acceptance completed for the executable
Windows CPU in-process lane; wider unsupported rows remain fail-closed and
non-blocking.

## Scope

`p8_acceptance_matrix_20260924.json` is the derived checklist for the six P8
requirements and five platform/process rows defined by the maintained
acceptance contract. The current acceptance boundary is the executable
Windows CPU in-process lane, local SQLite backup/restore, and short-cycle
repeatability. Linux/package qualification, multi-process, external-host, and
CUDA-canonical rows remain explicit fail-closed residuals.

The current decision is `accepted` for that bounded scope. External providers,
representative or long-running cadence, hosted CI/branch protection,
production rollback-window observation, and independent P8-B review are not
acceptance requirements. P5-D owner acceptance and production
rebuild-authority retirement are included as local evidence. Unsupported
multi-process, external-host, and CUDA-canonical rows remain explicitly
fail-closed.

## Verification

```powershell
python -m pytest -q `
  tests/architecture/governance/test_p8_acceptance_matrix.py `
  tests/runners/test_pytest_suite_manifests.py
```

Result: **17 passed** on Windows.

The matrix now binds each topology row to an executable admission gate, and
the unsupported rows are checked against the actual fail-closed implementation
rather than only carrying a documentation assertion.

```powershell
$paths=(Get-Content -Raw tests/suites/governance_audit_suite.json | ConvertFrom-Json).paths
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q $paths
```

Result: **79 passed**. This includes the P2-B sustainability baseline,
candidate teardown/state-transfer guards, archive/lifecycle checks, P6
authority checks, P7 retention checks, and the P8 matrix validator.

The candidate teardown/state-transfer subset independently passed **25 tests**.
The P2-B baseline observes all four check groups passing and reports `passed`
for the local sample; representative release cadence is observation-only and
is not an acceptance blocker.

The same P8 matrix and retention-authority tests were run in the HEI temporary
Linux clone `/tmp/echelon-forge-governance.iiLb6Y` with the available local
`ef_py` build artifact. After fetching full Git history for the retained
document probe, the result was **15 passed**. HEI had no maintained
Echelon-Forge checkout before this temporary clone, so this result is a
short-cycle Linux governance/import check, not a claim of Linux package
qualification.

## Boundary

This evidence does not establish Linux package qualification, multi-process,
external-host, CUDA-canonical execution, external provider operation, hosted
CI enforcement, or long-running production observation. Those rows are
outside the current acceptance and remain fail-closed where applicable.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p8_acceptance_baseline_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-27`
