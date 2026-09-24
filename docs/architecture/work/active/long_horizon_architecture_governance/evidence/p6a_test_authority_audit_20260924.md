# P6-A Test Authority Audit Evidence

Status: `2026-09-24` — P6-A implementation baseline; the control-migration
cluster remains open.

## Scope

The architecture guard and governance-audit manifests remain the single source
of truth for the maintained `tests/architecture/test_*.py` tier assignment:

- `tests/suites/architecture_guard_suite.json`;
- `tests/suites/governance_audit_suite.json`.

Each tier manifest now declares its owner, failure audience, and execution
strategy at the root. `tools/runners/audit_test_authority.py` derives a
non-authoritative report from those manifests and the live architecture test
tree. It rejects stale entries, missing files, duplicate assignment, malformed
metadata, and cross-tier overlap. It also joins the existing static audit's
source-scan signal so residual migration guards remain visible rather than
being silently treated as retired.

The two CI runner manifests (`tests/smoke/ci_smoke_suite.json` and
`tests/smoke/ci_contract_suite.json`) now carry the same root owner,
failure-audience, and execution-strategy metadata. The report lists all four
runner manifests while keeping architecture-tier file assignment as its
validated orphan/overlap scope.

The report is intentionally not a second registry. It does not rewrite suite
membership, change pytest marker semantics, alter CTest definitions, or touch
the P7-A archive-retention policy, gate, or suite node. The newly discovered
`test_p5d_rebuild_retirement_gate.py` orphan was assigned to the existing
architecture guard manifest; no test was dropped.

## Derived inventory

The checked-out tree currently derives:

| Measure | Result |
| --- | ---: |
| Architecture test files | 112 |
| Manifest entries | 112 |
| Tier manifests | 2 |
| Runner manifests with owner/lane metadata | 4 |
| Owners / execution strategies | 2 / 2 |
| Files with source-scan references | 110 |
| Files retaining the `source_scan_guard` residual flag | 88 |
| Files selected by the pytest smoke manifest | 34 |

The source-scan counts are diagnostics, not an acceptance claim. P6-A still
needs replacement evidence before any individual migration guard can be
retired; source-text boundary checks are not physically equivalent to target,
package, type, or behavior boundaries by themselves.

## Verification

Executed in the isolated worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/runners/test_pytest_suite_manifests.py `
  tests/architecture/governance/test_control_lifecycle_metadata.py
```

Result: **15 passed**. The test set includes the real collection/marker
lockstep check, tier partition/orphan detection, root metadata validation,
derived inventory assignment, and cross-tier overlap rejection.

```powershell
python tools/runners/audit_test_authority.py --format markdown --limit 10
python -m ruff check `
  tools/runners/audit_test_authority.py `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/runners/test_pytest_suite_manifests.py
git diff --check
```

The audit command, Ruff, and diff check passed. This is an implementation
baseline only: P6-A replacement/retirement decisions and P6-B CI lane work
remain open.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p6a_test_authority_audit_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-24`
