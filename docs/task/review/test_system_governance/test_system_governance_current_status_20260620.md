# Test System Governance Current Status 2026-06-20

Status: `2026-06-21` accepted with tracked residuals; audit infrastructure,
P1-B evidence reconciliation, P2 structural splits, P2-C collection
documentation, and P3 suite-tier validation are accepted for the current
governance slice. Broad test-system health remains not accepted; residual
blockers are tracked in
[Test System Residual Governance](../../issues/test_system_residual_governance/README.md).

## What Changed

- Created the `test_system_governance` task subproject under
  `docs/task/review/`.
- Added a repeatable audit runner that excludes `archive` / `Archive` paths and
  reports pytest, JSON contract, smoke membership, and risk flags.
- Added runner tests and documented the audit entry in `tests/README.md`.
- Split the two largest `tests/tools` airframe geometry snapshot-style tests
  into report/artifact-scoped tests over module-level fixtures.
- Split the first ten high-risk `tests/architecture/damage_model` P2-B files
  into smaller semantic tests while retaining the existing fail-closed checks.
- Added [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)
  to separate static audit, pytest collection, and coverage semantics.
- Confirmed that the current work is governance/test-system scope only; no
  runtime or model behavior has been accepted through this slice.

## Maturity Matrix

| Surface | State | Evidence | Boundary |
| --- | --- | --- | --- |
| Branch and task surface | accepted current slice | `codex/test-system-governance`; this subproject. | Branch existence does not imply whole-project test health. |
| Audit runner | pass for initial slice | `tools/runners/audit_test_system.py`; `tests/runners/test_audit_test_system.py`. | Static analysis only; pytest collection remains separate evidence. |
| Runner validation | pass | `cmo_python -m pytest -q tests/runners` reported 27 passed. | Does not run full active test tree. |
| Risk inventory | active | Audit markdown reported 151 risk-flagged Python files, 16 hidden mixin test files, and 5 mixin wrapper files. | Risk flags are triage signals, not deletion instructions. |
| Coverage interpretation | pass for P1-B | Current local `.coverage` records 34376 statements, 11916 missed, 65% covered. | Does not prove C++ or whole-project coverage. |
| Test simplification | accepted with tracked residuals | `tests/tools` airframe tests and ten `tests/architecture/damage_model` files were split into smaller semantic checks. | Airframe dependency-complete behavior and damage-model literal/source-scan concentration are retained in the residual issue. |

## Closeout Audit Snapshot

Latest audit command:

```bash
source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 20
```

Closeout headline values:

| Metric | Value |
| --- | ---: |
| Active test files | 341 |
| Active Python files | 255 |
| `test_*.py` files | 211 |
| Static test items | 3145 |
| Pytest smoke entries | 51 |
| Pytest smoke files | 49 |
| Contract JSON files | 59 |
| Contract smoke specs | 10 |
| Risk-flagged Python files | 151 |
| Hidden mixin test files | 16 |
| Mixin wrapper files | 5 |

Note: `static test items` is an AST-level definition count and can differ from
`pytest --collect-only` because mixins and inherited unittest methods change
collection semantics. Use pytest collection for execution counts.

## P1-B Evidence Reconciliation

Evidence note:

- [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)

Measured values:

| Evidence source | Value | Boundary |
| --- | ---: | --- |
| Static active tracked audit | 341 active tracked test files; 3145 AST test items | Excludes archive paths and untracked files. |
| Pytest working-tree collection | 2000 tests collected | Includes current working-tree tests; no execution. |
| Local Python `.coverage` | 34376 statements, 11916 missed, 65% covered | Python only; no branch arcs or C++ coverage acceptance. |
| C++ coverage | not measured | Requires coverage build objects and `gcovr`. |

Collection emitted an Eventlet deprecation warning and a nanobind leak
diagnostic for `ef_py.Side`; both are retained as collection-time side-effect
signals, not as coverage conclusions.

## Current P2-A Slice

First simplified files:

- `tests/tools/test_airframe_geometry_manifest.py`
- `tests/tools/test_airframe_geometry_review_cli.py`

Before/after structural audit:

| File | Metric | Before | After |
| --- | --- | ---: | ---: |
| `test_airframe_geometry_manifest.py` | Test items | 1 | 17 |
| `test_airframe_geometry_manifest.py` | Max single-test span | 1013 | 103 |
| `test_airframe_geometry_manifest.py` | Assert count | 432 | 432 |
| `test_airframe_geometry_manifest.py` | Max asserts in one test | 432 | 45 |
| `test_airframe_geometry_manifest.py` | Max literals in one test | 1270 | 118 |
| `test_airframe_geometry_review_cli.py` | Test items | 1 | 13 |
| `test_airframe_geometry_review_cli.py` | Max single-test span | 655 | 95 |
| `test_airframe_geometry_review_cli.py` | Assert count | 268 | 269 |
| `test_airframe_geometry_review_cli.py` | Max asserts in one test | 268 | 52 |
| `test_airframe_geometry_review_cli.py` | Max literals in one test | 599 | 109 |

Validation:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/tools/test_airframe_geometry_manifest.py
# 17 tests collected

cmo_python -m pytest -q tests/tools/test_airframe_geometry_manifest.py
# 17 skipped

cmo_python -m pytest --collect-only -q tests/tools/test_airframe_geometry_review_cli.py
# 13 tests collected

cmo_python -m pytest -q tests/tools/test_airframe_geometry_review_cli.py
# 13 skipped

cmo_python -m ruff check tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py tools/runners/audit_test_system.py tests/runners/test_audit_test_system.py
# All checks passed
```

The skip result comes through the existing optional dependency boundary in
`tests.tools.airframe_review_fixtures.require_airframe_geometry_extra()`. It
confirms the refactored collection path is valid, but it does not prove the
airframe review behavior on a dependency-complete machine.

## Current P2-B Slice

Damage-model consolidation files:

- `tests/architecture/damage_model/test_candidate_artifact_contracts.py`
- `tests/architecture/damage_model/test_component_fragility_validation.py`
- `tests/architecture/damage_model/test_benchmark_recalculation_admission.py`
- `tests/architecture/damage_model/test_source_evidence_governance.py`
- `tests/architecture/damage_model/test_component_probability_artifacts.py`
- `tests/architecture/damage_model/test_scope_provenance_closeout_gates.py`
- `tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py`
- `tests/architecture/damage_model/test_provenance_identity_review_gate.py`
- `tests/architecture/damage_model/test_effect_scale_release_gate.py`
- `tests/architecture/damage_model/test_release_provenance_closeout_gate.py`

Before/after structural audit:

| File | Metric | Before | After |
| --- | --- | ---: | ---: |
| `test_candidate_artifact_contracts.py` | Test items | 17 | 26 |
| `test_candidate_artifact_contracts.py` | Max single-test span | 597 | 111 |
| `test_candidate_artifact_contracts.py` | Assert count | 560 | 560 |
| `test_candidate_artifact_contracts.py` | Max asserts in one test | 228 | 71 |
| `test_candidate_artifact_contracts.py` | Max literals in one test | 554 | 178 |
| `test_candidate_artifact_contracts.py` | Risk score | 10 | 8 |
| `test_component_fragility_validation.py` | Test items | 14 | 15 |
| `test_component_fragility_validation.py` | Max single-test span | 143 | 92 |
| `test_component_fragility_validation.py` | Assert count | 349 | 352 |
| `test_component_fragility_validation.py` | Max asserts in one test | 56 | 41 |
| `test_component_fragility_validation.py` | Max literals in one test | 140 | 83 |
| `test_component_fragility_validation.py` | Risk score | 10 | 8 |
| `test_benchmark_recalculation_admission.py` | Test items | 10 | 23 |
| `test_benchmark_recalculation_admission.py` | Max single-test span | 129 | 59 |
| `test_benchmark_recalculation_admission.py` | Assert count | 243 | 243 |
| `test_benchmark_recalculation_admission.py` | Max asserts in one test | 62 | 27 |
| `test_benchmark_recalculation_admission.py` | Max literals in one test | 157 | 69 |
| `test_benchmark_recalculation_admission.py` | Risk score | 8 | 8 |
| `test_source_evidence_governance.py` | Test items | 15 | 22 |
| `test_source_evidence_governance.py` | Max single-test span | 121 | 58 |
| `test_source_evidence_governance.py` | Assert count | 246 | 246 |
| `test_source_evidence_governance.py` | Max asserts in one test | 48 | 29 |
| `test_source_evidence_governance.py` | Max literals in one test | 113 | 65 |
| `test_source_evidence_governance.py` | Risk score | 8 | 8 |
| `test_component_probability_artifacts.py` | Test items | 8 | 23 |
| `test_component_probability_artifacts.py` | Max single-test span | 138 | 71 |
| `test_component_probability_artifacts.py` | Assert count | 212 | 212 |
| `test_component_probability_artifacts.py` | Max asserts in one test | 67 | 21 |
| `test_component_probability_artifacts.py` | Max literals in one test | 178 | 57 |
| `test_component_probability_artifacts.py` | Risk score | 8 | 8 |
| `test_scope_provenance_closeout_gates.py` | Test items | 11 | 25 |
| `test_scope_provenance_closeout_gates.py` | Max single-test span | 122 | 52 |
| `test_scope_provenance_closeout_gates.py` | Assert count | 218 | 218 |
| `test_scope_provenance_closeout_gates.py` | Max asserts in one test | 58 | 21 |
| `test_scope_provenance_closeout_gates.py` | Max literals in one test | 149 | 44 |
| `test_scope_provenance_closeout_gates.py` | Risk score | 8 | 8 |
| `test_mechanism_source_evidence_closeout.py` | Test items | 10 | 14 |
| `test_mechanism_source_evidence_closeout.py` | Max single-test span | 141 | 65 |
| `test_mechanism_source_evidence_closeout.py` | Assert count | 176 | 176 |
| `test_mechanism_source_evidence_closeout.py` | Max asserts in one test | 31 | 24 |
| `test_mechanism_source_evidence_closeout.py` | Max literals in one test | 140 | 64 |
| `test_mechanism_source_evidence_closeout.py` | Risk score | 8 | 8 |
| `test_provenance_identity_review_gate.py` | Test items | 6 | 11 |
| `test_provenance_identity_review_gate.py` | Max single-test span | 221 | 67 |
| `test_provenance_identity_review_gate.py` | Assert count | 116 | 116 |
| `test_provenance_identity_review_gate.py` | Max asserts in one test | 70 | 20 |
| `test_provenance_identity_review_gate.py` | Max literals in one test | 213 | 52 |
| `test_provenance_identity_review_gate.py` | Risk score | 8 | 4 |
| `test_effect_scale_release_gate.py` | Test items | 4 | 11 |
| `test_effect_scale_release_gate.py` | Max single-test span | 133 | 41 |
| `test_effect_scale_release_gate.py` | Assert count | 119 | 119 |
| `test_effect_scale_release_gate.py` | Max asserts in one test | 60 | 19 |
| `test_effect_scale_release_gate.py` | Max literals in one test | 151 | 51 |
| `test_effect_scale_release_gate.py` | Risk score | 8 | 4 |
| `test_release_provenance_closeout_gate.py` | Test items | 4 | 8 |
| `test_release_provenance_closeout_gate.py` | Max single-test span | 168 | 81 |
| `test_release_provenance_closeout_gate.py` | Assert count | 66 | 66 |
| `test_release_provenance_closeout_gate.py` | Max asserts in one test | 45 | 13 |
| `test_release_provenance_closeout_gate.py` | Max literals in one test | 151 | 52 |
| `test_release_provenance_closeout_gate.py` | Risk score | 6 | 1 |

Validation:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
# 26 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
# 26 passed

cmo_python -m ruff check tests/architecture/damage_model/test_candidate_artifact_contracts.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_component_fragility_validation.py
# 15 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_component_fragility_validation.py
# 15 passed

cmo_python -m ruff check tests/architecture/damage_model/test_component_fragility_validation.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# 23 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# 23 passed

cmo_python -m ruff check tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_source_evidence_governance.py
# 22 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_source_evidence_governance.py
# 22 passed

cmo_python -m ruff check tests/architecture/damage_model/test_source_evidence_governance.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_component_probability_artifacts.py
# 23 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_component_probability_artifacts.py
# 23 passed

cmo_python -m ruff check tests/architecture/damage_model/test_component_probability_artifacts.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# 25 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# 25 passed

cmo_python -m ruff check tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# 14 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# 14 passed

cmo_python -m ruff check tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# All checks passed

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_provenance_identity_review_gate.py
# 11 tests collected

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_effect_scale_release_gate.py
# 11 tests collected

cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# 8 tests collected

cmo_python -m pytest -q tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# 30 passed

cmo_python -m ruff check tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# All checks passed

cmo_python tools/runners/audit_test_system.py --format json --limit 300
# Static test items: 3145; no `tests/architecture/damage_model` file reports `oversized_test_item`.
```

The `test_component_fragility_validation.py` update also corrected stale
hardcoded synthetic-sigmoid expectations to the current deterministic artifact
output. The `test_benchmark_recalculation_admission.py` update converted three
oversized gate tests into module-fixture-backed semantic checks; it removes that
file's `oversized_test_item` flag but leaves the file-level literal/assert-heavy
residual active. The `test_source_evidence_governance.py` update similarly
split source payload and rights-output policy checks over module-level artifact
fixtures, removing that file's `oversized_test_item` flag while keeping
fail-closed source-rights assertions. The
`test_component_probability_artifacts.py` update split surface probe, snapshot,
and result-pack assertions over module-level artifact fixtures, removing that
file's `oversized_test_item` flag while retaining the Stage-C candidate
boundary checks. The `test_scope_provenance_closeout_gates.py` update split
target geometry, warhead family scope, and row-provenance closeout assertions
over module-level fixtures, removing that file's `oversized_test_item` flag
while retaining non-authoritative Stage-B closeout boundaries. Latest audit
after that slice should be interpreted as structural test-item splitting, not
as a new business-coverage claim. The
`test_mechanism_source_evidence_closeout.py` update split the mechanism-source
closeout gate into blocked identity, fail-closed checks, author-side evidence,
and residual-trace assertions over one module-level fixture, removing that
file's `oversized_test_item` flag while preserving the retained residual
authority boundary. The `test_provenance_identity_review_gate.py`,
`test_effect_scale_release_gate.py`, and
`test_release_provenance_closeout_gate.py` updates split provenance identity,
effect-scale readiness/closeout, and release-provenance closeout checks into
module-fixture-backed semantic tests. After those three splits, the audit runner
reports no remaining `oversized_test_item` files under
`tests/architecture/damage_model`; residual risk is now file-level
literal/source-scan concentration and tier policy, not a single-test-item
problem.

## Current P2-C Slice

Mixin collection files:

- `tests/runtime/air_combat/weapon_guidance_realism/test_a8_consumer_validation.py`
- `tests/runtime/air_combat/weapon_guidance_realism/test_geometry_and_edge_cases.py`
- `tests/runtime/air_combat/weapon_guidance_realism/test_launch_guidance_and_dynamics.py`
- `tests/runtime/air_combat/weapon_guidance_realism/test_vulnerability_authority.py`
- `tests/runtime/air_combat/weapon_guidance_realism/test_warhead_and_component_damage.py`

Evidence:

- [test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md)
- [../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md](../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md)

Validation:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/runtime/air_combat/weapon_guidance_realism
# 192 tests collected

cmo_python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism
# 45 failed, 167 passed, 221 subtests passed

cmo_python -m ruff check tests/runtime/air_combat/weapon_guidance_realism
# All checks passed
```

Decision: the hidden mixin pattern is retained as an explicit local/focused
wrapper suite, not promoted to smoke. The focused package run failure is a
behavior/test-expectation drift residual and is not repaired inside this
collection-visibility slice.

## Current P3-A Slice

Suite-tier validation:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners/test_pytest_suite_manifests.py
# 5 passed

cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
# 340 passed, 41 subtests passed
```

The smoke suite is explicit and does not include
`tests/runtime/air_combat/weapon_guidance_realism/`. That package remains a
local/focused residual until its focused package run is green.

## Current P4/P5 Validation

Acceptance validation:

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_component_fragility_validation.py tests/architecture/damage_model/test_benchmark_recalculation_admission.py tests/architecture/damage_model/test_source_evidence_governance.py tests/architecture/damage_model/test_component_probability_artifacts.py tests/architecture/damage_model/test_scope_provenance_closeout_gates.py tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py tests/runners/test_pytest_suite_manifests.py
# 205 passed, 30 skipped

cmo_python -m ruff check tools/runners/audit_test_system.py tests/runners/test_audit_test_system.py tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_component_fragility_validation.py tests/architecture/damage_model/test_benchmark_recalculation_admission.py tests/architecture/damage_model/test_source_evidence_governance.py tests/architecture/damage_model/test_component_probability_artifacts.py tests/architecture/damage_model/test_scope_provenance_closeout_gates.py tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py tests/runtime/air_combat/weapon_guidance_realism
# All checks passed

cmo_python -m pytest --collect-only -q tests --ignore=tests/archive
# 2000 tests collected

cmo_python tools/runners/audit_test_system.py --format markdown --limit 20
# Active test files: 341; static test items: 3145; risk-flagged Python files: 151

cmo_python -m coverage report --skip-empty
# TOTAL 34376 statements, 11916 missed, 65% covered

git diff --check
# clean

python <local markdown-link check>
# checked 18 markdown files; local links ok
```

The collect-only run still emits the retained Eventlet deprecation warning and
nanobind `ef_py.Side` leak diagnostic. Those are collection-time side effects,
not coverage or acceptance claims.

## Residual Register

| Residual | Status | Next action |
| --- | --- | --- |
| File-level literal-heavy `tests/tools` airframe checks | retained in issue | Run on a dependency-complete machine before behavior-preservation acceptance. |
| Literal/source-scan-heavy `tests/architecture/damage_model` closeout/candidate tests | retained in issue | Decide data-contract extraction or focused/local tier justification for remaining file-level guards. |
| Hidden mixin tests under `weapon_guidance_realism` | retained in issue | Wrapper pattern is documented; reconcile 45 package-level failures before smoke consideration. |
| Coverage statement ambiguity | retained in issue | Keep coverage records split by measured roots and by Python/C++ toolchain. |
| Smoke/focused/local tier drift | accepted for current slice | Smoke manifest and suite README exclude the failing `weapon_guidance_realism` package; future promotion should use explicit node IDs after behavior reconciliation. |

## Recommended Action Order

1. Follow the gates in
   [Test System Residual Governance](../../issues/test_system_residual_governance/README.md)
   for airframe, damage-model, weapon-guidance, and coverage residuals.
2. Keep this review subproject as the accepted current governance slice until a
   narrower follow-on issue or task supersedes one of those residual groups.
3. Do not reopen this slice merely because a residual remains visible; reopen
   it only if audit tooling, suite-tier policy, or accepted split evidence is
   found to be wrong.

## Explicit Overclaim Refusals

- Do not call the whole test system healthy from the audit runner passing.
- Do not treat a lower risk score as coverage preservation unless focused tests
  or contracts pass.
- Do not claim full C++ or runtime coverage from Python smoke coverage data.
- Do not convert architecture guardrails into smoke gates merely because they
  are important; broad source scans need explicit tier decisions.
