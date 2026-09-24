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
architecture guard manifest; no test was dropped. Native CTest entries now
carry primary lane labels in `CMakeLists.txt`, and a configured CTest
inventory check verifies the labels rather than repeating a name regex.

## Derived inventory

The checked-out tree currently derives:

| Measure | Result |
| --- | ---: |
| Architecture test files | 113 |
| Manifest entries | 113 |
| Tier manifests | 2 |
| Runner manifests with owner/lane metadata | 4 |
| Owners / execution strategies | 2 / 2 |
| Files with source-scan references | 111 |
| Files retaining the `source_scan_guard` residual flag | 87 |
| Files selected by the pytest smoke manifest | 34 |
| Native CTest entries with a primary lane label | 25 |

The source-scan counts are diagnostics, not an acceptance claim. One
replacement slice is now complete: `test_stage_node_manifest_registry.py`
removed its header-text field scan and moved the maintained-node field
completeness assertion into a compiled native registry probe. The existing
validator and fail-closed negative tests remain in place. This reduces the
residual count from 88 to 87; it does not justify retiring the other source
scans, because source-text boundary checks are not physically equivalent to
target, package, type, or behavior boundaries by themselves.

## Verification

Executed in the isolated worktree:

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
$env:PYTHONPATH="$PWD\build-long-horizon-p5c-shared\Debug;$PWD"
python -m pytest -q `
  tests/architecture/causal_runtime/test_stage_node_manifest_registry.py `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/runners/test_pytest_suite_manifests.py `
  tests/architecture/governance/test_control_lifecycle_metadata.py
```

Result: **23 passed**. The test set includes the native registry replacement,
real collection/marker
lockstep check, tier partition/orphan detection, root metadata validation,
derived inventory assignment, and cross-tier overlap rejection.

```powershell
$env:CMO_BUILD_DIR='build-long-horizon-p5c-shared'
python -m pytest -q tests/architecture/build_system/test_ctest_lane_labels.py
```

Result: **2 passed**. The configured Release CTest inventory reports 25 native
entries; every entry has at least one primary lane label and the declared
`fast`, `qualification`, `nightly`, `release`, and `research` audiences are
all represented.

```powershell
python tools/runners/audit_test_authority.py --format markdown --limit 10
python -m ruff check `
  tools/runners/audit_test_authority.py `
  tests/architecture/governance/test_test_authority_audit.py `
  tests/runners/test_pytest_suite_manifests.py
git diff --check
```

The audit command, Ruff, and diff check passed. This is an implementation
baseline with one replacement slice; the remaining P6-A replacement/retirement
decisions and P6-B workflow parallelism, repeated CI evidence, and
failure-routing work remain open.

Document kind: `evidence`
Lifecycle: `maintained`
Canonical: `docs/architecture/work/active/long_horizon_architecture_governance/evidence/p6a_test_authority_audit_20260924.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-24`
