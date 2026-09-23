# P5-D Real Facade VecEnv Canary Evidence

Status: `2026-09-23` — one locally admitted facade VecEnv reset/step cycle
passed with the release, plan, package, wheel, and RunReceipt bindings. This
is a canary-path verification, not final production publication or P5-D
acceptance.

## Exercised path

The focused tests create the existing signed `production-canary` rollout slot,
release manifest, and RunReceipt fixture, then construct the real
`WorldBatchVecEnv` with `require_production_admission=True`. One case reads the
file-backed local slot; the second reads the durable `SQLiteArtifactLedger`
snapshot. In both cases the adapter must validate the signed slot and evidence
binding before constructing the native `RuntimeFacade`. Each case then
executes one real `reset()` and one real `step()` on the inline supported-row
scenario, and confirms the admission remains production-authorized after the
mutation path.

The file-backed case isolates the VecEnv path, while the SQLite case verifies
the same path through the durable snapshot reader. The real child-process
binding and rollback chain are covered separately by [the process/package
rollback packet](p5d_real_process_package_rollback_20260923.md); this packet
does not replace that process evidence.

## Verification

Executed in the isolated
`codex/long-horizon-governance-architecture` worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5d-wheel'
python -m pytest -q --confcutdir tests/architecture `
  tests/architecture/runtime_host/test_p5d_facade_vecenv_canary.py
python -m ruff check `
  tests/architecture/runtime_host/test_p5d_facade_vecenv_canary.py
git diff --check
```

Result: **2 tests passed** in 15.72 seconds; Ruff and the diff check passed.

## Boundary

The result proves the real facade VecEnv can execute an admission-bound reset
and step on the tested local Windows CPU-canonical build. It does not publish
a durable production decision, prove representative cadence or full caller
parity, or retire the in-kernel rebuild. Those remain P5-D/P2-B gates.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p5d_facade_vecenv_canary_20260923.md`
Owner: `release/runtime integration`
Last verified: `2026-09-23`
