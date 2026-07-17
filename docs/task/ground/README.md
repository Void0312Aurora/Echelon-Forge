# Ground

Status: active follow-on entry; bootstrap planning baseline plus the
environment-substrate G0 design/implementation line accepted and closed through
G0-M on `2026-06-06`; current progress tracking updated on `2026-06-06`.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject is the planning entry for the repository's current early
ground specialization bootstrap. It extends the shared simulation lifecycle
without creating a new vertical runtime path.

## Current Status

- The latest state summary is
  [ground_current_progress_20260524.md](ground_current_progress_20260524.md).
- Accepted environment-substrate G0 design/implementation line:
  [environment_substrate_g0_architecture/README.md](environment_substrate_g0_architecture/README.md).
  This package treats G0 as the shared environment-substrate design and
  implementation lane. Current accepted substages include architecture/design
  records, the G0-J static manifest contract, the G0-K generator/catalog
  contract, the G0-L projection setup plus compiler-ingestion contract, and
  G0-M metadata-only derived products; they do not release runtime setup
  application, movement, LOS, cover, fires, damage, or combat.
- Accepted environment-substrate G0-J static manifest contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md).
  This substage adds shared static manifest data structures, registries,
  validators, a deterministic fixture, and contract-level projection tests under
  `python/scenario/environment_substrate/`; it does not release generator or
  runtime behavior.
- Accepted environment-substrate G0-K generator/catalog contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md).
  This substage adds deterministic request/tile/seed/provenance rules, catalog
  descriptors/admission, and an in-memory generated manifest fixture under
  `python/scenario/environment_substrate/`; it does not release runtime
  projection or generated scenario artifacts.
- Accepted environment-substrate G0-L projection setup payload contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md).
  This substage adds Python-only inert setup payload/evidence conversion for
  already validated `world_zone_definition` projections.
- Accepted environment-substrate G0-L-F scenario compiler ingestion:
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md).
  This substage ingests accepted projection setup payloads into merged
  `environment.zones` before layout metadata compilation; it does not apply
  runtime setup.
- Accepted environment-substrate G0-M metadata-only derived products:
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md).
  This substage adds `surface_zone_index` and `occlusion_candidate_index`
  contract products only; it does not release movement, LOS, cover, fires,
  damage, combat, or runtime consumers.
- Environment-substrate G0 closure:
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md).
- The original bootstrap plan met its planning-lane success criteria and is now
  an accepted archived baseline, not an active dispatch surface.
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
  `ServiceProfile.Army` normalize to `ground`. That G1 slice held C++ DTO
  shells, bindings, runtime behavior, and scenario loaders; the later
  `2026-06-05` infrastructure update only adds static G0/G1 owner-slice DTOs
  and bindings, without releasing runtime behavior.
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
- The first C++ ground static owner-slice infrastructure has landed under
  `src/components/domains/ground/tasking/` and `src/components/domains/ground/command/`. It
  exposes G0/G1 static task/status metadata through existing compatibility
  shells, maintained batch contracts, JSON round-trip, and Python bindings. It
  does not release route movement, terrain, sensing, fires, damage, or combat.
- The ground profile now authors G0/G1 static `MissionCommandGround` fields from
  ground task/status metadata. This is command-authoring independence for static
  tasking, not an independent ground movement or combat runtime.

## Current Entry Points

- Current progress tracking:
  [ground_current_progress_20260524.md](ground_current_progress_20260524.md)
- Accepted environment-substrate G0 architecture package:
  [environment_substrate_g0_architecture/README.md](environment_substrate_g0_architecture/README.md)
- Accepted environment-substrate G0-J static manifest contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md)
- Accepted environment-substrate G0-K generator/catalog contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md)
- G0-K acceptance:
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_acceptance_20260606.md)
- Accepted environment-substrate G0-L projection setup payload contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md)
- Accepted environment-substrate G0-L-F scenario compiler ingestion:
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md)
- Accepted environment-substrate G0-M metadata-only derived products:
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md)
- Environment-substrate G0 closure:
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md)
- Environment-substrate G0-L projection preflight and task map:
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_preflight_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_preflight_20260606.md)
- Terrain system G0 architecture design:
  [environment_substrate_g0_architecture/environment_substrate_g0_terrain_system_architecture_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_terrain_system_architecture_20260605.md)
- Accepted bootstrap baseline:
  [archive/ground_domain_bootstrap_plan_20260521.md](archive/ground_domain_bootstrap_plan_20260521.md)
- Subagent dispatch:
  [ground_subagent_dispatch_queue_20260521.md](ground_subagent_dispatch_queue_20260521.md)
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
- Common/air/naval split (archived):
  [../archive/common_air_naval/common_air_naval_modular_split_plan_20260515.md](../archive/common_air_naval/common_air_naval_modular_split_plan_20260515.md)

## Sealed / Archived Subproject Records

These subproject directories are accepted evidence records, not active dispatch
surfaces. Their original paths now contain lightweight work statements, while
the full packets live in [archive/README.md](archive/README.md). They remain
linked from this index because current movement-release planning still consumes
their gates, but new work should open a fresh follow-on package instead of
editing these accepted records in place.

- Ground bootstrap plan:
  [archive/ground_domain_bootstrap_plan_20260521.md](archive/ground_domain_bootstrap_plan_20260521.md)
- G0 boundary freeze:
  [g0_boundary_freeze/README.md](archive/g0_boundary_freeze/README.md)
- G1 contract skeleton:
  [g1_contract_skeleton/README.md](archive/g1_contract_skeleton/README.md)
- G2 content/test seed:
  [g2_content_test_seed/README.md](archive/g2_content_test_seed/README.md)
- G3 execution-surface design:
  [archive/g3_execution_surface_design/README.md](archive/g3_execution_surface_design/README.md)
- G4 tasking runtime slice:
  [archive/g4_runtime_slice/README.md](archive/g4_runtime_slice/README.md)
- G5 MVP scenario shell:
  [archive/g5_mvp_scenario/README.md](archive/g5_mvp_scenario/README.md)
- G6 realism-gradient static fixtures:
  [archive/g6_realism_gradient_mvp_scenarios/README.md](archive/g6_realism_gradient_mvp_scenarios/README.md)
- G6-C route-move boundary guardrails:
  [archive/g6_route_move_boundary/README.md](archive/g6_route_move_boundary/README.md)
- G6-D route-move release decision:
  [archive/g6_route_move_release_decision/README.md](archive/g6_route_move_release_decision/README.md)
- G6-E native ground platform schema evidence:
  [archive/g6_native_ground_platform_schema/README.md](archive/g6_native_ground_platform_schema/README.md)
- Environment substrate G0 architecture:
  [environment_substrate_g0_architecture/README.md](environment_substrate_g0_architecture/README.md)
- Environment substrate G0-J static manifest contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_static_manifest_contract_20260605.md)
- Environment substrate G0-K generator/catalog contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md](environment_substrate_g0_architecture/environment_substrate_g0_generator_catalog_20260605.md)
- Environment substrate G0-L projection setup payload contract:
  [environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_projection_setup_acceptance_20260606.md)
- Environment substrate G0-L-F scenario compiler ingestion:
  [environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_scenario_ingestion_acceptance_20260606.md)
- Environment substrate G0-M metadata-only derived products:
  [environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_derived_products_acceptance_20260606.md)
- Environment substrate G0 closure:
  [environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md](environment_substrate_g0_architecture/environment_substrate_g0_closure_acceptance_20260606.md)

## Sealed Baseline

G0-G4 are now sealed as the accepted baseline for ground tasking:

- `ground` / `army` / `land` profile recognition and starter common-core
  defaults
- non-runtime ground content seed and focused ground unit contracts
- selected execution-surface decision: tasking-only lifecycle proof
- maintained runtime bridge through normalized `TaskOrder -> LeaderIntent ->
  PilotReport`

## Current Follow-On Focus

- treat accepted G0-K as the Python request/tile/catalog contract and in-memory
  fixture baseline for projection work
- treat accepted G0-L as payload/evidence conversion plus strict scenario
  compiler data ingestion; runtime setup application still needs a separate
  release package
- treat accepted G0-M as metadata-only derived-product contracts; runtime
  consumers and movement/LOS/cover behavior still need separate release packages
- keep terrain as the first detailed branch inside the shared environment root,
  alongside atmosphere/weather, wind, illumination, maritime/ocean, hydrology,
  and dynamic environment branches
- keep the accepted G0-J implementation manifest-first: current C++/Python terrain
  setup remains compatibility/query surface, and the new Python package is the
  shared `environment_substrate` contract namespace
- maintain G0/G5 tasking smoke and G6 G1 static occupy/support fixtures as
  realism-gradient guardrails
- keep G6-C/G6-D route-move guardrails in force before adding any movement
  scenario, without reopening those accepted records
- use the accepted G6-E2/E3 native schema evidence as input to a later
  route-move release vote
- keep G1 scenarios scoped to static occupy/support relationship semantics only
- keep observation/export, movement, sensing, terrain, fires, effects, damage,
  combat, and broad `MissionCommand` growth held; the current
  `MissionCommandGround` path is only static task metadata authoring
- use the subagent queue for all delegated work
