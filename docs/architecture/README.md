# Architecture Documentation

Language: English canonical; [Chinese companion](README.zh.md).

Document kind: `reference`
Lifecycle: `maintained`
Canonical: `docs/architecture/README.md`
Owner: `cross-domain architecture`
Last verified: `2026-08-27`

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
  baseline, P1 target decisions, and the complete P3-A/P3-B/P3-C public
  contract, authority-envelope, ledger, and compatibility foundations are
  accepted; P2 control-lifecycle and P4-P8 remain open, while no runtime
  migration or production cutover is accepted.

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
- [System layering and engine encapsulation](work/issues/system_layering_and_engine_encapsulation_plan.md)
- [Architecture and performance research follow-up](work/issues/architecture_and_performance_research_followup.md)
- [Runtime facade contract](work/issues/runtime_facade_contract_plan.md)
- [C++ dependency and DTO residuals](work/issues/cpp_dependency_and_dto_residuals.md)
- [Exact-runtime refactor](work/issues/exact_runtime/cpp_exact_runtime_refactor_plan.md)
- [GPU mainline integration checklist](work/issues/exact_runtime/gpu_execution_mainline_integration_checklist.md)

## Reviews

- [Long-horizon architecture governance plan review — 2026-08-25](reviews/long_horizon_architecture_governance_plan_review_20260825.md):
  independent P0-B review of lifecycle fencing, phase order, mixed-version
  rollout, run receipts, control retirement, operations, topology, and
  evidence durability. Initial and first repair verdicts were repair-required;
  the final repair review passed without shrinking the long-horizon outcome.
- [Long-horizon architecture governance P1 review — 2026-08-25](reviews/long_horizon_architecture_governance_p1_review_20260825.md):
  independent `gpt-5.6-sol` max review of host bootstrap/replacement/recovery and
  shutdown, plan/release/checkpoint/receipt authority, canonical journal/storage,
  one production-canary cutover, package rollback, operations and security. The
  final repair snapshot passed with no unresolved critical/high finding.
- [Long-horizon architecture governance P3-A review — 2026-08-25](reviews/long_horizon_architecture_governance_p3a_review_20260825.md):
  independent `gpt-5.6-sol` max review of the engine-independent public identity
  target, same-build value/schema authority, result/epoch semantics, actual
  target/install graph, and negative bypass gates. The repaired snapshot passed
  with no unresolved finding and no caller cutover.
- [Long-horizon architecture governance P3-B review — 2026-08-25](reviews/long_horizon_architecture_governance_p3b_review_20260825.md):
  independent `gpt-5.6-sol` max review of the typed authority envelope/schema
  owner, one-way provenance-bound adapter, exact cross-language vectors, native
  boundary and Cordis conformance. The repaired snapshot passed with no
  unresolved Critical/High finding and no short-term substitution.
- [Long-horizon architecture governance P3-C review — 2026-08-27](reviews/long_horizon_architecture_governance_p3c_review_20260827.md):
  independent `gpt-5.6-sol` max adversarial and repair review of the
  non-production ArtifactLedger, exact N/N-1 compatibility, fencing, recovery,
  kill/backout, ACL and snapshot gates. The final repaired snapshot passed with
  no unresolved Critical/High/Medium finding; P5-B/P5-D production authority
  remains held.
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
