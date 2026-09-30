# P7-B Zero-Inventory Retirement Evidence

Status: `2026-09-24` — first P7-B cleanup slice; remaining residual cleanup
and provider/restore drills remain open.

## Retired slice

The UniversalEnv compatibility migration had already reached a measured zero:
no maintained Python caller set `runtime_compatibility_enabled=True`, and the
maintained examples used `WorldBatchVecEnv`/facade paths. The zero-entry
inventory had become a ratchet without remaining coverage value. P7-B removed:

- `tests/architecture/fixtures/universal_env_runtime_compatibility_callers_20260612.json`;
- `tests/architecture/runtime_facade/test_universal_env_compatibility_caller_inventory.py`;
- its `universal_env_compatibility_inventory` lifecycle-control entry and
  architecture-suite membership.

The dated survival table under `docs/architecture/reviews/` remains as
historical provenance. New violations remain covered by the maintained
facade/VecEnv boundary gates:

- `tests/architecture/runtime_facade/test_runtime_escape_hatches.py`;
- `tests/architecture/runtime_facade/test_scenario_setup_facade_boundary.py`.

This is a contained retirement, not permission to remove the facade boundary
or to reintroduce raw `UniversalEnv` compatibility behavior.

## Verification

The successor facade/VecEnv checks passed **39 tests**. The lifecycle,
manifest, and derived-authority checks passed **15 tests** after the manifest
edit. The derived authority report now records:

| Measure | Result |
| --- | ---: |
| Architecture test files | 113 |
| Architecture manifest entries | 113 |
| Files with source-scan references | 111 |
| Files retaining a source-scan residual flag | 86 |

The following checks were also run:

```powershell
python tools/runners/audit_test_authority.py --format markdown --limit 5
python -m pytest -q `
  tests/architecture/governance/test_control_lifecycle_metadata.py `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/runners/test_pytest_suite_manifests.py
git diff --check
```

The targeted commands completed successfully. The complete governance audit
then produced **67 passed and 1 failed**; the sole failure is the pre-existing
P2-B sustainability baseline reporting `needs-disposition`, not a P7-B
retirement or document-lifecycle failure. No source-scan residual was silently
retired by this slice; only the completed zero-entry ratchet was removed.

## Boundary

P7-B is not complete. Remaining work includes classifying and retiring other
superseded migration controls or duplicate documents only where a replacement
gate and retrieval route exist, and completing the retention-authority
provider/restore-drill obligations. P8 acceptance is not implied.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p7b_zero_inventory_retirement_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-24`
