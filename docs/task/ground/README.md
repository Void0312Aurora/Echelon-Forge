# Ground

Status: active planning entry opened on `2026-05-21`; current progress tracking
updated on `2026-05-26`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject is the planning entry for the repository's current early
ground specialization bootstrap. It extends the shared simulation lifecycle
without creating a new vertical runtime path.

## Current Status

- The latest state summary is
  [ground_current_progress_20260524.md](ground_current_progress_20260524.md).
- `services/army` already exists as the authoritative service-profile boundary.
- The task tree now maintains a dedicated ground execution-specialization lane:
  G0-G4 tasking lifecycle evidence and G6-E native schema evidence are
  accepted, while movement, sensing, terrain, fires, damage, combat, and full
  ground runtime behavior remain held.
- G0 now freezes `ground` as the maintained specialization name, `platoon` as
  the first tight-loop tactical unit, and `move / occupy / support` as the first
  task family default.
- `army` and `land` are accepted aliases that normalize to `ground`; navigation
  routes through `services/army` plus `ground/`, not a new `army` runtime stack.
- The workline is split into G0-G6 phases so subagents can take bounded,
  non-overlapping tasks.
- G0 is accepted by main-thread G0-D.
- G1 accepted a narrow Python-profile-only slice: `army`, `ground`, `land`, and
  `ServiceProfile.Army` normalize to `ground`; C++ DTO shells, bindings,
  runtime behavior, and scenario loaders remain held.
- G2 accepted the first ground content/test seed: a non-auto-loaded
  `ground_platoon_starter.seed` under `examples/config/database/ground/units/`
  and three runnable `tests/contracts/unit/ground/` common-core contracts.
- G3 accepted one safe G4 candidate:
  `tasking-only lifecycle proof through normalized ground TaskOrder ->
  LeaderIntent -> PilotReport status shell`.
- G4 accepted that bounded slice and is now sealed as the tasking lifecycle
  baseline.
- G5 accepts the first canonical MVP scenario shell under `scenarios/ground/`
  and keeps command delivery, observation/export, movement, sensing, terrain,
  fires, and broad facade work held.
- G6 opens the first realism-gradient MVP scenario batch. G6-A records the
  gradient decision, and G6-B adds two G1 compatibility-shell fixtures:
  `ground_platoon_static_occupy_v1` and
  `ground_platoon_support_relationship_v1`.
- G6-C accepts route-move boundary guardrails: unknown explicit profile hints
  now fail closed, current ground scenarios must stay G0/G1, and `G2` route
  movement remains held until a later movement-release vote accepts native
  schema-backed movement evidence or an equivalent compatibility boundary.
- G6-D opens the route-move release decision and selects the schema-first path:
  the first `G2` route-move scenario must wait for native ground schema
  evidence plus a later movement-release vote. The current `Aircraft`
  compatibility shell remains G0/G1 only.
- G6-D1/D2 preflight returned `preflight-only`: at that time the native
  `Ground` unit type/schema blocker was still open. G6-E2/E3 later closed
  schema identity only; movement evidence still requires a separate release
  vote.
- G6-E0 opens the native ground platform schema planning package. It defines
  the minimum implementation surface and evidence gates for a loadable/spawnable
  native ground entity, but it does not release route movement or runtime
  movement behavior.
- G6-E1 source-inventory/design preflight selects `UnitType::Ground`,
  `type = "Ground"`, `Ground_Platoon_MVP`, and the existing type-name/default
  factory materialization path for the first native schema implementation.
- G6-E2/E3 accept the first native ground platform schema: the example
  database now loads `Ground_Platoon_MVP`, Python exposes `ef_py.UnitType.Ground`,
  and `spawn_unit(..., "Ground_Platoon_MVP", ...)` materializes a native ground
  entity with stable position, velocity, heading, instrument, and health
  inspection. This is schema evidence only; route movement, terrain, sensing,
  fires, damage, and combat remain held.

## Recommended Reading Order

- Current progress tracking:
  [ground_current_progress_20260524.md](ground_current_progress_20260524.md)
- Primary plan:
  [ground_domain_bootstrap_plan_20260521.md](ground_domain_bootstrap_plan_20260521.md)
- Subagent dispatch:
  [ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md)
- G0:
  [g0_boundary_freeze/README.md](g0_boundary_freeze/README.md)
- G1:
  [g1_contract_skeleton/README.md](g1_contract_skeleton/README.md)
- G2:
  [g2_content_test_seed/README.md](g2_content_test_seed/README.md)
- G3:
  [g3_execution_surface_design/README.md](g3_execution_surface_design/README.md)
- G4:
  [g4_runtime_slice/README.md](g4_runtime_slice/README.md)
- G5:
  [g5_mvp_scenario/README.md](g5_mvp_scenario/README.md)
- G6:
  [g6_realism_gradient_mvp_scenarios/README.md](g6_realism_gradient_mvp_scenarios/README.md)
- G6-C:
  [g6_route_move_boundary/README.md](g6_route_move_boundary/README.md)
- G6-D:
  [g6_route_move_release_decision/README.md](g6_route_move_release_decision/README.md)
- G6-E:
  [g6_native_ground_platform_schema/README.md](g6_native_ground_platform_schema/README.md)
- Review:
  [../review/ground_domain_bootstrap_plan_review_20260521.md](../review/ground_domain_bootstrap_plan_review_20260521.md)
- Architecture baseline:
  [../../plan/architecture/simulation_system_architecture_design.md](../../plan/architecture/simulation_system_architecture_design.md)
- Army service profile:
  [../../standards/services/army.md](../../standards/services/army.md)
- Ground standards overview:
  [../../standards/ground/README.md](../../standards/ground/README.md)
- Ground minimal task structure:
  [../../standards/ground/minimal_task_structure.md](../../standards/ground/minimal_task_structure.md)
- Common/air/naval split carry-over:
  [../common_air_naval/README.md](../common_air_naval/README.md)

## Sealed Baseline

G0-G4 are now sealed as the accepted baseline for ground tasking:

- `ground` / `army` / `land` profile recognition and starter common-core
  defaults
- non-runtime ground content seed and focused ground unit contracts
- selected execution-surface decision: tasking-only lifecycle proof
- maintained runtime bridge through normalized `TaskOrder -> LeaderIntent ->
  PilotReport`

## Current Follow-On Focus

- maintain G0/G5 tasking smoke and G6 G1 static occupy/support fixtures as
  realism-gradient guardrails
- keep G6-C/G6-D route-move guardrails active before adding any movement
  scenario
- use the accepted G6-E2/E3 native schema evidence as input to a later
  route-move release vote
- keep G1 scenarios scoped to static occupy/support relationship semantics only
- keep command delivery, observation/export, movement, sensing, terrain, fires,
  effects, damage, and broad `MissionCommand` growth held
- use the subagent queue for all delegated work
