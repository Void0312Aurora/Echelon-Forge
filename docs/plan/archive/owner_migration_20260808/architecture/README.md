# `architecture/`

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory holds the strict simulation-system architecture baseline, the
active architecture plan, performance follow-up research, and archived `src/`
layering records.

Current architecture stance:

- Echelon Forge is framed as a semantic-causal simulation compiler and learning
  platform.
- The maintained runtime kernel is organized by the SCAL faces: semantic,
  causal, agentic, and learning-facing architecture.
- The temporal DAG is an execution projection inside a broader
  graph-of-graphs model covering semantic, causal, information, agency,
  evidence, and future learning graphs.
- Backend acceleration, resident-state, and shadow-style work must cite the
  accepted WP6 backend profile registries and parity budgets before becoming
  maintained capabilities. The WP6 evidence is archived task history; see the
  [resident-state boundary rules](../../../../task/simulation_architecture/archive/wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
  and [WP6 acceptance review](../../../../task/review/archive/wp-acceptance/wp6_backend_profile_policy_acceptance_review_20260519.md).
- The post-WP6 implementation-preparation evidence is the archived
  [WP7 backend capability materialization](../../../../task/simulation_architecture/archive/wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md)
  line, which covers machine-checkable registry materialization, conservative
  runtime capability projection, promotion evidence gates, and multi-fidelity
  entry conditions without promoting candidate capabilities; its
  [acceptance review](../../../../task/review/archive/wp-acceptance/wp7_backend_capability_materialization_acceptance_review_20260519.md)
  accepts documentation and implementation readiness only, while current exact
  GPU, resident-state, shadow, device observation, and multi-fidelity support
  remain false.
- The active task line for turning this into implementation work is
  [docs/task/simulation_architecture/](../../../../task/simulation_architecture/README.md).

Recommended reading order:

1. [simulation_system_architecture_design.md](../../../../architecture/standards/simulation_system_architecture_design.md)
2. [simulation_system_architecture_design.zh.md](../../../../architecture/standards/simulation_system_architecture_design.zh.md)
3. [system_layering_and_engine_encapsulation_plan.md](../../../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.md)
4. [system_layering_and_engine_encapsulation_plan.zh.md](../../../../architecture/work/issues/system_layering_and_engine_encapsulation_plan.zh.md)
5. [architecture_and_performance_research_followup.md](../../../../architecture/work/issues/architecture_and_performance_research_followup.md)
6. [architecture_and_performance_research_followup.zh.md](../../../../architecture/work/issues/architecture_and_performance_research_followup.zh.md)
7. [archive/src_layered_refactor_freeze.zh.md](../../architecture/src_layered_refactor_freeze.zh.md)

Usage rules:

- The target steady state for this directory is English canonical `.md` files
  with optional Chinese `.zh.md` companions.
- During migration, some long-form plan/freeze docs still exist only as
  `.zh.md`; treat them as transitional sources until the English peer is added.
- Research docs provide rationale and option ordering; they do not authorize
  implementation by themselves.
- Completed freeze records are execution records. New scope should be frozen
  separately.
- The simulation-system design is the current strict architecture baseline.
  Turn broad implementation work into scoped task sheets under
  [docs/task/simulation_architecture/](../../../../task/simulation_architecture/README.md).
