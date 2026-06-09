<!-- Machine-translated draft generated on 2026-05-18 from docs/task/code_redundancy/code_redundancy_duplication_audit_20260516.zh.md. Review before treating this file as authoritative. -->

# Code Redundancy and Duplicate Logic Audit Report

Status: `2026-05-16` Full static analysis completed; `2026-05-16` Code review and first-round implementation convergence completed for non-`scenario_loader` mainline items within the freeze scope  
Scope: Redundancy and duplicate logic in C++ core engine, ECS component system, command chain data structures, and Python RL runtime

## 1. Background

After multiple rounds of refactoring (flat struct → Core/Air/Naval multi-inheritance split, `python/rl` root directory → sub-package convergence, `MovementCommand` → `PilotAction` migration), this project inevitably produced transitional remnants. This report focuses on **still-active duplicate code, overlapping fields, dual-track parallelism, and maintenance risks**.

## 2. Audit Scope

- `src/components/` — ECS component definitions (commands, tasks, physics, systems)
- `src/systems/` — System implementations (aerodynamics, forces, control, sensors, data links, ground contact)
- `src/core/engine/` — Core engine system registration and orchestration
- `python/rl/` — RL runtime Python layer (profile, tasking, runtime, control)
- `gym_envs/` — Gymnasium environment wrappers

## 2.1 Review Notes

- This review **excluded** re-evaluation of the `gym_envs/scenario_loader/*` mainline split items, particularly `5.3`, `5.11`, and `5.15`; these entries retain the original audit conclusions but are not a priority for the current round.
- The review conclusion uses three tiers:
  - `Valid`: The issue objectively exists and is suitable for current maintenance.
  - `Partially valid`: The phenomenon exists, but the original description is too broad, or part of it constitutes a reasonable layering/compatibility bridge.
  - `Not a priority for now`: The phenomenon exists, but it resembles a compatibility layer, validation layer, or reserved interface, and should not be treated as a priority "redundancy cleanup."
- After review, the most suitable immediate entry points are confirmed as: `3.1`, `3.3`, `5.7`, `5.12`, `5.13`. These changes are decoupled from the `scenario_loader` mainline split, have clear benefits, and manageable regression impact.
- After the `2026-05-16` freeze plan execution, all authorized convergences for `3.1`, `3.3`, `3.2`, `5.4`, `5.7`, `5.10`, `5.12`, and `5.13` have been recorded. This document serves as an audit and tracking baseline, no longer acting as an activity plan.

## 3. High Priority Findings

### 3.1 `MassProperties` Duplicated in System Registration

**Location**: [src/core/engine/simulation_kernel_systems.cpp:78 and :99](../../../../src/core/engine/simulation_kernel_systems.cpp)

```cpp
ecs.component<MassProperties>();  // Line 78
// ...
ecs.component<MassProperties>();  // Line 99 — identical duplicate
```

Although duplicate registration in flecs is idempotent, the two declarations appear in different sections (Physics section and EW/Logistics section), indicating a lack of organized grouping of registration code by component semantics.

**2026-05-16 Execution Update**: The current version has removed the duplicate registration; `src/core/engine/simulation_kernel_systems.cpp` now contains only one `ecs.component<MassProperties>()`. The direct duplication issue for this entry has been resolved. Subsequent work, if any, will focus mainly on the dual-track mass component boundary described in `3.2`, rather than the registration boilerplate.

---

### 3.2 `Mass` and `MassProperties` Dual-Track Mass Components

**Review Conclusion**: `First batch of boundary reinforcement completed`

**Location**:
- `Mass` defined in [src/components/physics/dynamics.h](../../../../src/components/physics/dynamics.h)
- `MassProperties` defined in [src/components/systems/logistics.h](../../../../src/components/systems/logistics.h)

| Field | `Mass` | `MassProperties` |
|---|---|---|
| `empty_mass_kg` | ✅ | ✅ **Duplicate** |
| `fuel_mass_kg` | ✅ | — |
| `stores_mass_kg` | ✅ | — |
| Total mass retrieval method | `get_total_kg()` | `current_total_mass_kg` |
| Reference area/wingspan/chord | — | ✅ |
| Drag index | — | ✅ |

**Impact**:

1. `empty_mass_kg` is distributed across two components, which may lead to data inconsistency.
2. `aerodynamics_system.h` uses `MassProperties` (reads area/chord), while `force_system.h`, `leapfrog_system.h`, and `ground_contact_system.h` use `Mass` (reads total mass).
3. `logistics_system.h` must update both components simultaneously (`MassUpdate` system uses `MassProperties, Mass, FuelSystem` as parameters), doubling maintenance cost.

**Suggestion**: Unify `empty_mass_kg` and `get_total_kg()` into a single authoritative component (`MassProperties`). The `Mass` component should retain only fuel/load sub-fields, or be removed entirely.

**2026-05-16 WP-C Execution Update**: The current version has completed the first batch of boundary reinforcement:
- [src/systems/systems/logistics_system.h](../../../../src/systems/systems/logistics_system.h) `MassUpdate` now explicitly uses `Mass` as the authoritative runtime decomposition source and synchronizes `MassProperties.empty_mass_kg/current_total_mass_kg`;
- `MassProperties.current_total_mass_kg` now mirrors `Mass::get_total_kg()`, thus no longer missing `stores_mass_kg`;
- Added minimal debug readback and direct regression tests to verify the `Mass` / `MassProperties` synchronization, without expanding into a general component exposure surface.

Remaining items:
- The dual-track structure of `Mass` and `MassProperties` still exists;
- `aerodynamics / force / leapfrog / ground_contact` still read from different component surfaces; this level of "single authoritative component migration" is outside the current freeze scope.

---

### 3.3 `command_link_system.h` Three System Copy-Paste

**Location**: [src/systems/systems/command_link_system.h:7-68](../../../../src/systems/systems/command_link_system.h)

The three systems `CommandLinkMovement`, `CommandLinkAction`, and `CommandLinkMission` contain identical logic — only the component types differ:

```cpp
// Three identical code blocks, only component types differ:
if (!pending[i].active) continue;
if (current_time < pending[i].deliver_time) continue;
cmd[i] = pending[i].command;
cmd[i].active = true;
pending[i].active = false;
```

**Impact**: Each modification to the delivery/deferral logic requires changes in three places, making omissions easy.

**Suggestion**: Replace the three repetitive code blocks with a C++ template function `deliver_pending<TCmd, TPending>(iter)`, eliminating approximately 45 lines of redundancy.

**2026-05-16 Execution Update**: The current version has introduced a template helper `deliver_pending_command()` in `src/systems/systems/command_link_system.h`, converging the common delivery logic for `Movement / Action / Mission` types. The copy-paste issue for this entry has been cleaned up in the first round.

---

### 3.4 Python Side Manually Maintains C++ Struct Field Mirrors

**Location**: [gym_envs/leader_env.py:83-177](../../../../gym_envs/leader_env.py)

```python
_TASK_ORDER_FIELDS = (
    "task_id", "task_type", "service_profile", ...
)  # 50+ fields

_LEADER_INTENT_FIELDS = (
    "phase_id", "element_phase_id", ...
)  # 33 fields

_PILOT_REPORT_FIELDS = (
    "report_type", "sender_id", ...
)  # 23 fields
```

These lists are used in `_clone_task_order()`, `_clone_leader_intent()`, and `_clone_pilot_report()` to copy fields one by one via `setattr(getattr())`.

**Risk**: Each time a C++ struct field is added or removed, the Python side must manually synchronize three field lists; otherwise the clone operation silently drops fields.

**Suggestion**: Use nanobind’s type reflection (all fields are already registered via `nb::enum_` / `nb::class_`) to automatically generate field name lists, or at least add unit tests to verify consistency between Python field lists and C++ structs.

**2026-05-16 Execution Update**: The first round of fixes has been completed:
- Added missing cooperative takeoff field mirrors for `TaskOrder` / `LeaderIntent`;
- In `gym_envs/leader_env.py`, added `_clone_assign_field()` to handle failed assignments from Python `int` to `ef_py enum`, preventing strong-typed enum fields from being silently dropped;
- Added reflective validation in `tests/leader/test_two_ship_contract_fields.py` requiring the Python field lists to match `dir(ef_py.TaskOrder/LeaderIntent/PilotReport)`.

**2026-05-16 Continued Push**: Further transformed `_TASK_ORDER_FIELDS` / `_LEADER_INTENT_FIELDS` / `_PILOT_REPORT_FIELDS` to be generated directly from `dir(ef_py.*())` reflection, and converged the clone core into a unified implementation. The Python side no longer maintains separate field name tuples, retaining only the clone compatibility layer.

Further evaluation may continue on whether `leader_env` can clone directly based on reflection results, without maintaining explicit field constant exports.

---

## 4. Medium Priority Findings

### 4.1 `MovementCommand` Legacy System Still Active in 9 Files

**Review Conclusion**: `Partially valid`

**Referenced Files**:
- `src/systems/physics/force_system.h`
- `src/systems/physics/ground_contact_system.h`
- `src/systems/physics/instrument_system.h`
- `src/systems/systems/logistics_system.h`
- `src/systems/systems/command_link_system.h`
- `src/systems/core/operation_system.h`
- `src/core/engine/simulation_kernel_systems.cpp`
- `src/core/engine/simulation_kernel_command_api.cpp`
- `src/core/engine/exact_stage_inventory.cpp`

Repeated pattern in each system:

```cpp
// Priority 1: PilotAction (new)
if (pilot && pilot->active) { throttle = pilot->throttle; }
// Priority 2: MovementCommand (legacy)
else if (cmd && cmd->active) { throttle = cmd->throttle_cmd; }
```

The `MovementCommand` legacy chain indeed spans 9 files, but the claim "the same priority logic repeated in 9 files" is not entirely accurate. After review, the actual repeated throttle/brake/command fallback logic is mainly concentrated in a few runtime systems like `force_system.h`, `logistics_system.h`, `ground_contact_system.h`, `instrument_system.h`. The other files mostly maintain compatibility paths for registration, API exposure, or phase inventories.

**Suggestion**: Extract a common function `resolve_throttle(entity)` to eliminate duplication, and mark `MovementCommand` as `[[deprecated]]` after all references have been migrated.

**2026-05-16 Execution Update**: The first round of convergence has been completed:
- Added `src/components/command/air/control_input_resolution.h`;
- Converged the repeated `PilotAction -> MovementCommand` throttle/brake fallback logic from `force_system.h`, `logistics_system.h`, `ground_contact_system.h`, and `instrument_system.h` into a shared helper;
- Retained the third-priority `ActionCommand` logic in `logistics_system.h` and the legacy idle/full-brake special cases in `ground_contact_system.h` locally to avoid over-abstraction;
- Added runtime regression tests to verify that `PilotAction` still takes precedence over legacy `MovementCommand`.

**2026-05-16 Continued Push**: Completed the second batch of convergence:
- Added unified construction helpers for legacy autopilot/stick/lagged commands in `src/components/command/legacy_command.h`;
- Added `make_pending_movement_command()` in `src/components/command/command_link.h`;
- Converged duplicate `MovementCommand` / `PendingMovementCommand` / `LaggedCommand` initialization boilerplate from `src/core/engine/simulation_kernel_command_api.cpp` and `src/models/core/default_unit_factory.h` into shared helpers.

**2026-05-16 Further Push**: Completed the third batch of low-risk boilerplate cleanup:
- Added `make_action_command()` in `src/components/command/legacy_command.h`;
- Added `make_pending_action_command()` and `make_pending_mission_command()` in `src/components/command/command_link.h`;
- Switched aggregate initialization of `ActionCommand` / `PendingActionCommand` / `PendingMissionCommand` in `src/core/engine/simulation_kernel_command_api.cpp` and `src/models/core/default_unit_factory.h` to shared helpers;
- Removed duplicate inactive reset of `ActionCommand` in `DefaultUnitFactory`, reducing compatibility layer boilerplate noise.

**2026-05-16 WP-A First Batch**: Continued tightening internal boilerplate in `simulation_kernel_command_api.cpp`:
- Added file-local helpers to unify `entity_id -> flecs::entity` invalid guard/warn;
- Added shared helper to unify `world_time_total` reading and determination of whether `CommandLink` needs to enter pending delivery path;
- Converged the `active=true` copy-set pattern for `PilotAction` / `MissionCommand` / `TaskOrder` / `LeaderIntent` / `PilotReport` into a shared helper;
- Added direct regression tests for invalid entity no-op and roundtrip `active` flag setting.

**2026-05-16 WP-A Second Batch**: Performed a final low-risk boilerplate convergence on `src/systems/core/operation_system.h`:
- Extracted `operation_seed_movement_command()` and `operation_seed_lagged_command()`;
- Converged the duplicate block in `ActionMapping` / `CommandLag` that initializes legacy target state from current `Transform + Velocity` into shared seed helpers;
- After review, `src/systems/physics/control_system.h` currently only handles scheduling/forwarding responsibilities and lacks duplication worth further extraction; therefore scope expansion for abstraction is not warranted this round.

The `MovementCommand` compatibility chain itself still exists, so this entry remains "partially valid," but the first round of duplicate logic is no longer dispersed across implementations.

---

### 4.2 `common_core_defaults.py` ↔ `common_core_profile.py` Function Wrappers

**Review Conclusion**: `Partially valid`

**Location**:
- [python/rl/profile/common_core_defaults.py](../../../../python/rl/profile/common_core_defaults.py) (132 lines) — Low-level primitives
- [python/rl/tasking/common_core_profile.py](../../../../python/rl/tasking/common_core_profile.py) (630 lines) — Wrapper layer

Almost every low-level function has a `_`-prefixed version in the upper layer:

| Low-Level Function | Upper Wrapper |
|---|---|
| `service_profile_default()` | `_service_profile_default()` |
| `task_family_default()` | `_task_family_default()` |
| `coordination_mode_default()` | `_coordination_mode_default()` |
| `infer_tactical_unit_type()` | `_infer_tactical_unit_type()` |
| `infer_recovery_site_id()` | `_infer_recovery_site_id()` |

The front part of the upper file indeed contains a batch of forwarding wrappers like `_service_profile_default()` / `_task_family_default()`, but the latter half functions such as `apply_task_order_common_core_defaults()`, `apply_leader_intent_common_core_defaults()`, `apply_pilot_report_common_core_defaults()` perform real profile selection, default value orchestration, and air/naval semantic bridging. Therefore it is not an "entirely deletable empty wrapper layer"; it is more suitable for limited contraction rather than simple merging.

**Suggestion**: Evaluate whether the composition functions in `common_core_profile.py` (e.g., `apply_task_order_common_core_defaults`) can be moved down to the `profile/` directory, or allow callers to use the underlying API directly.

---

### 4.3 `leader_env.py` 1752 Lines: Environment Logic Mixed with Command Strategy

**Location**: [gym_envs/leader_env.py](../../../../gym_envs/leader_env.py) — Longest Python file in the project

This file mixes:
- Environment lifecycle (`step/reset/close`)
- Action decoding (`_decode_action`, including quantization interval mapping logic)
- Action sanitization (`_sanitize_action_mapping`, including takeoff protection, approach gating, etc.)
- Command application (`_apply_leader_command`, 110 lines, includes complete phase→cmd_code mapping table)
- Observation building (`_build_observation`, 110 lines)
- Execution policy management (`_build_execution_policy`, `_predict_execution_action`)
- C2/teacher baseline management (`_compute_teacher_baseline`, `_update_scripted_c2`)

**Suggestion**: Extract `_decode_action` + `_sanitize_action_mapping` + `_apply_leader_command` into an independent module `leader_command_codec.py` under `python/rl/tasking/`, and extract `_build_observation` into `leader_observation_builder.py`.

---

### 4.4 `air_profile.py` and `naval_profile.py` Parallel Interfaces

**Review Conclusion**: `Partially valid`

**Location**:
- [python/rl/profile/air_profile.py](../../../../python/rl/profile/air_profile.py) (31 functions)
- [python/rl/profile/naval_profile.py](../../../../python/rl/profile/naval_profile.py) (18 functions)

11 functions exist with the same name in both modules:

`build_kernel_mission_command`, `infer_coordination_mode`, `infer_recovery_approach_type`, `infer_recovery_base_id`, `infer_recovery_runway_id`, `infer_route_ref_id`, `is_patrol_task`, `is_recover_task`, `normalize_task_order_spec`, `resolved_task_family`, `task_observation_codes`

This is a normal decomposition of the strategy pattern (air vs naval behavior differs) and should not be simply considered "meaningless duplication." However, among them, `is_patrol_task`, `is_recover_task`, `resolved_task_family`, and some recovery inference functions still have commonalities that can be extracted, suitable for shared primitive extraction without breaking domain boundaries.

**Suggestion**: Create a shared base class `BaseTaskingProfile` for air/naval profiles, moving common implementations up, and using polymorphism only at points of domain difference.

---

## 5. Low Priority Findings

### 5.1 Compatibility Transition Files

**Review Conclusion**: `Not a priority for now`

| File | Content | Conditions for Deletion |
|---|---|---|
| [src/components/physics/action.h](../../../../src/components/physics/action.h) | Contains only 13 `#include` | All external references migrated to direct imports |
| [src/components/tasking/tasking_enums.h](../../../../src/components/tasking/tasking_enums.h) | Contains only 2 `#include` | `action.h` no longer references it |

---

### 5.2 C++ Side `PilotAction` Fields Partially Unused

**Review Conclusion**: `Not a priority for now`

`PilotAction` defines over 20 fields (including `radar_active`, `radar_scan_az`, `radar_scan_el`, `tms_up`, `master_arm`, `fire_weapon`, `fire_gun`, `weapon_select_id`, etc.), but in the current simulation:
- The sensor system (`default_sensor_model.cpp`) does not read `radar_active` / `radar_scan_az` / `radar_scan_el` — radar always scans omnidirectionally
- The weapon system (`default_guidance_model.cpp`) does not read `master_arm` / `fire_weapon` — missiles are launched directly via the `fire_missile()` API

These fields are correctly reserved placeholders for future expansion and do not constitute redundancy, but the gap of "interface defined, behavior not implemented" is worth noting.

---

### 5.3 `scenario_loader/core.py` Large File 3831 Lines

**Location**: [gym_envs/scenario_loader/core.py](../../../../gym_envs/scenario_loader/core.py) — 188KB, largest single file in the project

The `ScenarioLoader` class contains 129 methods, with responsibilities spanning:

- Scenario JSON parsing and compilation
- Entity generation and randomization
- Waypoint generation and rotation
- ILS beacon management
- Mission command construction
- C2 task interface
- Execution episode state construction
- Observation cache management
- Reward/termination runtime fields
- GPU backend mode switching
- Post-compilation scenario loading

**Issue**: This file is larger than the combined size of `python/scenario_compiler.py` (1321 lines, 59 functions) and `python/scenario_runtime.py` (1520 lines, 38 functions). Both `ScenarioCompiler` and `ScenarioLoader` handle scenario compilation logic, resulting in semantic overlap and unclear call relationships.

**Suggestion**: Split `core.py` by responsibility into `scenario_loading.py`, `entity_spawning.py`, `mission_building.py`, and `runtime_state.py` (the latter already partially exists but is far smaller than the corresponding logic in `core.py`).

---

### 5.4 Three Scripted Controllers Share a Pattern but No Base Class

**Review Conclusion**: `First batch integration completed`

**Locations**:
- [python/rl/control/scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py)
- [python/rl/control/scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py)
- [python/rl/control/scripted_landing.py](../../../../python/rl/control/scripted_landing.py)

The three classes share identical interfaces and initialization patterns:

```python
class ScriptedXxxController:
    def __init__(self, *, action_dim: int, dt: float = 0.05):
        self.action_dim = int(action_dim)
        self.dt = float(dt)
        # ...

    def reset(self, obs: dict) -> None:
        inst = np.asarray(obs.get("instruments", ...))
        mission = np.asarray(obs.get("mission", ...))
        # identical inst/mission extraction pattern ...

    def step(self, obs: dict) -> np.ndarray:
        inst = np.asarray(obs.get("instruments", ...))
        mission = np.asarray(obs.get("mission", ...))
        # identical field extraction pattern ...
```

Additional duplication:
- The `_wrap_deg()` helper function is defined once each in `scripted_takeoff.py` and `scripted_landing.py`
- Instrument array index unpacking (`ias = inst[0]`, `alt_radar = inst[3]`, etc.) is implemented independently in all three places

**Suggestion**: Extract a `BaseScriptedController` abstract base class that unifies the `__init__`/`reset`/`step` template methods and shared instrument decoding logic. The three subclasses would only implement the differentiated control laws.

**2026-05-16 WP-B Execution Update**: The current version has completed minimal shared skeleton extraction:
- Added [python/rl/control/base_scripted_controller.py](../../../../python/rl/control/base_scripted_controller.py), unifying `action_dim/dt`, `obs -> np.ndarray` unpacking, zero-action construction, and `wrap_deg()`;
- [scripted_takeoff.py](../../../../python/rl/control/scripted_takeoff.py), [scripted_stable_flight.py](../../../../python/rl/control/scripted_stable_flight.py), [scripted_landing.py](../../../../python/rl/control/scripted_landing.py) have been switched to the shared helper, without modifying their control law bodies or changing public class names or constructor signatures;
- Focus contracts have passed regression: `scripted_takeoff_takeoff2_throttle`, `scripted_takeoff_clearance_hold`, `scripted_landing_controller`, `scripted_stable_flight_rudder_sign`;
- Also fixed the missing `type: "unit_regression"` test fixture metadata in [tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json](../../../../tests/contracts/unit/controllers/scripted_takeoff_clearance_hold.json) so it can be properly dispatched by the unified contract runner.

Remaining items:
- The instrument field indices and control laws inside the three controllers remain as local implementations;
- This iteration did not expand to `wrappers.py`, `leader_env.py`, or the broader scripted baseline runtime, deliberately keeping a low-risk boundary.

---

### 5.5 `world_batch_vec_env.py` ↔ `cooperative_world_batch_vec_env.py` Parallel Implementations

**Review Conclusion**: `Partially valid`

**Locations**:
- [python/rl/runtime/world_batch_vec_env.py](../../../../python/rl/runtime/world_batch_vec_env.py) (2018 lines)
- [python/rl/runtime/cooperative_world_batch_vec_env.py](../../../../python/rl/runtime/cooperative_world_batch_vec_env.py) (1861 lines)

The two files still share many function names and import patterns, and indeed retain considerable parallel implementations, but the “completely independent dual-write” is no longer accurate. `cooperative_world_batch_vec_env.py` explicitly reuses infrastructure from `world_batch_vec_env.py`, such as `_RuntimeFacadeAdapter`, `_normalize_batch_observation_backend`, and `_normalize_batch_visual_backend`.

Shared infrastructure still maintained separately includes:

- `_batch_observation_backend_mode()`
- `_normalize_flight_shaping_backend()`
- `_prepare_step_evaluations_batch()`
- `_sync_command_chain_batch()`
- `_refresh_visual_batch()`

**Issue**: These two classes are essentially single-agent vs. multi-agent variants of the same architecture. Partial sharing already exists, but the sharing boundary remains unfocused, so further infrastructure modifications still require cross-referencing between the two files.

**Suggestion**: Extract a `_BaseWorldBatchInfrastructure` mixin that contains all shared functions (approximately 25). The two concrete classes would inherit it and retain only their divergent logic.

---

### 5.6 `EGI` and `InstrumentState` Field Overlap

**Review Conclusion**: `Partially valid`

**Locations**:
- `EGI` defined in [src/components/systems/navigation.h](../../../../src/components/systems/navigation.h)
- `InstrumentState` defined in [src/components/physics/instruments.h](../../../../src/components/physics/instruments.h)

The two components have 12 semantically overlapping fields:

| Data | `EGI` | `InstrumentState` |
|---|---|---|
| Latitude | `lat_deg` | `lat_deg` |
| Longitude | `lon_deg` | `lon_deg` |
| NED velocity | `vn/ve/vd_mps` | `vn/ve/vd_mps` |
| Barometric altitude | `alt_baro_m` | `alt_baro_m` |
| Radar altitude | `alt_radar_m` | `alt_radar_m` |
| Heading/Pitch/Roll | `heading/pitch/roll_deg` | `heading/pitch/roll_deg` |

`NavigationSystem` writes to `EGI`, then `InstrumentSystem` copies from `EGI` to `InstrumentState`. The field overlap objectively exists. However, `EGI` also carries navigation states like `drift_lat_m`, `drift_lon_m`, `drift_alt_m`, `time_since_last_gps_fix`, `position_uncertainty_m`, `gps_available`, etc.; thus it is not merely a “meaningless duplicate container” but rather a navigation intermediate cache and state surface.

**Suggestion**: In the short term, clarify the responsibility boundary of `EGI`. If it is intended to model GPS outages/drift/navigation confidence, it should be retained and documented. If it will not carry these semantics in the long run, consider either sinking it into `InstrumentState` or extracting a read-only projection layer.

**2026-05-16 Execution Update**: This iteration completed the first batch of boundary integration:
- Explicitly designated `EGI` as a navigation cache/state surface;
- Added `InstrumentNavigationProjection` and `project_egi_to_instrument_navigation()` in `src/components/systems/navigation.h`;
- `src/systems/physics/instrument_system.h` no longer manually performs `EGI -> InstrumentState` field copying and ground speed/ground track derivation, but instead consumes the navigation projection results uniformly;
- Added runtime regression to verify that instrument navigation readings still match the projection output from `EGI`.

This step did not delete the overlapping fields, but it made the responsibility boundary between “state surface” and “pilot-facing projection surface” explicit, facilitating future evaluation of whether to further collapse or retain the two-layer structure.

---

### 5.7 `instrument_system.h` and `default_control_model.cpp` Duplicate Ground Track Computation

**Locations**:
- [src/systems/physics/instrument_system.h:44-49](../../../../src/systems/physics/instrument_system.h) — `inst_ground_track_deg_from_velocity()`
- [src/models/air/default_control_model.cpp:57-65](../../../../src/models/air/default_control_model.cpp) — `ground_track_deg_from_velocity()`

Both functions do exactly the same thing: compute ground track from `Velocity`, falling back to heading angle at low speeds. Only variable names differ (`horiz_speed` vs `v_h`).

**Suggestion**: Extract the ground track computation into `components/basic/common.h` as a shared utility function.

**2026-05-16 Execution Update**: The current version has unified `Math::ground_track_deg_from_velocity()` in `src/components/basic/common.h`.
- `src/systems/physics/instrument_system.h` now accesses the common helper through a thin wrapper `inst_ground_track_deg_from_velocity()`;
- `src/models/air/default_control_model.cpp` directly calls `Math::ground_track_deg_from_velocity()`;
- The navigation projection in `src/components/systems/navigation.h` also reuses the same primitive.

Thus the core duplicate logic for this item has been integrated. Future simplification should focus on removing the local thin wrapper name rather than dealing with algorithm divergence.

---

### 5.8 `world_to_body` Rotation Matrix Duplication

**Review Conclusion**: `Partially valid`

The same attitude matrix conversion from world coordinates to body coordinates appears in at least three places with related implementations:

| File | Implementation |
|---|---|
| [src/systems/physics/aero_state_system.h:39-78](../../../../src/systems/physics/aero_state_system.h) | `world_to_body()` — full 3-axis rotation |
| [src/systems/physics/instrument_system.h:83-124](../../../../src/systems/physics/instrument_system.h) | `project_forces_to_body()` — full 3-axis rotation, but only returns ax/az |
| [src/systems/physics/aerodynamics_system.h:26-45](../../../../src/systems/physics/aerodynamics_system.h) | `get_body_right()` — partial rotation (only body Y → world) |

Among these, `world_to_body` in `aero_state_system.h` and `project_forces_to_body` in `instrument_system.h` both implement the same ψ→θ→φ Euler rotation sequence, constituting substantial duplication. `get_body_right()` in `aerodynamics_system.h` only covers a partial direction projection, not the same level. Additionally, there is a simpler `world_to_body` in the weapon effects model.

**Suggestion**: Extract `world_to_body()` and `body_to_world()` as public functions in the `Math::` namespace.

**2026-05-16 Execution Update**: This iteration completed the first batch of public extraction:
- Added `Math::world_to_body()`, `Math::body_to_world()`, and shared Euler-angle rotation coefficient helpers in `src/components/basic/common.h`;
- Connected `src/systems/physics/aero_state_system.h`, `src/systems/physics/instrument_system.h`, and `src/systems/physics/aerodynamics_system.h` to the common primitives, eliminating duplicate 3-axis rotation implementations in the main runtime;
- The simplified `world_to_body` in `src/models/weapons/default_effects_model.cpp` is retained for now, not forcibly merged with the main flight dynamics rotation primitives, to avoid introducing semantic changes in weapon effect determination.

---

### 5.9 GPU and CPU Dual-Track FlightShaping Computation

**Review Conclusion**: `Not prioritized as a current entry point`

**Locations**:
- [src/gpu/gpu_flight_shaping_runtime.h](../../../../src/gpu/gpu_flight_shaping_runtime.h) — GPU path (36-line declaration)
- [src/core/mission/runtime/reward_runtime.h](../../../../src/core/mission/runtime/reward_runtime.h) — CPU path (286-line declaration + implementation)

The GPU path explicitly declares two functions: `compute_flight_shaping_reference_cpu_batch()` and `compute_flight_shaping_experiment_batch()`. Review confirms that the current GPU path falls back to the CPU reference when CUDA is unavailable or the experiment path returns no result. This is standard verification dual-tracking, not redundancy that should be immediately removed.

---

### 5.10 Nanobind Bindings Are the Third Manual Field Mirror

**Review Conclusion**: `First batch of test reinforcement completed`

**Location**: [src/interfaces/python/bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp) (417 lines)

Every field of every C++ struct has a corresponding `.def_rw("name", &Struct::field)` line. The Nanobind bindings themselves are reasonable binding boilerplate. The problem is that, when combined with Python-side tuples like `_TASK_ORDER_FIELDS` / `_LEADER_INTENT_FIELDS` / `_PILOT_REPORT_FIELDS`, it forms a third manually maintained surface:

| Layer | Location | Lines |
|---|---|---|
| C++ definition | `src/components/tasking/*.h` | authoritative |
| Nanobind bindings | `src/interfaces/python/bindings_command.cpp` | ~180 lines of field mappings |
| Python clone tuples | `gym_envs/leader_env.py` | ~100 lines of field names |

An omission in any of the three locations leads to field loss.

**Suggestion**: Lowest-cost solution — use `dir(ef_py.TaskOrder())` reflection on the Python side instead of hardcoded tuples (nanobind objects support `dir()`). Or write unit tests that automatically detect whether the Python mirror is complete after each C++ struct modification.

**2026-05-16 WP-C Execution Update**: The current version has added the first batch of binding-maintenance regression:
- Kept the existing `.def_rw(...)` binding pattern in Nanobind, without introducing a new auto-binding system;
- Continued coverage of reflection consistency for `TaskOrder / LeaderIntent / PilotReport` in [tests/leader/test_two_ship_contract_fields.py](../../../../tests/leader/test_two_ship_contract_fields.py);
- Added [tests/runtime/bindings/test_bindings_command_surface.py](../../../../tests/runtime/bindings/test_bindings_command_surface.py) to directly pin the public field surfaces of `MissionCommand / PilotAction / CommPacket`, reducing the risk of silent drift after a missed binding in `bindings_command.cpp`.

Remaining items:
- `bindings_command.cpp` remains a manually maintained surface;
- This iteration did not auto-generate the field surfaces for `MissionCommand / PilotAction / CommPacket`, only added direct regression.

---

### 5.11 `shaping.py` Deadband/Norm/Power Pattern Repeated 24 Times

**Location**: [gym_envs/scenario_loader/execution_runtime/shaping.py](../../../../gym_envs/scenario_loader/execution_runtime/shaping.py) (316 lines)

The same reward term computation pattern — take parameter deadband → compute error → divide by norm → raise to power → clip → call `add_reward_term` — appears in the following scenarios 24 times:

- Altitude error penalty + altitude hold reward (2 times)
- Speed error penalty + speed hold reward (2 times)
- Roll/pitch/yaw rate/sideslip angle attitude penalties (4 times, reduced to ~30 lines via tuple iteration but still repeats norm/power/clip logic)
- G-load deviation penalty (1 time)
- Runway centerline penalties (including `_m` variant, `_barrier` variant, `_penalty` variant — 6 times total)
- Departure centerline penalty + departure centerline reward + departure track penalty + departure track reward (4 times)

Of the total 316 lines, approximately 180 are variants of the same pattern.

**Suggestion**: Extract a `_compute_error_penalty(cfg, prefix, state_value, add_reward_term)` helper function to unify the convention for the five keys: `name/deadband/norm/power/clip`.

---

### 5.12 `mission_obs_taxonomy.py` Field List Fully Expanded

**Review Conclusion**: `Valid`

**Location**: [python/mission_obs_taxonomy.py](../../../../python/mission_obs_taxonomy.py) (189 lines)

21 field names appear repeatedly across multiple observation mode lists:

| Occurrence Count | Example |
|---|---|
| 6 modes | `command_code`, `target_heading_deg`, `target_altitude_m`, `target_speed_mps` |
| 4 modes | `dist_m`, `bearing_rel_deg`, `cdi_norm`, ... (10 nav_v2 fields) |
| 3 modes | `form_offset_x/_y/_z_m` |
| 2 modes | `self_role_code`, `relative_slot_code`, ... (4 role fields) |

The field list is a fully expanded pattern of "copy the previous level + add new fields", rather than a "base list + incremental" composition pattern. If a field name is modified in `nav_v2`, it must be changed in 4 places.

**Suggestion**: Replace full expansion with incremental definitions:
```python
_NAV_V2_FIELDS = ["selected_steerpoint", "steerpoint_mode_code", ...]
_FORM_EXTRA = ["form_offset_x_m", "form_offset_y_m", "form_offset_z_m"]
_ROLE_EXTRA = ["self_role_code", ...]
MISSION_OBS_FIELD_NAMES_BY_NAME = {
    "nav_v2_formation_role_v1": _BASE_FIELDS + _NAV_V2_FIELDS + _FORM_EXTRA + _ROLE_EXTRA,
}
```

**2026-05-16 Execution Update**: The current version has been refactored according to this suggestion.
- `python/mission_obs_taxonomy.py` has been split into incremental lists: `_MISSION_OBS_BASIC_FIELDS`, `_MISSION_OBS_NAV_V2_EXTRA_FIELDS`, `_MISSION_OBS_FORMATION_EXTRA_FIELDS`, `_MISSION_OBS_ROLE_EXTRA_FIELDS`, `_MISSION_OBS_COOPERATIVE_TAKEOFF_EXTRA_FIELDS`, etc.;
- `MISSION_OBS_FIELD_NAMES_BY_NAME` is now constructed by combining "base fields + incremental fields" for each mode, instead of continued full expansion;
- `tests/runtime/mission/test_mission_obs_taxonomy.py` adds direct regression checks for mode encoding, field layout, key indices, and dimensions.

This item is effectively resolved in the current code. Future work will mainly involve maintaining the compositional definition as new mission obs modes are added.

---

### 5.13 `env_config.py` args/env_cfg Merge Pattern Repeated 8 Times

**Review Conclusion**: `Partially valid`

**Location**: [python/env_config.py:26-90](../../../../python/env_config.py)

In `resolve_env_settings()`, the same kind of merge pattern does appear repeatedly, but saying "8 completely identical occurrences" is a slight simplification. Currently, it is more accurate to say that 8 items (`include_proprio`, `action_mode`, `mission_obs_mode`, `visual_downsample`, `visual_update_interval`, `execution_step_runtime_mode`, `step_info_mode`, `flight_shaping_backend`) follow the same merge pattern, plus a slightly specialized `include_visual` branch.

Typical pattern:

```python
X = getattr(args, "X", None)
if X is None:
    X = type(env_cfg.get("X", default))
else:
    X = type(X)
```

**Suggestion**: Extract `_merge_config_value(args, attr_name, env_cfg, cfg_key, default, coerce_fn)` to eliminate duplication.

**2026-05-16 Execution Update**: The current version has completed the first batch of integration.
- `python/env_config.py` now includes `_merge_config_value()` and `_merge_optional_config_value()`, and the merging logic for `include_proprio`, `action_mode`, `mission_obs_mode`, `visual_downsample`, `visual_update_interval`, `execution_step_runtime_mode`, `step_info_mode`, and `flight_shaping_backend` has been switched to the shared helpers;
- `include_visual` retains its independent branch because it additionally carries the specialization of inferring the visual extractor from `train_config`, which is not appropriate to forcibly unify just for form's sake;
- This iteration added `tests/runtime/core/test_env_config.py`, directly covering the lower/trim behavior of optional merge, empty-string clearing, and illegal-value error branches, filling the gap where previously only indirect verification via the contract runner existed.

Thus, the repetition pattern for this item has been significantly converged. What remains is a reasonable specialization branch, not a large area of copied logic.

---

### 5.14 `simulation_kernel_command_api.cpp` Entity Validation Boilerplate 20 Times

**Review Conclusion**: `Partially Established`

**Location**: [src/core/engine/simulation_kernel_command_api.cpp](../../../../src/core/engine/simulation_kernel_command_api.cpp) (365 lines)

The file does indeed contain a large number of repetitive ECS entity lookup + validation patterns, but the count of "20 places" is overstated. According to the current implementation, `auto e = ecs.entity(entity_id);` appears approximately 14 times in this file, with explicit invalid guard / warn around 11 places.
```cpp
auto e = world.entity(entity_id);
if (!e.is_valid()) return;
```

Similar boilerplate also exists in `observation_api.cpp`, but these should be treated as an extension scope for a unified abstraction later, not conflated with the local count in `command_api.cpp`.

**Recommendation**: Extract a `resolve_entity(world, entity_id)` or a more lightweight `with_valid_entity(...)` helper. Eliminate the high-frequency boilerplate in `command_api.cpp` first, then decide whether to generalize to observation / visual APIs.

**Update Executed on 2026-05-16**: The current version has implemented the first batch of helper extraction within `src/core/engine/simulation_kernel_command_api.cpp`:
- Unified invalid entity guard / warn;
- Unified world time reading and command-link queue determination;
- Kept the helper scope limited to the `command_api.cpp` file, not spreading to observation / visual APIs.

This entry can be considered as having completed the first phase of consolidation; whether to extend to other kernel API files requires separate evaluation, not further expansion within the current round.

---

### 5.15 `execution_runtime/mainline.py` ↔ `shadow.py` Parallel Verification Double Write

**Location**:
- [gym_envs/scenario_loader/execution_runtime/mainline.py](../../../../gym_envs/scenario_loader/execution_runtime/mainline.py) (741 lines, 37KB)
- [gym_envs/scenario_loader/execution_runtime/shadow.py](../../../../gym_envs/scenario_loader/execution_runtime/shadow.py) (225 lines)

`shadow.py` implements a C++ `ExecutionEpisodeController` path with the same semantics as `mainline.py`, used to verify that the C++ compilation path and Python interpretation path produce identical results. This is a standard "shadow testing" pattern in the deep learning compiler domain, but means each step is computationally executed twice.

**Recommendation**: Once the C++ `ExecutionEpisodeController` path has been fully validated by all scenario contracts (as `scenario_contract_runner.py` is already doing), the shadow path can be marked as deprecated and removed.

---

### 5.16 `training_callbacks.py` 1120 Lines and `world_model/dreamer.py` 1282 Lines

**Review Conclusion**: `Not Taken as Current Entry Point`

**Location**:
- [python/training_callbacks.py](../../../../python/training_callbacks.py) (1120 lines, 28 functions)
- [python/world_model/dreamer.py](../../../../python/world_model/dreamer.py) (1282 lines, 13 functions)

These are reasonably large files (training logic and Dreamer model) rather than redundancy issues. However, `training_callbacks.py` contains multiple callback types (logging, checkpointing, curriculum scheduling, evaluation scheduling, early stopping) and could be split into submodules like `callbacks/logging.py`, `callbacks/checkpoint.py`, `callbacks/curriculum.py`, etc.

---

## 6. Summary of Impact After Review

| Review Conclusion | Entry | Description |
|---|---|---|
| `Established` | `3.1` | Duplicate registration, low risk, can be cleaned up immediately |
| `First Batch of Boundary Reinforcement Completed` | `3.2` | `Mass` remains the authoritative runtime decomposition of mass; `MassProperties` synchronization boundary has been tightened |
| `Established` | `3.3` | Three sets of data chain delivery logic can be templated directly |
| `Established` | `3.4` | Python manual field mirroring risks silent drift; field completion, enum clone compatibility, and reflection validation first batch fixes have been completed |
| `Established` | `4.3` | `leader_env.py` has obvious mixed responsibilities |
| `First Batch of Consolidation Completed` | `5.4` | Scripted controller has extracted a minimal shared skeleton; control laws remain locally implemented |
| `Established` | `5.7` | Ground track calculation has genuine duplication |
| `Established` | `5.12` | Mission obs taxonomy maintenance method is prone to drift |
| `Partially Established` | `4.1` | Legacy chain scope is genuine, but throttle/brake fallback first batch of duplicate logic has been shared and consolidated |
| `Partially Established` | `4.2` | Front section has wrapper redundancy; rear section still bears real bridge logic |
| `Partially Established` | `4.4` | Air/naval parallel interfaces are reasonable; suitable for extracting commonality but should not be forcibly merged |
| `Partially Established` | `5.5` | Two vec envs are still maintained in parallel, but helper sharing has begun |
| `Partially Established` | `5.6` | Overlap between EGI and InstrumentState remains, but first batch boundary consolidation of "state surface -> instrument projection surface" has been completed |
| `Partially Established` | `5.8` | Main runtime consumer has completed first batch of commonization; simplified variant in weapon effects model is retained |
| `First Batch of Test Reinforcement Completed` | `5.10` | Binding boilerplate is still manually maintained, but key public surface now has direct regression coverage |
| `Partially Established` | `5.13` | Merge pattern duplication is real, but not "8 identical occurrences" |
| `Partially Established` | `5.14` | Entity guard boilerplate is real, but the count is exaggerated |
| `Not Taken as Current Entry Point` | `5.1` | Compatibility umbrella header; keep for now |
| `Not Taken as Current Entry Point` | `5.2` | More like reserved interface not fully implemented |
| `Not Taken as Current Entry Point` | `5.9` | GPU/CPU dual track is a verification path |
| `Not Taken as Current Entry Point` | `5.16` | Module size issue, not redundancy |

## 7. Subsequent Recommendations

### 7.1 Immediate Actions

1. Delete duplicate registration of `MassProperties` (`3.1`).
2. Template the three sections of duplicate logic in `command_link_system` (`3.3`).
3. Extract `ground_track_deg_from_velocity()` into a public header file (`5.7`).
4. Rewrite the field list definition in `mission_obs_taxonomy.py` using incremental composition (`5.12`).
5. Extract `_merge_config_value()` / `_merge_optional_config_value()` in `env_config.py` (`5.13`).

### 7.2 Second Batch to Advance

1. Continue compressing remaining consumers in the `MovementCommand` compatibility chain, and assess when to mark as `[[deprecated]]` (`4.1`).
2. Continue evaluating the long-term structure of `EGI` vs. `InstrumentState`: maintain "navigation state surface + instrument projection surface", or further sink to retain only read-only projection helpers (`5.6`).
3. Evaluate whether the simplified `world_to_body` in `src/models/weapons/default_effects_model.cpp` should converge toward the common rotation primitive or remain as an independent approximation model (`5.8`).

### 7.3 Items to Defer

1. Entries related to `scenario_loader` mainline refactoring (`5.3`, `5.11`, `5.15`) continue to advance along the existing mainline; no duplicate trimming in this round.
2. Keep `common_core_profile.py` and `air/naval_profile.py` in the bridge + strategy structure for now, avoiding premature abstraction reshaping during parallel air/naval development.
3. Retain the GPU/CPU FlightShaping reference path until the GPU path and verification toolchain stabilize before evaluating removal.
