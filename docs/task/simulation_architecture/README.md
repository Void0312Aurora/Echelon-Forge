# Simulation Architecture

Status: active subproject opened on `2026-05-19`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject turns the strict simulation architecture baseline into scoped
work packages. It should be used before starting broad implementation across
weapons, naval runtime, sensor/track, command/tasking, facade, or backend
acceleration.

Architecture authority:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [system layering and engine encapsulation plan](../../plan/architecture/system_layering_and_engine_encapsulation_plan.md)
- [architecture and performance follow-up](../../plan/architecture/architecture_and_performance_research_followup.md)

## Current Position

The active design conclusion is:

1. The project should be treated as a SCAL system: semantic, causal, agentic,
   and learning-facing, with `WP0-WP5` building the verified runtime kernel,
   `WP6` closing backend profile policy for acceleration and resident-state
   work, and `WP7` materializing that policy into registry, projection,
   evidence, and multi-fidelity entry tasks.
2. The project should follow one canonical semantic lifecycle.
3. Real execution should use a causal-temporal execution model. The temporal
   DAG is the scheduling projection, with feedback crossing explicit
   state-store or event-queue boundaries.
4. Air, naval, weapon, and future domains should extend that lifecycle through
   stage-local model families, capability bundles, and stage-node contracts.
5. Runtime facade and typed request/result contracts should become the long-term
   frontend dependency.
6. Policy computation and test/orchestration should be modeled as explicit
   producers and consumers of facade contracts, not as hidden owners of
   simulation state.
7. Information-state boundaries must distinguish `World Truth`,
   `ObservationPacket`, and `DecisionBelief`.
8. Local work on this machine should focus on build/import/smoke, architecture
   docs, contract design, and simulation assembly rather than RL training.
9. Backend acceleration and resident-state work should be routed through
   explicit backend profiles and parity budgets behind contracts, not through
   a second semantic path.
10. Backend capability implementation should start from the accepted WP6
    registry and parity records, then add machine-checkable materialization and
    evidence gates before any exact GPU, resident-state, shadow, or
    multi-fidelity capability can become maintained.
11. The maintained training-path bridge between accepted facade contracts and
    future learning-facing consumers should be routed through a separate
    `WP7.5` line that migrates batch training paths away from
    `RuntimeFacade.runtime()`.
12. Learning-face work should be routed through a separate `WP8` task family
    focused on curriculum, evaluation, capability profiling, scenario
    generation, and learning evidence; it should not reopen the simulation
    closure or assume local RL training availability.
13. When this subproject is split across subagents or workers, follow the
    [Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md):
    keep write scopes disjoint, keep one integration owner, and do not split
    the same normative table across concurrent authors.

## Work Packages

| Work package | Status | Goal | Output |
|--------------|--------|------|--------|
| `WP0 Architecture Baseline` | complete | Make the SCAL framing, semantic lifecycle, causal-temporal execution projection, and extension rules explicit | architecture design doc, task subproject entry |
| `WP1 Pipeline Inventory` | complete | Map current code, systems, models, and tests onto `P0-P10` and current coupling hotspots | [pipeline inventory](wp1_pipeline_inventory/pipeline_inventory_wp1_20260519.md) |
| `WP2 Contract Freeze` | complete | Identify packet families, stage-node contracts, and cross-layer policy/orchestration contracts that need explicit ownership | [contract freeze](wp2_contract_freeze/contract_freeze_wp2_20260519.md) |
| `WP2.5 Scheduler Semantics Freeze` | complete | Freeze event ordering, state versioning, barrier visibility, clock-domain merge policy, replay contract, and stage-node manifest schema | [scheduler semantics freeze](wp25_scheduler_semantics/scheduler_semantics_wp25_20260519.md), [acceptance review](../review/wp25_scheduler_semantics_acceptance_review_20260519.md) |
| `WP3 Engagement Pilot` | complete | Use weapon/engagement as the first cross-domain validation slice | [engagement pilot task family](wp3_engagement_pilot/engagement_pilot_wp3_20260519.md) |
| `WP4 Facade Alignment` | complete | Ensure pilot behavior is reachable through facade-shaped APIs without raw runtime access | [facade alignment task family](wp4_facade_alignment/facade_alignment_wp4_20260519.md), [final acceptance](../review/wp4_facade_alignment_acceptance_review_20260519.md) |
| `WP5 Validation Harness` | complete | Add smoke, architecture, trace, boundary, information-leakage, and replay/evidence tests that prove the shared lifecycle and graph boundaries | [validation harness task family](wp5_validation_harness/validation_harness_wp5_20260519.md), [final acceptance](../review/wp5_validation_harness_acceptance_review_20260519.md) |
| `WP6 Backend Profile Policy` | complete | Freeze backend profile taxonomy, parity budgets, resident-state boundaries, and backend capability exposure rules | [backend profile policy](wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md), [profile registry](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md), [parity budget registry](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md), [resident-state boundary rules](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md), [acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md) |
| `WP7 Backend Capability Materialization` | complete / accepted | Materialize accepted WP6 policy into machine-checkable registry, runtime capability projection, promotion evidence gates, and multi-fidelity entry conditions without promoting candidates | [backend capability materialization](wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md), [registry materialization](wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.md), [runtime capability projection](wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md), [promotion evidence gates](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md), [multi-fidelity entry conditions](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.md), [acceptance review](../review/wp7_backend_capability_materialization_acceptance_review_20260519.md) |
| `WP7.5 Training Path Facade Bridge` | planned | Migrate maintained batch training paths from `RuntimeFacade.runtime()` and raw `WorldBatchRuntime` stepping to facade-shaped execution and observation APIs before `WP8` depends on them | [training path facade bridge](wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md) |
| `WP8 SCAL Learning Face` | planned | Define curriculum, evaluation, capability profiling, scenario generation, and learning evidence as explicit architecture and task vocabulary without reopening the simulation closure | [learning face task family](wp8_learning_face/learning_face_wp8_20260520.md) |

### WP2.5 Workstream Map

WP2.5 is a freeze document, but the follow-on work is split into bounded
streams:

- `WP2.5-F StageNodeManifest Schema` first:
  [manifest/event cluster](wp25_scheduler_semantics/wp25_manifest_event_cluster_20260519.md).
- `WP2.5-A Event Ordering and ID Rules`, `WP2.5-B State Shard Versioning`, and
  `WP2.5-C Barrier Visibility` in parallel after the manifest vocabulary is
  stable:
  [state/barrier cluster](wp25_scheduler_semantics/wp25_state_barrier_cluster_20260519.md).
- `WP2.5-D Clock-Domain Merge` after those semantic rules are stable.
- `WP2.5-E Deterministic Replay Contract` after the scheduler semantics are
  frozen:
  [clock/replay cluster](wp25_scheduler_semantics/wp25_clock_replay_cluster_20260519.md).
- `WP2.5-G Integration and Index Sync` last, as the serial publication pass.

`WP2.5-D` and `WP2.5-E` are the highest-reasoning streams.

## WP7.5 Training Path Facade Bridge

Output:

- [WP7.5 Training Path Facade Bridge](wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

`WP7.5` is the missing bridge between accepted simulation-side facade
contracts and planned learning-facing contract vocabulary. It does not replace
`WP8`; instead, it migrates the maintained training mainline away from the
`RuntimeFacade.runtime()` escape hatch and toward
`RuntimeFacade.step_execution_batch()` plus
`RuntimeFacade.export_observation_packet()`.

`WP7.5` workstream map:

- `WP7.5-A Step Execution Mainline` migrates maintained batch stepping onto
  `ExecutionBatchStepRequest` / `ExecutionBatchStepResult`.
- `WP7.5-B Observation Packet Mainline` migrates maintained observation reads
  onto `ObservationBatchRequest` / `ObservationBatchPacket`.
- `WP7.5-C Compatibility Escape Hatch Reduction` narrows raw runtime access to
  explicit compatibility or diagnostics seams.
- `WP7.5-D Validation And Integration Sync` is serial and publishes the bridge
  line into README, review, and `WP8` references.

`WP7.5-A` and `WP7.5-B` are the highest-reasoning streams because they change
the maintained training mainline while preserving current facade and
information-state rules.

`WP7.5` work should use the project subagent rules in
[Subagent Usage Policy](../../standards/governance/subagent_usage_policy.md)
when it is split across workers.

## WP8 SCAL Learning Face

Output:

- [WP8 SCAL Learning Face task family](wp8_learning_face/learning_face_wp8_20260520.md)

WP8 gives the deferred SCAL learning face a bounded task family. It does not
add a second runtime lifecycle. It turns curriculum, evaluation, capability
profiling, scenario generation, and learning evidence into explicit experiment
and planning contracts that remain separate from the authoritative simulation
layer.

WP8 workstream map:

- `WP8-A Curriculum And Scenario Generation` defines how scenarios, seeds,
  curriculum phases, and generation requests are selected and versioned.
- `WP8-B Evaluation And Capability Profiling` defines benchmark protocols,
  profile schemas, score attribution, and capability evidence.
- `WP8-C World-Model Interface And Learning Evidence` defines how learning
  consumes facade-shaped observations and records evidence without becoming a
  truth source.
- `WP8-D Integration And Index Sync` is serial and updates task/review
  indexes, cross-references, and bilingual alignment.

`WP8-B` and `WP8-C` are the highest-reasoning streams because they have to
keep learning outputs comparable without drifting into hidden truth ownership.

## WP0 Scope

WP0 is documentation-only:

- add the strict architecture baseline,
- open this task subproject,
- update navigation entries,
- avoid code changes,
- avoid deciding exact field layouts before WP1/WP2 evidence is collected.

Exit criteria:

1. `docs/plan/architecture` has a clear architecture authority document.
2. `docs/task` has a simulation architecture entry.
3. The task entry explains why weapon work should be treated as a cross-domain
   engagement pilot with multiple clock domains, not a standalone vertical
   stack.

## WP1 Pipeline Inventory

WP1 should inspect the live code and produce a table that maps existing assets
onto the canonical semantic lifecycle:

- `P0 ContentCompile`
- `P1 WorldSetup`
- `P2 TaskingIntent`
- `P3 CommandDelivery`
- `P4 PlatformControl`
- `P5 PhysicsStep`
- `P6 SenseTrackLink`
- `P7 FireControlLaunch`
- `P8 MunitionLifecycle`
- `P9 EffectsDamage`
- `P10 ObservationExport`

Expected evidence:

- relevant `src/components/*` DTOs,
- `src/systems/*` stage behavior,
- `src/models/*` model implementations,
- `src/core/engine/*` orchestration surfaces,
- `src/runtime/facade/*` request/result coverage,
- Python adapter compatibility paths,
- tests that already enforce or violate the intended boundary,
- evidence of clock domains, event queues, state-store feedback, or current
  cross-stage coupling.

WP1 should not implement new code unless a small doc or test fixture is required
to complete the inventory.

## WP2 Contract Freeze

Input:

- [WP1 pipeline inventory](pipeline_inventory_wp1_20260519.md)

Output:

- [WP2 contract freeze](contract_freeze_wp2_20260519.md)

WP2 should turn the inventory into a scoped contract plan. It should decide:

1. which packet families already exist,
2. which are compatibility aggregations,
3. which need new facade-level request/result APIs,
4. which should stay component-only,
5. which stage nodes need explicit read/write sets, clock domains, latency
   policies, and sync policies,
6. which same-window DAG edges are data-derived versus cross-window feedback,
7. which state shards need versioning now or later for partial sync,
8. which event families need deterministic `(timestamp, priority, event_id)`
   ordering,
9. which clock domains can use default nested triggering and which need an
   explicit merge policy,
10. which Python calls need adapter compatibility,
11. which observation schemas are policy/test-owned `ObservationViewSpec`
    variants versus simulation-owned state exports,
12. how policy action cadence maps onto `P3/P4/P5` using `ActionIntentPacket`
    and `ActionHoldPolicy`,
13. how reward is split between simulation facts and experiment shaping using
    the fact/shaping criterion from the architecture baseline,
14. how `terminated` and `truncated` reasons are attributed to simulation,
    policy, or orchestration sources,
15. which side owns authoritative episode phase and which side only mirrors it
    for Gymnasium, batch, replay, or CI APIs,
16. how scripted, learned, and human coordination directors inject tasking or
    command intent without mutating raw ECS state,
17. which `merge_policy` each cross-layer producer uses,
18. which scheduling-window injection semantics each action or coordination
    path expects,
19. which observation schema changes are minor-compatible versus
    major-incompatible.

The expected output is a freeze document, not implementation.

Architecture closure note:

- The architecture framework is closed at the simulation/policy/orchestration
  layer boundary.
- Remaining `B`-level contract semantic details should patch the architecture
  baseline directly.
- `C`-level implementation alignment should be tracked as task plans.
- `D`-level internal design blanks, such as policy-layer internals or
  orchestration-layer internals, should become separate architecture docs and
  should not reopen the simulation-layer framework.

## WP3 Engagement Pilot

Output:

- [WP3 engagement pilot task family](wp3_engagement_pilot/engagement_pilot_wp3_20260519.md)

The first implementation pilot should be the engagement lifecycle because it
crosses the largest number of architecture boundaries and naturally uses
multiple clock domains:

`tasking -> command delivery -> sensor/track -> fire control -> launcher -> munition -> seeker/guidance/fuze -> effects -> damage -> observation`

The pilot must involve at least two platform families, such as:

- aircraft pylon launch,
- naval mount launch.

The pilot should avoid creating separate `air weapon` and `naval weapon`
runtime paths. Differences should appear in launcher, munition, seeker,
guidance, fuze, effects, doctrine families, and clock-domain policies.

The first implementation wave should be split into contract DTO scaffolding,
facade packet shells, Python binding exposure, air launch adapters, naval
launch adapters, munition/damage export, diagnostics trace, and a
stage-aligned non-RL smoke harness. Air and naval workers may run in parallel
only when they do not edit the same shared kernel file.

## WP4 Facade Alignment

Output:

- [WP4 facade alignment task family](wp4_facade_alignment/facade_alignment_wp4_20260519.md)

WP4 turns the accepted engagement pilot into the maintained frontend shape. It
should reference WP2.5 for scheduler semantics and Temp-02 for the
information/agency boundary:

- `ObservationPacket` is what the agent is allowed to see.
- `DecisionBelief` is what the agent thinks is true after inference, memory,
  doctrine, or learned state.
- `AgentRole` is role plus authority plus information-state source plus
  decision-model reference plus action interface.

WP4 should not create new simulation semantics. It should make existing
behavior reachable through facade-shaped APIs or documented compatibility
adapters.

WP4 dispatch clusters:

- `WP4-A Surface Inventory` first:
  [surface inventory cluster](wp4_facade_alignment/wp4_surface_inventory_cluster_20260519.md).
- `WP4-B/C Engagement, Step, And Lifecycle Alignment` after the initial surface
  vocabulary is stable:
  [engagement/step cluster](wp4_facade_alignment/wp4_engagement_step_cluster_20260519.md).
- `WP4-D/E Policy, AgentRole, And Python Mirror` after action, coordination,
  observation, belief, and agent-role names are stable:
  [policy/binding cluster](wp4_facade_alignment/wp4_policy_binding_cluster_20260519.md).
- `WP4-F Integration And Docs` remains serial in the main thread or a dedicated
  integration worker after the clusters return.

`WP4-A`, `WP4-C`, and `WP4-D` are the highest-reasoning streams because they
touch cross-layer semantics, belief boundaries, or adapter ownership.

WP4 first-wave outputs are accepted as discovery inputs:

- [WP4 first-wave acceptance review](../review/wp4_first_wave_acceptance_review_20260519.md)
- [WP4-A surface inventory draft](wp4_facade_alignment/wp4_surface_inventory_wp4a_20260519.md)
- [WP4-B/C engagement-step alignment notes](wp4_facade_alignment/wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding alignment notes](wp4_facade_alignment/wp4_policy_binding_alignment_notes_20260519.md)

WP4 second-wave clusters:

- `WP4-G Facade Evidence Gates`:
  [facade evidence cluster](wp4_facade_alignment/wp4_facade_evidence_cluster_20260519.md).
- `WP4-H Information And Agent Shim`:
  [agent shim cluster](wp4_facade_alignment/wp4_agent_shim_cluster_20260519.md).
- `WP4-I Compatibility Guard And Integration`:
  [compat guard cluster](wp4_facade_alignment/wp4_compat_guard_cluster_20260519.md).

WP4 second-wave and integration outputs:

- [WP4 second-wave acceptance review](../review/wp4_second_wave_acceptance_review_20260519.md)
- [WP4-I compatibility guard notes](wp4_facade_alignment/wp4_compat_guard_notes_20260519.md)
- [WP4-F integration handoff](wp4_facade_alignment/wp4_integration_handoff_20260519.md)
- [WP4 final acceptance review](../review/wp4_facade_alignment_acceptance_review_20260519.md)

## WP5 Validation Harness

Output:

- [WP5 validation harness task family](wp5_validation_harness/validation_harness_wp5_20260519.md)

WP5 converts the architecture and facade work into maintained evidence. The
harness should cover five validation tiers:

- design conformance,
- trace conformance,
- boundary conformance,
- information/belief leakage,
- replay/evidence conformance.

WP5 starts from the accepted WP4 facade labels. It should not start from raw
runtime inspection; the point is to prove that facade-shaped artifacts,
diagnostics, and replay metadata are enough to validate the shared architecture.

WP5 first-wave clusters:

- `WP5-A Harness Inventory`:
  [harness inventory cluster](wp5_validation_harness/wp5_harness_inventory_cluster_20260519.md).
- `WP5-B Design And Boundary Gates`:
  [design/boundary cluster](wp5_validation_harness/wp5_design_boundary_cluster_20260519.md).
- `WP5-C Trace And Replay Gates`:
  [trace/replay cluster](wp5_validation_harness/wp5_trace_replay_cluster_20260519.md).

`WP5-C` is the highest-reasoning first-wave stream because trace ancestry and
replay metadata tests can become brittle if they assume runtime metadata that
WP4 explicitly deferred.

WP5 first-wave outputs are accepted:

- [WP5 first-wave acceptance review](../review/wp5_first_wave_acceptance_review_20260519.md)
- [WP5-A harness inventory notes](wp5_validation_harness/wp5_harness_inventory_notes_20260519.md)
- [WP5-B design/boundary notes](wp5_validation_harness/wp5_design_boundary_notes_20260519.md)
- [WP5-C trace/replay gates notes](wp5_validation_harness/wp5_trace_replay_gates_notes_20260519.md)

WP5 second-wave clusters:

- `WP5-D Information And Belief Gates`:
  [information/belief cluster](wp5_validation_harness/wp5_information_belief_cluster_20260519.md).
- `WP5-E Smoke Promotion And Docs`:
  [smoke promotion cluster](wp5_validation_harness/wp5_smoke_promotion_cluster_20260519.md).

WP5 second-wave and final outputs are accepted:

- [WP5-D information/belief acceptance review](../review/wp5_information_belief_acceptance_review_20260519.md)
- [WP5-D information/belief notes](wp5_validation_harness/wp5_information_belief_notes_20260519.md)
- [WP5-E smoke promotion notes](wp5_validation_harness/wp5_smoke_promotion_notes_20260519.md)
- [WP5 validation harness acceptance review](../review/wp5_validation_harness_acceptance_review_20260519.md)

## WP6 Backend Profile Policy

Output:

- [WP6 backend profile policy](wp6_backend_profile_policy/backend_profile_policy_wp6_20260519.md)
- [WP6-A backend profile taxonomy cluster](wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.md)
- [WP6-A backend profile registry](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md)
- [WP6-B parity budget cluster](wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.md)
- [WP6-B parity budget registry](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md)
- [WP6-C + WP6-D integration and index sync](wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.md)
- [WP6-C1 resident-state boundary rules](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
- [WP6 backend profile policy acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md)

WP6 closes the backend profile and parity-budget gap behind contracts. It
names the profile vocabulary, budget records, resident-state boundaries, and
capability projection rules that accelerated, resident-state, approximate, and
diagnostics-only paths must obey before those paths can be treated as
maintained.

WP6 workstream map:

- `WP6-A Backend Profile Taxonomy`:
  [taxonomy cluster](wp6_backend_profile_policy/wp6_backend_profile_taxonomy_cluster_20260519.md) and
  [profile registry](wp6_backend_profile_policy/wp6_backend_profile_registry_20260519.md).
- `WP6-B Parity Budget And Comparison Rules`:
  [parity budget cluster](wp6_backend_profile_policy/wp6_parity_budget_cluster_20260519.md) and
  [parity budget registry](wp6_backend_profile_policy/wp6_parity_budget_registry_20260519.md).
- `WP6-C Resident-State And Backend Capability Alignment`:
  [resident-state boundary rules](wp6_backend_profile_policy/wp6_resident_state_boundary_rules_20260519.md)
  plus capability-projection guards in
  [runtime facade layering tests](../../../tests/architecture/test_runtime_facade_layering.py),
  [runtime facade tests](../../../tests/runtime/facade/test_runtime_facade.py),
  and [GPU runtime binding tests](../../../tests/test_gpu_runtime_bindings.py).
- `WP6-D Integration And Index Sync`:
  [integration and index sync](wp6_backend_profile_policy/wp6_integration_and_index_sync_20260519.md) and
  [acceptance review](../review/wp6_backend_profile_policy_acceptance_review_20260519.md).

## WP7 Backend Capability Materialization

Output:

- [WP7 backend capability materialization](wp7_backend_capability_materialization/backend_capability_materialization_wp7_20260519.md)
- [WP7-A registry materialization cluster](wp7_backend_capability_materialization/wp7_registry_materialization_cluster_20260519.md)
- [WP7-A registry materialization notes](wp7_backend_capability_materialization/wp7_registry_materialization_notes_20260519.md)
- [WP7-B runtime capability projection cluster](wp7_backend_capability_materialization/wp7_runtime_capability_projection_cluster_20260519.md)
- [WP7-B runtime capability projection notes](wp7_backend_capability_materialization/wp7_runtime_capability_projection_notes_20260519.md)
- [WP7-C promotion evidence gates cluster](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_cluster_20260519.md)
- [WP7-C promotion evidence gates notes](wp7_backend_capability_materialization/wp7_promotion_evidence_gates_notes_20260519.md)
- [WP7-D multi-fidelity entry conditions cluster](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_cluster_20260519.md)
- [WP7-D multi-fidelity entry conditions notes](wp7_backend_capability_materialization/wp7_multifidelity_entry_conditions_notes_20260519.md)
- [WP7-E integration and index sync cluster](wp7_backend_capability_materialization/wp7_integration_and_index_sync_cluster_20260519.md)
- [WP7 backend capability materialization acceptance review](../review/wp7_backend_capability_materialization_acceptance_review_20260519.md)

WP7 is the accepted post-WP6 documentation and implementation-preparation line.
It turns accepted backend profile policy into materialized registry, runtime
projection, promotion evidence, and multi-fidelity entry conditions. This
acceptance does not promote exact GPU, resident-state, device observation,
shadow, or adaptive fidelity support; current support remains false until a
future promotion review updates the registry, parity budget, projection adapter,
and validation evidence together.

WP7 workstream map:

- `WP7-A Registry Materialization` starts first and owns the machine-checkable
  registry/schema shape.
- `WP7-D Multi-Fidelity Entry Conditions` may run beside WP7-A as long as it
  cites WP6/WP7-A profile vocabulary rather than inventing support claims.
- `WP7-B Runtime Capability Projection` waits for WP7-A and keeps projection
  conservative.
- `WP7-C Promotion Evidence Gates` consumes WP7-A/D and maps candidate
  promotion to WP5 validation tiers.
- `WP7-E Integration And Index Sync` is serial and should run after A-D
  stabilize.

## Acceptance Gates

Every implementation task derived from this subproject should satisfy:

1. stage ownership is documented,
2. stage-node read/write sets and clock domains are documented,
3. feedback crosses state-store or event-queue boundaries,
4. facade or compatibility-adapter access is explicit,
5. CPU exact behavior remains the reference path,
6. cross-domain behavior uses the same lifecycle,
7. local smoke tests run without requiring RL dependencies,
8. diagnostics can explain command, launch, munition, effect, and damage events,
9. observation schema, action validity, reward composition,
   termination/truncation source, and episode lifecycle authority are assigned
   to explicit layers.
10. maintained decision paths consume `ObservationPacket` or declared
    `DecisionBelief`, not `World Truth`.
11. backend capability claims cite a maintained backend profile and parity
    budget; `RuntimeCapabilities` must not infer exact GPU, resident-state, or
    shadow support from helper/probe presence alone.
12. WP7 capability materialization keeps exact GPU, resident-state, device
    observation, shadow, and multi-fidelity support false unless a maintained
    profile revision, parity budget, ownership/sync policy, and validation gate
    explicitly promote the claim.
13. WP8 learning-face outputs keep curriculum, evaluation, capability
    profiling, scenario generation, and learning evidence explicit and
    replayable rather than turning them into a second simulation truth path.

## Non-Goals

- Full RL training on the local Windows machine.
- Immediate exact GPU world-step replacement.
- Introducing Rust as a near-term backend.
- Rewriting all existing command/tasking DTOs before the contract freeze.
- Moving every existing file into new directories during WP0/WP1.
