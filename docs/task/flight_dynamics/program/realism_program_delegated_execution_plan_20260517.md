<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/realism_program_delegated_execution_plan_20260517.zh.md. Review before treating this file as authoritative. -->

# Main Line Delegation Execution Plan for Realism

Status: `2026-05-17` main thread convergence version.

Related documents:

- [Current Status of the Realism Main Line and Associated Subprojects](realism_program_current_status_20260517.zh.md)
- [Realism P1 Task Overview Table](realism_program_p1_taskboard_20260517.zh.md)
- [Code Quality Review](code_quality_review_realism_wave_20260517.zh.md)
- [Flight Dynamics P1 Implementation Package](../flight/flight_dynamics_realism_p1_implementation_package_20260517.zh.md)
- [Sensor/Situational Awareness P1 Implementation Package](../sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md)
- [Weapon/Guidance P1 Implementation Package](../weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)
- [C2 Command Chain Problem Analysis](../c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)

Purpose of this document:

- Converge the directional documents already formed for `flight / sensor_situation / weapon_guidance / c2_command_chain / naval` into a main line plan that can be delegated for execution.
- Clarify which tasks must first be closed off by the main thread, and which tasks are suitable for parallel advancement by subagents/workers.
- Provide a unified `lane`, dependency matrix, and stage acceptance order for the next round of implementation, avoiding a return to each discipline working in isolation.

Supplementary scope:

1. The overall current stage and main-blocker judgment should prioritize
   [Realism Main Line Convergence Plan](realism_program_convergence_plan_20260517.zh.md)
   and
   [Current Status of the Realism Main Line and Associated Subprojects](realism_program_current_status_20260517.zh.md).
2. This document is better suited as an execution document for "how to distribute/converge lanes", rather than solely bearing the responsibility of the latest overall stage description.

---

## 0. Round Achieved Results

As of `2026-05-17`, the main thread has, through two batches of delegation, reclaimed the first round of shared integration closure, and completed main thread recompilation and integration acceptance.

### 0.1 Batch 1 Implemented

1. `Lane A / A1`:
   - `AeroTuning / EngineTuning / StallState / Sensor defaults / MissileTuningDefinition` have been added to `UnitDefinition / loader / factory`
2. `Lane B / B2`:
   - `Propulsion` has become the unified source of truth for `Force / Logistics / Instrument / Observation`
3. `Lane C / C3`:
   - The missile shared launch runtime has entered the formal launch chain, no longer relying solely on guidance lazy init
4. `Lane D / D1`:
   - Naval `screen-hold` has been supplemented with direct-recovery -> hold handoff closure

### 0.2 Batch 2 Implemented

1. `Lane D / MissionCommand contract`:
   - `bridge.py` has closed off profile routing
   - `naval_profile.py` has supplemented key naval/recovery/formation/helo field authoring
   - Runtime / batch roundtrip tests have been added
2. `Lane D / DataLink QoS`:
   - Stronger regression tests for budget scaling / fanout / churn / counter reset have been added
3. `Lane C / weapon launch plumbing`:
   - The minimal fact chain `definition -> default_loadout -> selected station -> fire_missile()` is now operational
   - `debug_get_missile_runtime_state()` has added key fields for quality, sensor, and guidance
4. `Lane B / propulsion tests`:
   - Homologous contract tests for `Propulsion -> Instrument / Logistics / Observation` have been added

### 0.3 Main Thread Completed Acceptance

1. `cmake --build build-workshop --target ef_core -j4` currently passes
2. `cmake --build build --target ef_py -j4` and
   `cmake --build build-workshop --target ef_py -j4` currently pass
3. Unified main thread acceptance currently shows:
   - `80 passed, 2 subtests passed`
4. The only remaining red flag at the time of planning
   - [tests/runtime/test_air_combat_1v1_fixture.py](../../../../tests/runtime/test_air_combat_1v1_fixture.py)
   - `test_loader_fixture_exposes_hostile_contact_and_weapon_state`
5. The above red flag has been confirmed and closed by the main thread:
   - Root cause: the fixture stopped prematurely upon first seeing a raw contact, directly asserting a `Tentative / Unknown` contact as a hostile confirmed track
   - Currently, the fixture wait condition has been corrected per confirmed hostile track semantics
6. This round's `Lane A` small cuts have been reclaimed:
   - Deduplication of `sensor` default value source
   - Deduplication of missile `Vec3 -> Math::Vector3`
7. This round's main thread added regression tests for structural closure:
   - `tests/runtime/test_sensor_situation_realism_p0.py`
   - `tests/runtime/test_kernel_observation_sanity.py`
   - `tests/runtime/test_weapon_guidance_realism_guards.py`
   - `tests/runtime/test_air_combat_1v1_fire_missile.py`
   - `tests/architecture/test_runtime_facade_layering.py`
   - Current result: `47 passed`
8. This round's new lane closure regression:
   - `tests/architecture/test_runtime_facade_layering.py`
   - `tests/world_batch/test_world_batch_vec_env.py`
   - `tests/runtime/test_command_link_qos.py`
   - `tests/runtime/test_mission_command_roe_fields.py`
   - `tests/runtime/test_flight_dynamics_tuning_runtime.py`
   - Current result: `51 passed`
9. This round's `Lane B/C/D` actual incremental closure:
   - `Lane B`: `aerodynamics_system.h` has landed stateful stall memory, and the tuned runtime test is locked
   - `Lane C`: `launch envelope enforcement` has been placed before ammo/cooldown/VLS/munition consumption
   - `Lane D`: ROE/authority/assigned-target/authorization fields of `MissionCommand` are locked by `CommandLink QoS` contract tests

---

## 1. Overall Assessment

The current realism main line is no longer suitable for completely parallel advancement along the five lines: "flight dynamics / sensor / weapon / naval warfare / C2".

Supplementary stage judgment:

1. The main line overall is still in `P1-A integration wrap-up`.
2. The key gatekeeping surfaces for `flight`, `sensor`, `naval`, and `C2` are largely closed; they are now better suited for maintenance mode.
3. The current main line focus has shifted from "fixing basic red flags" to "structural debt reduction and limited deeper modeling".
4. Therefore, the focus of this plan should change from "continue expanding more lanes" to "first converge, then parallelize under constraints."

The reason is not that these directions are unimportant, but that they already share three high-overlap prerequisite surfaces:

1. `schema -> loader -> factory` parameter injection chain
2. `runtime observation / Python binding / debug view` exposure surface
3. Shared semantic chain of `Detection -> Track -> Report -> MissionCommand / ROE / Weapon`

If deeper modeling is distributed before these shared prerequisite surfaces are closed, we will see:

1. Workers modifying the same `unit_definition / bindings / tests/runtime` simultaneously
2. Each direction expanding its own debug/observation interfaces, leading to increasingly divergent contracts
3. Upper-level `naval / air_combat / leader` scenarios continuing to build on drifting shared semantics

Therefore, the next round should adopt:

1. `Main thread first closes shared integration`
2. `Prioritize advancing weapon terminal realism and deeper modeling`
3. `Then proceed with limited parallel advancement per lane for deeper modeling`
4. `Naval` as a high-value scenario acceptance surface merged into the `C2/runtime` maintenance state, rather than an independent functional expansion main line.

---

## 2. What the Main Thread Should Do First

The following tasks should not be distributed to multiple implementation workers from the start; the main thread should first freeze the boundaries, determine the contracts, and define the writing set.

### 2.1 Shared Schema / Loader / Factory Closure

Coverage directions:

- flight: `AeroTuning / EngineTuning / StallState`
- sensor: new fields and defaults for `Sensor`
- weapon: `MissileTuning`, missile launch initialization parameters

Core file surfaces:

- [unit_definition.h](../../../../src/content/unit_definition.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)

Main thread goals:

1. Clarify the minimum set of fields for each line in `UnitDefinition`
2. Clarify the default value fallback strategy
3. Freeze "which tuning goes into the database and which remains in code defaults"

### 2.2 Shared Observation / Binding / Debug Contract Closure

Coverage directions:

- flight: debug view, runtime propulsion/stall values
- sensor: new fields for `Detection / Track / CommPacket`
- weapon: missile runtime debug/state view

Core file surfaces:

- [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp)
- [observation.h](../../../../src/core/interfaces/observation.h)

Main thread goals:

1. Freeze which fields go into the main observation
2. Which fields go only into debug/instrument/Python surface
3. Ensure runtime guards for each direction can be accepted with a unified observation surface

Supplementary judgment for this round:

1. `RuntimeFacade.runtime()` is currently not suitable for direct removal from C++ bindings
2. A more appropriate next step is to pull the raw runtime/world penetration back into an adapter on the Python side
3. `leader_world_batch_runtime.py` should be treated together with `world_batch_vec_env.py` as part of the same adapter closure task

### 2.3 Shared Runtime Semantics Closure

Coverage directions:

- sensor/weapon: `Detection -> Track -> Report`
- naval/C2: `MissionCommand -> behavior_runtime -> ship runtime`
- flight: propulsion state becomes the unified source of truth

The main thread needs to clarify:

1. `shared track != local contact` continues to be the primary contract
2. The primary semantics of `Track status / source / quality / classification / iff`
3. Which fields of `MissionCommand` require a roundtrip contract in the Python/C++ dual maintenance path
4. Whether `Propulsion` becomes the sole source of truth for thrust, fuel consumption, and instruments

---

## 3. Recommended Execution Lanes

The next round is recommended to be split into 4 lanes + 1 sidecar, where the main thread will no longer prioritize deep decomposition of `ScenarioLoader`.

Current frozen execution scope:

1. `ScenarioLoader` enters compatibility maintenance mode
   - Currently only accepts necessary fixes for blocking integration/regression
   - No longer treats continued decomposition of owners as a default main thread task
2. Main thread shifts to lane orchestration
   - Responsible for freezing the writing set, distributing tasks, collecting results, and performing integration acceptance
3. Parallel main lines become:
   - `Lane A sidecar`: `RuntimeFacade` adapter wrap-up
   - `Lane B`: Flight modeling deepening
   - `Lane C`: Weapon modeling deepening
   - `Lane D`: C2 / CommandLink modeling deepening

### 3.1 Lane A: Shared Contract / Integration

This is the highest priority lane for the entire main line.

Scope:

1. Schema / loader / factory wiring
2. Observation / binding / debug exposure
3. Runtime shared semantics and roundtrip contract
4. Infrastructure closure for realism runtime tests

Recommended tasks:

1. `A1 schema/factory integration`
   - `unit_definition.h`
   - `unit_definition_loader.cpp`
   - `default_unit_factory.h`
2. `A2 observation/binding integration`
   - `simulation_kernel_observation_api.cpp`
   - `bindings_core.cpp`
   - `bindings_command.cpp`
3. `A3 runtime semantic contracts`
   - `track_manager_system.h`
   - `data_link_system.h`
   - `simulation_kernel_weapon_api.cpp`
   - `mission_command_codec` / Python bridge
4. `A4 runtime test infrastructure`
   - `tests/runtime/*realism*`
   - `python/testing/runtime.py`

Low-risk subtasks already achieved this round:

1. `A1a sensor default source dedupe`
   - Unified to `unit_definition` / loader default baseline + factory preset override
2. `A1b missile math Vec3 dedupe`
   - Removed independent 3D vector type from `missile_guidance_math.h`
3. `A2a runtime facade adapter tightening`
   - `world_batch_vec_env.py` / `leader_world_batch_runtime.py` have already been pulled back into a single Python main line for raw world/runtime business penetration
   - `tests/architecture/test_runtime_facade_layering.py` has added layer guards
4. `A2b ScenarioLoader state-shell extraction`
   - `core.py` + `runtime_state.py` have formed the first phase state shell
   - The synchronization contract for execution episode state (route/mission/reward/runtime cache) has been leveled
5. `A2c ScenarioLoader scripted-opponent collaborator extraction`
   - build/reset/step owners have been sunk to `behavior_runtime/scripted_opponents.py`
   - `ScenarioLoader` retains a thin proxy and compatible access surface
   - Regression tests for scripted-opponent related runtime/world-batch have been added and are green
6. `A2c-2 ScenarioLoader command-chain owner extraction`
   - Runtime owners `_leader_phase_manager` and `_naval_screen_*` have been sunk to `behavior_runtime/command_chain_owner.py`
   - `command_chain.py` / `loading.py` now manage lifecycle through collaborator owner
   - `ScenarioLoader` still retains old property proxies, compatible with external bridge injection paths like `leader_env`
   - Targeted and extended regressions are green: `57 passed`
7. `A2c-3 ScenarioLoader behavior-phase owner extraction`
   - `post_waypoint_transition / mission_phase_name / _approach_prev_*` have been sunk to `behavior_runtime/behavior_phase_owner.py`
   - `runtime_state.py` has added unified mirroring view, maintaining roundtrip contract for execution episode state
   - `ScenarioLoader` continues to retain old property proxies and `_state_shell` compatible visibility
   - Related regressions are green: `57 passed`

Suggested `Lane A` subtasks for next round delegation:

1. `A2a-1 runtime facade adapter tightening` wrap-up
   - Continue compressing the usage surface of `batch_runtime` / raw runtime as maintenance interfaces
   - Keep `tests/architecture/test_runtime_facade_layering.py` as the gatekeeping line
2. `A2b-1 ScenarioLoader state-shell extraction` wrap-up
   - Keep `runtime_state.py` as the single synchronization surface for execution episode state
   - Avoid mission/route/post-transition/runtime cache from flowing back into `core.py`
3. `A2c-1 ScenarioLoader collaborator extraction` continue sinking
   - Behavior-phase owner first phase has landed
   - Next step: reduce load on `core.py` compat facade and deeper collaborator aspects, rather than repeating scripted-opponent / command-chain / behavior-phase first phase
   - Keep `gym_envs/scenario_loader/behavior_runtime/*` as the primary writing set

Acceptance tests:

1. [test_sensor_situation_realism_p0.py](../../../../tests/runtime/test_sensor_situation_realism_p0.py)
2. [test_kernel_observation_sanity.py](../../../../tests/runtime/test_kernel_observation_sanity.py)
3. [test_bindings_command_surface.py](../../../../tests/runtime/test_bindings_command_surface.py)
4. [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)
5. [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)

### 3.2 Lane B: Flight Dynamics

This lane will only formally expand after `Lane A` freezes the schema / binding / test contract.

Current frozen supplement:

1. `flight` is currently closer to the second half of `P1-A`; it is no longer a default blocking surface for the main thread.
2. `sensor/naval` have entered maintenance mode.
3. Only blocker fixes, contract closure, and shared-contract-related regressions are accepted.

Recommended splits:

1. `B1` data hookup chain
2. `B2` propulsion state as unified source of truth
3. `B3` Mach/compressibility and stall semantics deepening
4. `B4` debug/test closure
5. `B5` FBW/control law and high AoA recovery interface

Recommended file boundaries:

- [flight_dynamics_tuning.h](../../../../src/components/physics/flight_dynamics_tuning.h)
- [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- [aero_state_system.h](../../../../src/systems/physics/aero_state_system.h)
- [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h)
- [logistics_system.h](../../../../src/systems/systems/logistics_system.h)
- [instrument_system.h](../../../../src/systems/physics/instrument_system.h)
- [default_control_model.cpp](../../../../src/models/air/default_control_model.cpp)

Acceptance tests:

1. [test_flight_dynamics_p0_runtime_guards.py](../../../../tests/runtime/test_flight_dynamics_p0_runtime_guards.py)
2. [test_flight_dynamics_realism_guards.py](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)
3. [test_flight_dynamics_tuning_runtime.py](../../../../tests/runtime/test_flight_dynamics_tuning_runtime.py)

### 3.3 Lane C: Sensor + Weapon Modeling

This lane shares the same `Detection/Track/Report/Observation/Binding` backbone, so it is recommended to keep it under one program lane rather than splitting it completely.

Current freeze supplement:

1. `sensor` currently has been stabilized into a maintenance state.
2. `weapon` is still the most worthwhile deep direction to continue this round.
3. The first priority of `Lane C` is weapon terminal realism, truth shortcut tightening, and deeper modeling.

#### C1 Sensor Shared Integration Follow-up

Scope:

1. `Sensor` default values and database wiring
2. `Track status/source/quality/confidence` tightening
3. `DataLink` shared semantics stabilization

Core files:

- [sensor.h](../../../../src/components/systems/sensor.h)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [track_management.h](../../../../src/components/systems/track_management.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)

#### C2 Sensor Deeper Modeling

Scope:

1. More granular `M-of-N / quality / coast-drop`
2. `Radar + DataLink` minimal fusion
3. Conservative environment/clutter/sea clutter deepening

Acceptance tests:

1. [test_sensor_situation_realism_p0.py](../../../../tests/runtime/test_sensor_situation_realism_p0.py)
2. [test_naval_sensor_realism_runtime.py](../../../../tests/runtime/test_naval_sensor_realism_runtime.py)

#### C3 Weapon Shared Integration Follow-up

Scope:

1. `MissileTuning` shared API
2. Launch initialization and quality semantics wind-down
3. Missile runtime debug/state exposure
4. Guidance shared reference / observation unification

This round's supplemental freeze:

1. Completed cut only commits the pre-launch rejection contract for
   `min_launch_range_m / max_launch_off_boresight_deg / lobl_required`.
2. The current working tree also mixes in a larger batch of
   `definition-driven launch tuning / station-based launch selection / global tuning overlay`
   expansions; behavior regression is currently green, but they no longer belong to the "minimum envelope rejection firing".
3. Therefore, `Lane C` should not blindly add features in the next round, but should split
   `launch definition resolution / tuning overlay / runtime assembly`
   into clearer sub-responsibilities.

Core files:

- [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)
- [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)

#### C4 Weapon Deeper Modeling

Scope:

1. Seeker type differentiation
2. Midcourse / datalink / activation
3. 3DoF parameterization
4. Fuze / damage layering

Acceptance tests:

1. [test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)
2. [test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/test_air_combat_1v1_fire_missile.py)

Current freeze suggestion:

1. `C4` is not the default next cut in this round's main thread.
2. Before tightening the maintenance boundary of `sensor/naval`, it is not recommended to open a large parallel expansion of `midcourse / seeker type / fuze / damage`.

### 3.4 Lane D: C2 / Runtime Wind-down

The principle of this lane is:

1. First wind down `runtime/C2` main semantics
2. Incorporate `naval` as a high-value scenario acceptance surface
3. Defer deeper naval tasking / relay / jamming / authority transfer

Recommended order:

1. `D1 MissionCommand fields / codec / profile reconciliation`
2. `D2 DataLink QoS stress testing and budget scaling`
3. `D3 sensor/naval` shared semantics and maritime watchdog regression linkage review (maintenance state)
4. `D4 CommandLink minimal priority policy`
5. `D5 ROE / tasking minimal message closure prototype`

Supplementary notes:

1. `screen-hold` is no longer kept as a stable red dot.
2. `naval` is currently better suited as a high-value acceptance surface for `sensor/C2/runtime` rather than an independent entry point for expanding functionality.

Core files:

- [naval_screen.py](../../../../gym_envs/scenario_loader/behavior_runtime/naval_screen.py)
- [command_chain.py](../../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [mission_command.h](../../../../src/components/command/mission_command.h)
- [command_link_system.h](../../../../src/systems/systems/command_link_system.h)
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)
- Python `bridge/profile` and C++ `mission_command_codec`

Acceptance tests:

1. [test_naval_screen_scenario.py](../../../../tests/runtime/test_naval_screen_scenario.py)
2. [test_data_link_qos_runtime.py](../../../../tests/runtime/test_data_link_qos_runtime.py)
3. [test_command_link_qos.py](../../../../tests/runtime/test_command_link_qos.py)
4. [test_weapon_roe_runtime.py](../../../../tests/runtime/test_weapon_roe_runtime.py)

---

## IV. Recommended Delegation Approach

### 4.1 Tasks Suitable for Continued Delegation to Workers

The following tasks have relatively clear specs and are suitable for continued distribution via subagent/worker:

1. `weapon` truth shortcut / seeker reject / fuze-damage convergence
2. `MissionCommand` fields/codec/profile reconciliation and gap testing
3. `DataLink` stress testing, budget scaling, and counter testing
4. `RuntimeFacade / ScenarioLoader` compat surface offloading wind-down
5. `CommandLink` priority policy

### 4.2 Tasks More Suitable for Delegation to Explorer/Sidecar

The following tasks are more about reconciliation, stress testing gaps, and contract organization, suitable for explorer or sidecar workers:

1. `MissionCommand` field matrix and roundtrip contract
2. `DataLink` stress test design and budget scaling gap testing
3. Realism document wording review and phase acceptance matrix organization
4. Entry point and teardown risk inventory for realism watchdog tests in `tests/runtime`

### 4.3 Tasks Not Recommended for Immediate Large-Scale Parallelism

The following tasks currently have large overlap in scope and shared semantics not yet nailed down; it is not recommended to assign them to multiple implementation workers simultaneously:

1. Simultaneously modifying `unit_definition_loader.cpp` + `default_unit_factory.h` + `bindings_core.cpp`
2. Simultaneously modifying `track_manager_system.h` + `data_link_system.h` + `simulation_kernel_observation_api.cpp`
3. Parallel advancement of relay, jamming, naval tasking doctrine before the `shared contact/track` contract is stabilized
4. Parallel full-depth expansion of seeker type + fuze + damage before missile shared runtime state is finalized
5. Simultaneously reopening `flight` and `weapon` deepening before structural debt in `sensor/naval` is further tightened

---

## V. Phase Order

Recommended phase order:

### Phase 0: Main Thread Freeze Shared Boundaries

Deliverables:

1. Schema field scope
2. Observation/debug exposure scope
3. Shared runtime semantics wording
4. Minimal entry points for realism runtime tests

### Phase 1: Lane A One-Round Wind-down

Acceptance targets:

1. New fields and new states on the three lines `P0` can be consistently accessed from configuration, runtime, observation, and Python layers
2. Old tests no longer depend on old semantics
3. High-level scenarios like `naval` and `air_combat` use the same shared semantics

Current status update:

1. `A1a / A1b / A2a / A2b` have completed the first stage implementation and passed main thread regression acceptance
2. `A2c` first stage also implemented and passed main thread regression acceptance
3. `A2a` remaining work is mainly continued freezing of the adapter usage surface, not reopening raw runtime
4. `A2b/A2c` remaining work is mainly `RuntimeFacade` compat wind-down and `core.py` compat facade offloading, not pushing state logic back into `core.py`
5. Therefore, the next cut in `Phase 1` should focus on sinking the remaining collaborators of `ScenarioLoader`, rather than returning to earlier `A1`-type deduplication tasks

### Phase 2: Lane B / C / D Parallel Progress

Conditions:

1. `Lane A` has completed one round of shared integration
2. `sensor/naval` currently stabilized into maintenance state
3. Reality guards can run stably
4. DTO / observation / binding surfaces no longer drift frequently

### Phase 3: Re-evaluate Deeper Modeling

At this point, decide whether to enter:

1. Deeper Mach/compressibility / stall
2. Deeper Radar+DataLink fusion, environmental effects
3. Seeker type / midcourse / fuze layering
4. Deeper naval tasking / authority transfer

---

## VI. Suggested Initial Delegation Tickets

If continuing to distribute via subagent in the next round, it is recommended to open only the following initially:

1. `Worker Weapon-A`
   - Task: weapon truth shortcut / seeker reject / fuze-damage convergence
2. `Worker C2-A`
   - Task: `MissionCommand` fields / codec / profile reconciliation and gap testing
3. `Worker QoS-A`
   - Task: `DataLink` stress testing and budget scaling gap testing
4. `Worker Runtime-A`
   - Task: `RuntimeFacade / ScenarioLoader` compat surface offloading wind-down
5. `Explorer C2-B`
   - Task: `MissionCommand` fields/codec/profile reconciliation
6. `Explorer Docs-A`
   - Task: Realism document wording review and phase acceptance matrix organization

Tasks not recommended to open initially:

1. Parallel advancement of `relay + jamming + doctrine`
2. Full parallel deepening of `seeker type + fuze + damage`
3. `flight` and `weapon` as default main lines for parallel expansion again
4. Independent expansion of more functionality in `naval`

---

## VII. Final Recommendation

The most valuable organizational approach right now is not to "further subdivide into more directions", but:

1. First acknowledge this is a `shared integration + sensor/naval blocker` problem
2. Use `Lane A` to first nail down shared interfaces, observation surfaces, and contracts
3. Prioritize clearing `weapon` deep realism and truth shortcut
4. Then place `flight / C2-runtime` back into clearer implementation lanes
5. Use `naval` and `air_combat` as high-value scenario acceptance surfaces, not as new entry points for expanding functionality

One-sentence summary:

The next round should switch from "parallel advancement by discipline" to an organizational approach of "first freeze the shared contract, prioritize clearing weapon deep realism, then limited parallel work."
