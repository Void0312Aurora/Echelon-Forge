# Test System Governance Acceptance 2026-06-20

Status: `2026-06-21` accepted with tracked residuals; audit infrastructure,
P1-B evidence semantics, P2 structural splits, P2-C collection documentation,
and P3 suite-tier validation are accepted for this slice. Overall test-system
health is not accepted; residual blockers are tracked in
[Test System Residual Governance](../../issues/test_system_residual_governance/README.md).

## Accepted Scope

Accepted for this dated record:

- A new branch-scoped test-system governance surface exists under
  `docs/task/review/test_system_governance/`.
- The initial audit runner provides a repeatable, non-archive active-test
  inventory and risk triage.
- Runner tests and documentation exist for the audit workflow.
- `tests/tools/test_airframe_geometry_manifest.py` has been structurally split
  into report-scoped tests without reducing its existing assertion count.
- `tests/tools/test_airframe_geometry_review_cli.py` has been structurally
  split into artifact-scoped tests over a single module-level CLI fixture.
- P1-B evidence now separates static audit counts, pytest working-tree
  collection, local Python coverage, and absent C++ coverage.
- `tests/architecture/damage_model/test_candidate_artifact_contracts.py` has
  been structurally split so the candidate-bundle check no longer has an
  oversized single test item.
- `tests/architecture/damage_model/test_component_fragility_validation.py` has
  been structurally split so the readiness gate no longer has an oversized
  single test item, and stale synthetic-sigmoid expectations now match current
  deterministic artifact output.
- `tests/architecture/damage_model/test_benchmark_recalculation_admission.py`
  has been structurally split so the recalculation, lineage tolerance, and
  replacement tolerance gate checks no longer carry an oversized single test
  item.
- `tests/architecture/damage_model/test_source_evidence_governance.py` has been
  structurally split so the source payload pack and rights-output policy checks
  no longer carry oversized single test items.
- `tests/architecture/damage_model/test_component_probability_artifacts.py`
  has been structurally split so the surface-probe, snapshot, and result-pack
  checks no longer carry oversized single test items.
- `tests/architecture/damage_model/test_scope_provenance_closeout_gates.py`
  has been structurally split so target-geometry, warhead-family, and
  row-provenance closeout checks no longer carry oversized single test items.
- `tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py`
  has been structurally split so blocked identity, fail-closed closeout,
  author-side evidence, and residual-trace checks no longer carry an oversized
  single test item.
- `tests/architecture/damage_model/test_provenance_identity_review_gate.py`
  has been structurally split so retained source, allowed-output policy,
  benchmark/comparison, identity validation, signoff, and residual-trace checks
  no longer carry an oversized single test item.
- `tests/architecture/damage_model/test_effect_scale_release_gate.py` has been
  structurally split so readiness and closeout checks no longer carry oversized
  single test items.
- `tests/architecture/damage_model/test_release_provenance_closeout_gate.py`
  has been structurally split so RES-001 source/policy/benchmark, RES-002
  identity, residual trace, and guard checks no longer carry an oversized
  single test item.
- `tests/runtime/air_combat/weapon_guidance_realism/` has an explicit local
  README documenting the five wrapper classes that collect hidden capability
  mixin tests.
- Smoke-suite manifests remain explicit and do not include the failing
  `weapon_guidance_realism` package.
- Remaining airframe, damage-model, weapon-guidance, and coverage blockers are
  retained in
  [Test System Residual Governance](../../issues/test_system_residual_governance/README.md).

Not accepted / retained boundaries:

- Overall test-system health.
- Full Python or C++ coverage sufficiency.
- Completion of the whole `tests/tools` simplification cluster.
- Completion of the whole `tests/architecture/damage_model` simplification
  cluster.
- Any new smoke/focused/local/manual suite policy beyond the documented audit
  interpretation rules.
- `weapon_guidance_realism` behavior acceptance; its package-level focused run
  currently fails.
- Airframe geometry behavior acceptance on a dependency-complete environment;
  the local focused run skipped through the pre-existing optional dependency
  gate.

## Validation Commands And Outcomes

```bash
source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners/test_audit_test_system.py
# 3 passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners
# 27 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tools/runners/audit_test_system.py tests/runners/test_audit_test_system.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 12
# Completed and reported active test/risk/contract summary.

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/tools/test_airframe_geometry_manifest.py
# 17 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/tools/test_airframe_geometry_manifest.py
# 17 skipped

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/tools/test_airframe_geometry_review_cli.py
# 13 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/tools/test_airframe_geometry_review_cli.py
# 13 skipped

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py tools/runners/audit_test_system.py tests/runners/test_audit_test_system.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests --ignore=tests/archive
# Historical P1-B snapshot: 1917 tests collected in 3.46s.
# Current closeout snapshot below: 2000 tests collected.

source tools/maintenance/cmo_env.sh
cmo_python -m coverage report --skip-empty
# Historical P1-B snapshot: TOTAL 34407 statements, 11945 missed, 65% covered.
# Current closeout snapshot below: TOTAL 34376 statements, 11916 missed, 65% covered.

source tools/maintenance/cmo_env.sh
cmo_python tools/runners/measure_test_coverage.py --skip-python --skip-cpp --output-dir /tmp/cmo-coverage-metadata-p1b
# Metadata written with python_sources ["gym_envs", "python"] and no report results.

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
# 26 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_candidate_artifact_contracts.py
# 26 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_candidate_artifact_contracts.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_component_fragility_validation.py
# 15 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_component_fragility_validation.py
# 15 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_component_fragility_validation.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# 23 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# 23 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_benchmark_recalculation_admission.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_source_evidence_governance.py
# 22 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_source_evidence_governance.py
# 22 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_source_evidence_governance.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_component_probability_artifacts.py
# 23 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_component_probability_artifacts.py
# 23 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_component_probability_artifacts.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# 25 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# 25 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_scope_provenance_closeout_gates.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# 14 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# 14 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_provenance_identity_review_gate.py
# 11 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_effect_scale_release_gate.py
# 11 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# 8 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# 30 passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python tools/runners/audit_test_system.py --format markdown --limit 5
# Active test files: 343; static test items: 1990; risk-flagged Python files: 152.
# No `tests/architecture/damage_model` file reports `oversized_test_item`.

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests/runtime/air_combat/weapon_guidance_realism
# 192 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runtime/air_combat/weapon_guidance_realism
# 45 failed, 167 passed, 221 subtests passed

source tools/maintenance/cmo_env.sh
cmo_python -m ruff check tests/runtime/air_combat/weapon_guidance_realism
# All checks passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners/test_pytest_suite_manifests.py
# 5 passed

source tools/maintenance/cmo_env.sh
cmo_python tools/runners/run_pytest_suite.py --suite tests/smoke/ci_smoke_suite.json
# 340 passed, 41 subtests passed

source tools/maintenance/cmo_env.sh
cmo_python -m pytest -q tests/runners tests/tools/test_airframe_geometry_manifest.py tests/tools/test_airframe_geometry_review_cli.py tests/architecture/damage_model/test_candidate_artifact_contracts.py tests/architecture/damage_model/test_component_fragility_validation.py tests/architecture/damage_model/test_benchmark_recalculation_admission.py tests/architecture/damage_model/test_source_evidence_governance.py tests/architecture/damage_model/test_component_probability_artifacts.py tests/architecture/damage_model/test_scope_provenance_closeout_gates.py tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py tests/architecture/damage_model/test_provenance_identity_review_gate.py tests/architecture/damage_model/test_effect_scale_release_gate.py tests/architecture/damage_model/test_release_provenance_closeout_gate.py tests/runners/test_pytest_suite_manifests.py
# 205 passed, 30 skipped

source tools/maintenance/cmo_env.sh
cmo_python -m pytest --collect-only -q tests --ignore=tests/archive
# 2000 tests collected

source tools/maintenance/cmo_env.sh
cmo_python -m coverage report --skip-empty
# TOTAL 34376 statements, 11916 missed, 65% covered

git diff --check
# clean

python <local markdown-link check>
# checked 18 markdown files; local links ok
```

## Evidence Artifacts

- [../../../../tools/runners/audit_test_system.py](../../../../tools/runners/audit_test_system.py)
- [../../../../tests/runners/test_audit_test_system.py](../../../../tests/runners/test_audit_test_system.py)
- [../../../../tests/README.md](../../../../tests/README.md)
- [../../../../tests/tools/test_airframe_geometry_manifest.py](../../../../tests/tools/test_airframe_geometry_manifest.py)
- [../../../../tests/tools/test_airframe_geometry_review_cli.py](../../../../tests/tools/test_airframe_geometry_review_cli.py)
- [../../../../tests/architecture/damage_model/test_candidate_artifact_contracts.py](../../../../tests/architecture/damage_model/test_candidate_artifact_contracts.py)
- [../../../../tests/architecture/damage_model/test_component_fragility_validation.py](../../../../tests/architecture/damage_model/test_component_fragility_validation.py)
- [../../../../tests/architecture/damage_model/test_benchmark_recalculation_admission.py](../../../../tests/architecture/damage_model/test_benchmark_recalculation_admission.py)
- [../../../../tests/architecture/damage_model/test_source_evidence_governance.py](../../../../tests/architecture/damage_model/test_source_evidence_governance.py)
- [../../../../tests/architecture/damage_model/test_component_probability_artifacts.py](../../../../tests/architecture/damage_model/test_component_probability_artifacts.py)
- [../../../../tests/architecture/damage_model/test_scope_provenance_closeout_gates.py](../../../../tests/architecture/damage_model/test_scope_provenance_closeout_gates.py)
- [../../../../tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py](../../../../tests/architecture/damage_model/test_mechanism_source_evidence_closeout.py)
- [../../../../tests/architecture/damage_model/test_provenance_identity_review_gate.py](../../../../tests/architecture/damage_model/test_provenance_identity_review_gate.py)
- [../../../../tests/architecture/damage_model/test_effect_scale_release_gate.py](../../../../tests/architecture/damage_model/test_effect_scale_release_gate.py)
- [../../../../tests/architecture/damage_model/test_release_provenance_closeout_gate.py](../../../../tests/architecture/damage_model/test_release_provenance_closeout_gate.py)
- [../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md](../../../../tests/runtime/air_combat/weapon_guidance_realism/README.md)
- [README.md](README.md)
- [test_system_governance_task_clusters_20260620.md](test_system_governance_task_clusters_20260620.md)
- [test_system_governance_current_status_20260620.md](test_system_governance_current_status_20260620.md)
- [test_system_governance_p1b_evidence_20260621.md](test_system_governance_p1b_evidence_20260621.md)
- [test_system_governance_p2c_mixin_evidence_20260621.md](test_system_governance_p2c_mixin_evidence_20260621.md)

## Open Residuals

- [Test System Residual Governance](../../issues/test_system_residual_governance/README.md)
  owns the remaining open residuals after this accepted slice:
  dependency-complete airframe execution, damage-model file-level
  literal/source-scan concentration, failing `weapon_guidance_realism`, and
  separate Python/C++ coverage evidence.

## Forbidden Claims

- Do not claim the test system is simplified.
- Do not claim full business coverage from the audit runner.
- Do not claim C++ coverage from Python `.coverage`.
- Do not move a broad source-scan architecture guard into CI smoke without a
  node-ID or manifest-specific gate decision.

## Index Synchronization

- Parent review README and Chinese companion must link this subproject before
  the subproject is treated as the current test-system governance surface.
- Archive is empty except for [archive/README.md](archive/README.md).
