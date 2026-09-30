# Architecture Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-09-25`

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
- [Runtime composition baseline](standards/runtime_composition_baseline.md):
  maintained default CPU-exact Cordis/owner/native authority chain, single
  construction truth, compatibility rules, evidence gates, and held residuals.

## Reference

- [Truth-leak inventory](reference/t8_g4_truth_leak_inventory.md): current
  declared/open authority leaks and their verification boundary.

## Active Work

- [Long-horizon architecture governance](work/active/long_horizon_architecture_governance/README.md):
  active program for immutable admitted kernels, host-owned replacement,
  consolidated composition authority, physical facade boundaries, lifecycle-
  governed controls, and sustainable CI/evidence evolution. P0 authority and
  baseline, P1 target decisions, the complete P3-A/P3-B/P3-C public contract,
  authority-envelope, ledger, and compatibility foundations, and the P4-A
  dark/shadow host lifecycle and the P4-B/P4-C internal candidate tasks are
  accepted; P2 control-lifecycle and P5-P8 remain open, while no production
  truth publication, runtime migration or production cutover is accepted.

## Completed Work

- [Cordis simulation composition kernel](work/archive/cordis_simulation_composition_kernel/README.md):
  accepted bounded default CPU-exact composition program and historical
  implementation evidence. Current authority is the runtime composition
  standard above; Node, CUDA, broader profiles/providers, external plugins, and
  complete replay remain held residuals.

## Active Work

- [Stable entity identity for stochastic draws](work/active/stable_entity_identity/README.md):
  English-only task package replacing raw Flecs ids in per-engagement and
  per-detection seeds with a per-world serial and the reset seed.

## Open Issues

- [System modularization issue](work/issues/modularization_plan.md): draft
  residual analysis; directory placement does not authorize implementation.
- [Cross-domain scripted agent system](work/issues/cross_domain_scripted_agent_system_plan.md):
  draft plan for an independent, fully playable scripted-agent line across
  Air, Naval, Ground, and future domain profiles.
- [System layering and engine encapsulation](work/issues/system_layering_and_engine_encapsulation_plan.md)
- [Architecture and performance research follow-up](work/issues/architecture_and_performance_research_followup.md)
- [Runtime facade contract](work/issues/runtime_facade_contract_plan.md)
- [C++ dependency and DTO residuals](work/issues/cpp_dependency_and_dto_residuals.md)
- [Exact-runtime refactor](work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [GPU mainline integration checklist](work/issues/exact_runtime/gpu_execution_mainline_integration_checklist.md)

## Reviews

- [Cross-domain scripted agent system consumer census — 2026-09-24](reviews/cross_domain_scripted_agent_system_consumer_census_20260924.md):
  advisory WP0 review; confirms the existing neutral tasking seam, compiled
  AgentRole/intent authority, RL-adjacent entanglements, and domain capability
  limits before implementation.
- [Cross-domain scripted agent capability evidence matrix — 2026-09-25](reviews/cross_domain_scripted_agent_capability_matrix_20250925.md):
  maintained evidence boundary for Air candidate, Naval bounded adapter, and
  Ground held labels; records the manifest shape and promotion gates.
- [Air scripted algorithm substitution research — 2026-09-26](reviews/air_scripted_algorithm_substitution_research_20260926.md):
  maintained research record for planner/assessor/observation/action strategy
  seams, dependency injection, migration batches, and replacement gates.
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
