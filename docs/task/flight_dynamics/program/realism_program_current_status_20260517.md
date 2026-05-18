<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/program/realism_program_current_status_20260517.zh.md. Review before treating this file as authoritative. -->

# Realization Mainline and Associated Sub-Projects Current Status

Status: `2026-05-17` Current workspace integration review version.

Associated Documents:

- [Realization Master Task List](realism_program_taskboard_20260516.zh.md)
- [Realization P1 Master Task List](realism_program_p1_taskboard_20260517.zh.md)
- [C2 Command Chain and Communications Sub-Project](../c2_command_chain/README.md)
- [C2 Command Chain and Communications Progress Checkpoint](../c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md)
- [C2 Command Chain and Communications Open Issues Analysis](../c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
- [Naval Warfare Progress Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)
- [Naval Warfare Subsequent Assignment Execution Sheet](../../naval/naval_delegated_execution_backlog_20260517.zh.md)
- [Air Combat 1v1 F-16C Baseline Switch and Minimal Duel Contract Progress](../../air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)
- [Command Chain and C2 Communications Realism Analysis](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)

Document Positioning:

- This document organizes the document entry points under `docs/task/flight_dynamics/` that are directly related to the current realization mainline.
- It simultaneously links the associated sub-project documents I am currently responsible for: `naval/`, `air_combat/`, `C2 command-chain`.
- This document does not repeat the details of each analysis; it only answers "which documents to look at now, where we are currently, and what remaining stability issues exist."

## 0. Current Overall Phase

The current overall phase is recommended to be uniformly stated as:

1. The mainline as a whole is still in `P1-A integration wrap-up`.
2. The key gatekeeping surfaces for `flight`, `sensor`, `weapon`, `naval` and `C2` have been closed; it is now more appropriate to transition to maintenance mode.
3. In this round of sampling review, `sensor / DataLink / track`, naval weapon command chain, and weapon gatekeeping have all turned green;
   they are no longer written as stable red points; the remaining focus shifts to shared contract closure and structural debt reduction.
4. `C2` has entered "minimum engineering closed loop integrated into the mainline," but it is still not a complete tasking / network / authority system.

This means the most important work now is not to continue expanding multiple lines in depth, but first to close the shared contract and structural debt, then do limited deeper modeling as needed.

## 1. Document Organization Scope

### 1.1 Current Positioning of `flight_dynamics/`

`docs/task/flight_dynamics/` now hosts two types of documents:

1. Core Documents for the Realization Mainline
   - Flight Dynamics
   - Sensors/Situational Awareness
   - Weapons/Guidance
   - Realization Master Task Board
2. Cross-Domain Analysis Input Documents
   - [Naval Warfare Simulation Realism Analysis](../naval/naval_realism_analysis_20260516.zh.md)
   - [Command Chain and C2 Communications Realism Analysis](../c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md)
3. Current Active Sub-Project Entry Points
   - [C2 Command Chain and Communications Sub-Project](../c2_command_chain/README.md)

Type 2 documents remain here for historical tracking and cross-domain analysis completeness, but the current execution status should no longer rely solely on frozen analyses.

### 1.2 How to Read the Current Active Documents

It is recommended to read in the following order:

1. First read this file:
   - Confirm current active directions and true stability status.
2. Then read the master task board and sub-tasks under `flight_dynamics/`:
   - [Realization Master Task List](realism_program_taskboard_20260516.zh.md)
   - [Realization P1 Master Task List](realism_program_p1_taskboard_20260517.zh.md)
3. For the `C2` direction, do not just look at frozen analysis:
   - Currently, first read [C2 Command Chain and Communications Sub-Project](../c2_command_chain/README.md), [Progress Checkpoint](../c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md) and [Open Issues Analysis](../c2_command_chain/c2_command_chain_unresolved_issues_20260517.zh.md)
4. For naval warfare execution status, do not rely on old analysis:
   - Currently, refer to [Naval Warfare Progress Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md) and [Naval Warfare Subsequent Assignment Execution Sheet](../../naval/naval_delegated_execution_backlog_20260517.zh.md)
5. For air combat 1v1 operational status, do not just look at frozen plans:
   - Currently, combine [Air Combat 1v1 F-16C Baseline Switch and Minimal Duel Contract Progress](../../air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md) with current running tests to judge.

## 2. Current Progress Summary

### 2.1 Flight Dynamics Mainline

Current Assessment:

- `Propulsion` has been closed into a unified single source of truth for `Force / Logistics / Instrument / Observation`.
- `StallState` has been upgraded from "just bookkeeping" to a memory-based stall state participating in aerodynamic behavior:
  `effective_stall_progress` now drives `stall_drag / damp_scale / pitch_break_active / debug stall_progress`.
- `test_flight_dynamics_realism_guards.py`, `test_flight_dynamics_tuning_runtime.py`,
  `test_flight_dynamics_p0_runtime_guards.py`, `test_kernel_observation_sanity.py`
  are currently green in this workspace.
- This line is now closer to the latter half of `P1-A`, rather than still being in `P0` or about to enter `P1-B`.
- The focus of this round is no longer "gatekeeping tests are continuously red," but "deeper modeling has not yet progressed, structural debt remains."

Meaning:

- The behavioral contract for this line has entered a state where further deepening is possible.
- It is now more recommended to put `flight` into maintenance mode:
  First ensure shared contracts and regression green lines, do not treat it as the default expansion entry point for the main thread.
- The next more worthwhile investment is deepening `Mach/compressibility / stall / FBW`, and
  closing the boundaries of `default_unit_factory / unit_definition`, rather than continuing firefighting-style fixes to basic runtime.

### 2.2 Sensor/Situational Awareness Mainline

Current Assessment:

- The batch of `P0` main contracts: `shared track != local contact`, `coasted track usability`, `local + datalink -> fused`
  are green in the current workspace.
- `test_sensor_situation_realism_p0.py` and `test_data_link_qos_runtime.py`
  are both green, indicating that `track/report` and QoS contracts have been closed to a maintainable state.
- The maritime sensor main chain has also turned green in this round of review;
  The focus now should be on subsequent deeper modeling and structural closure, rather than continued firefighting on basic contracts.
- Currently closer to the latter half of `P1-A`, can be transitioned to maintenance mode.
- The old frozen analysis statement about "DataLink directly copying contacts" is no longer suitable as a current status description;
  The boundary conditions for `DataLink -> track/report` have been tightened to the current contract.

Meaning:

- This round has re-locked the main semantics: "shared track is visible but does not fabricate local contact."
- This line is no longer one of the main blockers, but has entered the acceptance surface for maintenance mode.
- Note that some old test scenario scopes have also been tightened:
  Certain receiving platforms, if they inherently possess long-range air situational awareness capability, are no longer suitable as
  "scenario carriers that rely solely on datalink for visibility."

### 2.3 Weapon/Guidance Mainline

Current Assessment:

- The shared launch runtime has been integrated into the formal launch chain of `fire_missile()`.
- The minimal factual chain from `UnitDefinition / default_loadout / weapon_select_id` to launch entity initialization has been completed.
- `debug_get_missile_runtime_state()` has been supplemented with key fields for mass, sensor, propulsion, and guidance,
  facilitating runtime verification.
- `launch envelope` has been added as a pre-launch gate:
  `min_launch_range_m / max_launch_off_boresight_deg / lobl_required`
  will reject shots before ammo/cooldown/VLS/munition consumption.
- `midcourse_datalink_supported`, `seeker_activation_range_m`,
  `terminal_seeker_active` have entered runtime, with dedicated gatekeeping tests locking the handover semantics between midcourse and terminal guidance.
- Currently closer to the latter half of `P1-A`, rather than still being in the `P0` workaround phase described in the old frozen analysis.

Meaning:

- `test_weapon_guidance_realism_guards.py` and
  `test_air_combat_1v1_fire_missile.py` are currently green.
- It is now possible to clearly verify: different station choices result in missile runtimes driven by different definitions,
  while the global `set_missile_tuning()` can still explicitly override the definition baseline.
- However, a new structural risk must be acknowledged:
  The weapon line has now gone beyond just "rejecting shots on incomplete packages" and has started to incorporate
  `definition-driven launch tuning`, `global tuning overlay`, and `station-based launch selection`
  together into `simulation_kernel_weapon_api.cpp`;
  behaviorally it is green, but structurally this means that `Lane C` will need to continue splitting the responsibility boundaries of launch resolution,
  tuning overlay, and runtime assembly.
- Therefore, it is now more recommended to put `weapon` into maintenance mode:
  First freeze the shared contract, and do not treat `midcourse / seeker type / damage layering`
  as the default next cut for the main thread.

### 2.4 Naval Warfare Sub-Project

Current Assessment:

- The direct-recovery -> hold handoff of `screen-hold` has achieved minimal closure.
- `test_naval_screen_scenario.py` is currently green.
- The batch of naval warfare foundations like `UNREP / abstract stores / maritime override / multi-sensor+ESM` remain green.
- `test_naval_ship_database.py` and `test_ship_mission_command_authority.py`
  this set of targeted test cases for naval weapon command chain/authority are green in this round of review.
- The most important work for naval warfare now is no longer `screen-hold`, but to incorporate the closed `naval` shared semantics
  into the `C2/runtime` maintenance mode.

Meaning:

- Naval warfare no longer has `screen-hold` regression as the main blocking point.
- This round of sampling review did not reproduce red points in the naval weapon command chain; it is more suitable as an acceptance surface for maintenance mode.
- Therefore, naval warfare is also not suitable as a new main line for feature expansion, but should enter maintenance mode as a high-value acceptance surface for `C2/runtime`.
- The next step should continue to place naval warfare as a high-value acceptance surface for `C2/runtime`, but no longer treat it as an independent firefighting line.

### 2.5 Air Combat 1v1 Sub-Project

Current Assessment:

- The direct path of `fire_missile` and the bridge path of `PilotAction.fire_weapon` have both been incorporated into definition-driven
  missile runtime verification.
- The semantic alignment issue of `air_combat_1v1_fixture` on the `ScenarioLoader` entry has been closed;
  [tests/runtime/test_air_combat_1v1_fixture.py](../../../../tests/runtime/test_air_combat_1v1_fixture.py)
  is currently green.

Key facts confirmed by this main thread:

- From the first frame, the `Red_Fighter` raw contact is visible, but it may still be `Tentative / Unknown`.
- By around the second frame, it will be upgraded to hostile confirmed track, `classification=2`.
- The previous failure was not due to the kernel losing the hostile classification, but because the fixture stopped prematurely when "first seeing the contact"
  and then used the raw contact to assert hostile track semantics.

Meaning:

- `ScenarioLoader / fixture` is now consistent with the main semantics of `shared track != raw contact`.
- Air combat 1v1 no longer has consistently reproducible behavioral red points; the remaining effort shifts to reward / termination /
  eval contract deepening, as well as deeper modeling work.

### 2.6 C2 / Command Chain Analysis Line

Current Assessment:

- The profile routing of `bridge.py` has been closed: explicit `tasking_profile` takes priority,
  falling back to `service_profile` to infer `naval / air` when absent.
- `naval_profile.build_kernel_mission_command()` has been supplemented with a batch of key field authoring:
  `embarked_helo_entity_id / launch_helo / recover_helo / relay_oth_targeting /
  recovery_* / formation_*`.
- The Python builder, runtime roundtrip, and world-batch roundtrip for `MissionCommand`
  all have explicit tests locking them.
- `CommandLink` has progressed from "only minimal FIFO" to "queue backlog can be reordered with minimal priority,"
  and the backlog debug surface also has explicit tests locking it.
- The Python mainline access surface of `RuntimeFacade` has been reclaimed into an explicit adapter,
  with `RuntimeFacade.runtime()` now only serving as a compatibility / diagnostics escape hatch.

Meaning:

- `test_naval_mission_command_mapping.py`, `test_mission_command_roe_fields.py`,
  `tests/world_batch/test_world_batch_runtime.py`, `test_mission_command_air_fields_roundtrip.py`
  the relevant roundtrip test cases are currently green.
- `tests/runtime/test_command_link_qos.py`, `tests/architecture/test_runtime_facade_layering.py`
  and `test_world_setup_compat.py` now lock the queue / adapter / compat scope as gatekeeping lines.
- The main remaining effort for the `C2` direction has shifted from "field drift" to
  `CommandLink priority / jitter / retry`, `relay / jamming / doctrine`,
  `RuntimeFacade / ScenarioLoader compat` reduction, and deeper tasking closure.

## 3. Stability Issues Found in Current Review

### 3.1 No New Stable Failures Reproduced

No stable failures were reproduced in the current main thread sampling review; the targeted regressions corresponding to this section have turned green:

1. [tests/runtime/test_sensor_situation_realism_p0.py](../../../../tests/runtime/test_sensor_situation_realism_p0.py)
2. [tests/runtime/test_data_link_qos_runtime.py](../../../../tests/runtime/test_data_link_qos_runtime.py)
3. [tests/runtime/test_naval_ship_database.py](../../../../tests/runtime/test_naval_ship_database.py)
4. [tests/runtime/test_ship_mission_command_authority.py](../../../../tests/runtime/test_ship_mission_command_authority.py)
5. [tests/runtime/test_mission_command_air_fields_roundtrip.py](../../../../tests/runtime/test_mission_command_air_fields_roundtrip.py)
6. [tests/runtime/test_world_setup_compat.py](../../../../tests/runtime/test_world_setup_compat.py)
7. [tests/runtime/test_command_link_qos.py](../../../../tests/runtime/test_command_link_qos.py)
8. [tests/runtime/test_weapon_guidance_realism_guards.py](../../../../tests/runtime/test_weapon_guidance_realism_guards.py)

Current result: This round of targeted regression has turned green; no stable failures reproduced.

Supplementary notes:

1. The more appropriate overall scope now is "key gatekeeping surfaces are basically green."
2. This does not mean all sub-directions can claim full sign-off.
3. The current mainline focus has shifted from generalized `flight / weapon` to structural debt reduction and limited deepening,
   rather than `flight / weapon / screen-hold`, which were previously considered higher-priority risks.

### 3.2 Key Surfaces Verified as Green

1. Main thread completed `build-workshop` recompilation; `ef_core` builds successfully.
2. Main thread integration acceptance:
   - `test_flight_dynamics_realism_guards.py`
   - `test_flight_dynamics_tuning_runtime.py`
   - `test_flight_dynamics_p0_runtime_guards.py`
   - `test_kernel_observation_sanity.py`
   - `test_weapon_guidance_realism_guards.py`
   - `test_air_combat_1v1_fire_missile.py`
   - `test_naval_screen_scenario.py`
   - `test_sensor_situation_realism_p0.py`
   - `test_data_link_qos_runtime.py`
   - `test_naval_mission_command_mapping.py`
   - `test_mission_command_roe_fields.py`
   - `tests/world_batch/test_world_batch_runtime.py::WorldBatchRuntimeTests::test_world_batch_runtime_mission_command_roundtrip_preserves_naval_extension_fields`
   - Current result: `82 passed`
3. Newly added focused acceptance in this round is green:
   - `tests/architecture/test_runtime_facade_layering.py`
   - `tests/world_batch/test_world_batch_vec_env.py`
   - `tests/runtime/test_command_link_qos.py`
   - `tests/runtime/test_mission_command_roe_fields.py`
   - `tests/runtime/test_flight_dynamics_tuning_runtime.py`
   - Current result: `51 passed`
4. `Weapon` specific tests with explicitly specified new build artifacts are green:
   - `CMO_BUILD_DIR=build pytest -q tests/runtime/test_weapon_guidance_realism_guards.py tests/runtime/test_air_combat_1v1_fire_missile.py`
   - Current result: `29 passed`
5. `MissionCommand` Python/C++ closure related targeted verification is green: `11 passed`
6. `DataLink QoS` extended gatekeeping line is green: `8 passed, 2 subtests passed`
7. Naval warfare `screen-hold` full scenario verification is green: `8 passed`
8. `RuntimeFacade / MissionCommand` adapter and air/naval roundtrip gatekeeping lines are green:
   - `tests/architecture/test_runtime_facade_layering.py`
   - `tests/runtime/test_mission_command_air_fields_roundtrip.py`
   - `tests/runtime/test_world_setup_compat.py`

### 3.3 Structural Risks Still Present

These are not behavioral red lights in this round, but they remain the most important architectural debts:

1. God Factory tendency in `default_unit_factory.h`
2. Content layer pollution in `content/unit_definition.h`
3. `Weapon launch resolution + tuning overlay + runtime assembly` beginning to converge in `simulation_kernel_weapon_api.cpp`
4. The `RuntimeFacade.runtime()` compatibility escape hatch still exists
5. `ScenarioLoader` is still a God Object on the Python side
6. `SimulationKernel` public API continues to bloat

Their detailed analysis remains based on
[code_quality_review_realism_wave_20260517.zh.md](code_quality_review_realism_wave_20260517.zh.md).

### 3.4 Small Structural Fixes Closed in This Round

Although major structural debts remain, `Lane A` has already closed two low-risk small fixes in this round:

1.  Deduplication of `sensor` default value sources  
   - `default_unit_factory.h` no longer carries an independent sensor default value implementation  
   - Now reuses the default sensor baseline from `unit_definition` / loader side, with factory preset overlay applied on top  

2.  Deduplication of missile 3D vector type  
   - `missile_guidance_math.h` no longer maintains an independent `Vec3` struct  
   - Changed to `using Vec3 = Math::Vector3`  

Implications:  

- These two changes are not yet sufficient to eliminate the major structural debt of `default_unit_factory` and `weapon guidance`,  
  but they have already halted two categories of low-cost regressions: "duplicate default value sources" and "parallel basic types".  
- In the next round, we can continue deeper decomposition in the same direction without needing to clean up these basic noises first.  

### 3.5  Completed closure of `RuntimeFacade / ScenarioLoader` in this round  

In addition to the two small incisions above, this round (`Lane A`) also completed one round of main-thread closure for `RuntimeFacade / ScenarioLoader`:  

1.  Python-side `RuntimeFacade` access surface has been closed back to explicit adapter  
   - More world/time-step/visual accesses in `world_batch_vec_env.py` now go through `_RuntimeFacadeAdapter`  
   - `leader_world_batch_runtime.py` has reduced business-level direct penetration of `batch_runtime.world(...)`  
   - `tests/architecture/test_runtime_facade_layering.py` has added layering guards to lock this closure direction  
2.  `ScenarioLoader` has completed the first-phase extraction of the state shell  
   - Runtime fields such as mission/route/reward/termination have been centralized into `runtime_state.py`  
   - `core.py` now maintains backward-compatible property access via `_state_shell`  
3.  The synchronization contract between the execution episode controller and loader state has been filled in  
   - This round fixed write-back omissions for `mission_command / route cache / post-waypoint / mission phase` on the main thread  
   - Also fixed mirror semantics for fields like `cached_route_ref_id=0` (field exists but value is zero)  
4.  The scripted-opponent owner of `ScenarioLoader` has completed first-phase extraction  
   - The build/reset/step lifecycle has been sunk into `behavior_runtime/scripted_opponents.py`  
   - `core.py` now only retains a thin proxy and compatible access surface  
   - Compatible reads via `loader.scripted_opponents` / `loader.scripted_opponent_reports` are still retained  
5.  The command-chain owner of `ScenarioLoader` has completed first-phase extraction  
   - `_leader_phase_manager` and naval-screen runtime cache  
     have been sunk into `behavior_runtime/command_chain_owner.py`  
   - `command_chain.py` now delegates lifecycle and kernel sync to the collaborator owner  
   - `ScenarioLoader` still retains compatible proxy entry points for `_leader_phase_manager` / `_naval_screen_*`; the old path for external injection via bridge has not been interrupted  
   - Targeted regression tests cover `execution_episode_state / naval_screen / common_core / world_batch / air_combat fixture`  
6.  The behavior-phase owner of `ScenarioLoader` has completed first-phase extraction  
   - `post_waypoint_transition / mission_phase_name / _approach_prev_*`  
     have been sunk into `behavior_runtime/behavior_phase_owner.py`  
   - `runtime_state.py` now continues to maintain the import/export contract for execution episode state through a unified mirror view  
   - `ScenarioLoader` still retains old field names and private method entries; the compatibility assertion of `_state_shell` continues to hold  
   - Related extended regression tests are currently green: `57 passed`  

Additional implications:  

- This indicates that the risk of `RuntimeFacade.runtime()` still exists, but has been narrowed from "scattered penetration in the main thread" to "compatible escape hatches still present".  
- The problem of `ScenarioLoader` has also been narrowed from "state and orchestration all crammed into one owner" to "compat facade cleanup and deeper owner offloading still to be continued; main owner is still oversized".  

### 3.6  Low-confidence noise  

Currently kept only as notes, not counted as confirmed failures:  

1.  Subagent reports occasionally mentioned `MemoryError / nanobind` observation read noise under `pytest` environment  
2.  This round's main thread could not stably reproduce this, so it is not elevated to a primary stability issue  

## 4.  Suggested follow-up processing order  

It is recommended to proceed in the following order, rather than spreading all lines simultaneously again:  

1.  First, close the structural closure of `Lane A`  
   - `default_unit_factory`  
   - `unit_definition`  
   - `RuntimeFacade / ScenarioLoader`  
   - These issues are not red currently, but have become the boundary debt that should be cleaned first before continuing to expand functionality in the next round  
2.  Then proceed with deeper modeling  
   - `flight`: Mach/compressibility / stall / FBW  
   - `sensor`: relay / jamming / deeper fusion  
   - `weapon`: seeker type / fuze / damage layering  
   - `C2/naval`: deeper tasking / authority / message loop  

After this round, the recommended entry order for `Lane A` can be further narrowed to:  

1.  First complete the remaining closure of `RuntimeFacade` Python main thread  
   - No rush to delete C++ bindings  
   - Continue to freeze `batch_runtime` / raw runtime as compatible escape hatches, not as maintenance interfaces  
2.  Then continue splitting `ScenarioLoader`  
   - State shell, scripted-opponent owner, command-chain owner, behavior-phase owner: first phase completed  
   - Next priority: offload compatible entries in `core.py` and deeper behavior-owner slicing, rather than expanding `core.py` again  

## 5.  Most recommended document entry points for now  

If the next round is to proceed, it is recommended to look first at:  

1. [Realistic P1 Task Master List](realism_program_p1_taskboard_20260517.zh.md)  
2. [Realistic Mainline Closure Plan](realism_program_convergence_plan_20260517.zh.md)  
2. [Naval Warfare Progress Checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)  
3. [Air Combat 1v1 F-16C Baseline Switch and Minimum Engagement Contract Progress](../../air_combat/air_combat_1v1_f16c_baseline_progress_20260516.zh.md)  
4. [C2 Command Chain and Communication Subproject](../c2_command_chain/README.md)  
5. This document  

Benefits of this approach:  

- It avoids mistaking the frozen analysis under `flight_dynamics/` for the current execution state  
- It directly shows the gap between "mainline planning" and "current stability reality"  
- It allows aligning "current overall phase, main blockers, and freeze scope" first, before deciding whether it is worth distributing more parallel implementations
