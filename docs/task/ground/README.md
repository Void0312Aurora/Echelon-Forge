# Ground

Status: active planning entry opened on `2026-05-21`; G0-G4 are sealed as the
accepted ground baseline. G5 is open for the first minimal MVP scenario shell.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This subproject is the planning entry for the repository's third domain
bootstrap: a future ground specialization that should extend the shared
simulation lifecycle without creating a new vertical runtime path.

## Current Status

- `services/army` already exists as the authoritative service-profile boundary.
- The task tree now maintains a dedicated ground execution-specialization lane;
  runtime execution remains deferred.
- G0 now freezes `ground` as the maintained specialization name, `platoon` as
  the first tight-loop tactical unit, and `move / occupy / support` as the first
  task family default.
- `army` and `land` are accepted aliases that normalize to `ground`; navigation
  routes through `services/army` plus `ground/`, not a new `army` runtime stack.
- The workline is split into G0-G5 phases so subagents can take bounded,
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
- G5 opens the first canonical MVP scenario under `scenarios/ground/` and keeps
  command delivery, observation/export, movement, sensing, terrain, fires, and
  broad facade work held.

## Recommended Reading Order

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

- build the G5 MVP scenario shell as the first canonical `scenarios/ground/`
  fixture
- keep the scenario scoped to tasking status-chain validation only
- keep command delivery, observation/export, movement, sensing, terrain, fires,
  effects, damage, and broad `MissionCommand` growth held
- use the subagent queue for all delegated work
