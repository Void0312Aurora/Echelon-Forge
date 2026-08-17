# Architecture Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-17`

This owner covers cross-domain system architecture, runtime layers, contracts,
backends, and architecture decisions. Maintained standards, references, issues,
and reviews now live in this owner; legacy plan packets are archive provenance.

## Standards

- [Simulation conventions](standards/simulation_conventions.md): maintained
  engine-neutral coordinate, unit, observation, array, action, and determinism
  conventions.
- [Runtime workflow and contract baseline](standards/runtime_workflow_and_contract_baseline.md):
  maintained loader-to-runtime stage ownership and roundtrip seams, subordinate
  to the strict simulation architecture baseline.
- [Simulation system architecture design](standards/simulation_system_architecture_design.md):
  strict maintained layering, authority, and runtime baseline.

## Reference

- [Truth-leak inventory](reference/t8_g4_truth_leak_inventory.md): current
  declared/open authority leaks and their verification boundary.

## Active Work

- [Cordis simulation composition kernel](work/active/cordis_simulation_composition_kernel/README.md):
  active long-term program for a Cordis composition control plane, native
  lifecycle kernel, deterministic manifest realization, provider/system/backend
  composition, and host parity; no runtime integration is claimed yet.

## Open Issues

- [System modularization issue](work/issues/modularization_plan.md): draft
  residual analysis; directory placement does not authorize implementation.
- [System layering and engine encapsulation](work/issues/system_layering_and_engine_encapsulation_plan.md)
- [Architecture and performance research follow-up](work/issues/architecture_and_performance_research_followup.md)
- [Runtime facade contract](work/issues/runtime_facade_contract_plan.md)
- [C++ dependency and DTO residuals](work/issues/cpp_dependency_and_dto_residuals.md)
- [Exact-runtime refactor](work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [GPU mainline integration checklist](work/issues/exact_runtime/gpu_execution_mainline_integration_checklist.md)

## Reviews

- [Cordis simulation composition program architecture review — 2026-08-17](reviews/cordis_simulation_composition_program_review_20260817.md):
  advisory macro review that retains the native composition direction while
  requiring authority and program-boundary revision before later
  system/plugin/host phases.
- [Response to the Cordis simulation composition program architecture review — 2026-08-17](reviews/cordis_simulation_composition_program_review_response_20260817.md):
  active-owner disposition that incorporates the authority, typed-admission,
  capability, evidence-timing, and independent-slice findings while retaining
  Cordis as a required strategic composition target and keeping Node
  conditional.
- [Architecture review — 2026-06-03](reviews/architecture_review_20260603.md)
- [Architecture norms and correctness review — 2026-06-03 (Chinese only)](reviews/architecture_norms_correctness_review_20260603.zh.md)
- [Architecture refactoring audit — 2026-05-22](reviews/architecture_refactoring_audit_20260522.md)
- [UniversalEnv caller survival table — 2026-06-12 (Chinese only)](reviews/universal_env_runtime_compatibility_caller_survival_table_20260612.zh.md)

These are retained review snapshots. They do not replace current standards,
plans, implementation, or executable evidence.

Use the [shared documentation structures](../engineering/documentation/structure_examples.md)
for future architecture standards, references, work, and reviews.
