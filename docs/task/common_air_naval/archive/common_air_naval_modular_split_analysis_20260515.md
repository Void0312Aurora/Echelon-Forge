<!-- Machine-translated draft generated on 2026-05-18 from docs/task/common_air_naval/common_air_naval_modular_split_analysis_20260515.zh.md. Review before treating this file as authoritative. -->

# Common / Air / Naval Module Splitting Analysis

Status: Analysis Completed, Code Splitting Not Yet Started.  
Date: `2026-05-15`

## 1. Background

The project's current execution mainline still focuses on air combat / flight missions, but the goal has been explicitly expanded to joint operations, with naval warfare as the second priority direction.

The current problem is not the "lack of Navy enumeration", but rather:

- The design intent of `joint/common core` already exists.
- Concrete DTOs, runtime helpers, tests, and tooling still heavily adopt `air-first` semantics.
- If naval logic is directly overlaid on the current structure, it will easily lead to a second parallel air combat stack instead of a mergeable multi-service mainline.

Therefore, before formally implementing the parallel development of naval warfare / joint layer, a module splitting analysis oriented toward `common + air + naval` must be completed.

## 2. Scope of This Document

This document focuses on the pre-splitting analysis of the following chains:

- `src/components/tasking/*`
- `src/components/command/*`
- `src/interfaces/python/bindings_command.cpp`
- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`
- `python/testing/scenario_contract_runner.py`
- `tests/contracts/*`
- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`

This document does not directly authorize code implementation; subsequent implementation shall follow the accompanying freeze plan document.

## 3. Confirmed Findings

### 3.1 The `tasking/command` layer is still a mixed DTO

Although the most core C++ DTO layer has been split into `tasking` and `command` directories, many structures still mix `common core` with `air specialization` in the same header file:

- [src/components/tasking/tasking_enums.h](../../../../../src/components/tasking/tasking_enums.h)
- [src/components/tasking/task_order.h](../../../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h)
- [src/components/command/mission_command.h](../../../../../src/components/command/mission_command.h)

Typical mixed signals:

- Fields like `ServiceProfile / TaskFamily / TacticalUnitType / CommandRelationship` have joint layer commonality.
- `LeaderPhase / RecoveryApproachType / Takeoff* / RunwaySlotPosition / FormationRole / WingmanSlot` are clearly air-combat-specific semantics.
- `TaskOrder`, `LeaderIntent`, `MissionCommand` simultaneously carry common relationship fields and air combat task execution details.

### 3.2 `MissionCommand` is the highest risk splitting point

[src/components/command/mission_command.h](../../../../../src/components/command/mission_command.h) is not just a passive DTO; it has directly entered:

- Aerodynamic / autopilot control interpretation
  - [src/models/air/default_control_model.cpp](../../../../../src/models/air/default_control_model.cpp)
- Instrument and mission runtime
  - [src/systems/physics/instrument_system.h](../../../../../src/systems/physics/instrument_system.h)
  - [src/core/mission/episode/detail/episode_transition_runtime.cpp](../../../../../src/core/mission/episode/detail/episode_transition_runtime.cpp)
- Batch runtime and facade export
  - [src/runtime/contracts/world_batch_contracts.h](../../../../../src/runtime/contracts/world_batch_contracts.h)
  - [src/runtime/facade/runtime_facade_types.h](../../../../../src/runtime/facade/runtime_facade_types.h)

This means `MissionCommand` cannot be directly refactored as the first step, otherwise it could easily disrupt:

- Control behavior
- Episode state / codec
- Runtime facade
- Python bindings
- Downstream training / evaluation scripts

### 3.3 `TaskOrder / LeaderIntent / PilotReport` are better suited as first splitting candidates

Compared to `MissionCommand`, the following structures, although widely used, currently assume more "setting/export/synchronization" responsibilities, with behavioral coupling lower than `MissionCommand`:

- [src/components/tasking/task_order.h](../../../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h)

They have already entered:

- `SimulationKernel` / `WorldBatchRuntime` setting and reading APIs
- Python bindings
- Runtime facade
- `leader_env`, `scenario_loader`, `scenario_contract_runner`

However, the main risk is still field attribution and semantic mixing, not tight-loop control logic itself. Therefore, they are more suitable as the first batch of "structural layer splitting".

### 3.4 The Python "common" semantic layer is still `air-first`

The following Python modules nominally carry `common` or assume loader/runtime glue responsibilities, but their implementations are still clearly air-biased:

- [python/rl/tasking/common_core_profile.py](../../../../python/rl/tasking/common_core_profile.py)
- [python/rl/tasking/leader_tasking.py](../../../../python/rl/tasking/leader_tasking.py)
- [gym_envs/scenario_loader/core.py](../../../../gym_envs/scenario_loader/core.py)
- [gym_envs/leader_env.py](../../../../gym_envs/leader_env.py)

Confirmed issues include:

- `common_core_profile.py` defaults to `AirForce`, `Aircraft`, and hardcodes air combat task families, recovery, takeoff, runway fields, etc.
- `leader_tasking.py` simultaneously mixes:
  - Synchronization bridging of `TaskOrder / LeaderIntent / PilotReport`
  - Air combat `MissionCommand` translation
  - Air combat phase/task manager
- `scenario_loader.py` is responsible for loading/state mirroring, but also directly carries air combat task runtime semantics.
- `leader_env.py` hardcodes air-specific field lists, phase mapping, reward/observation semantics in the environment shell.

This means the Python layer should not continue to extend via `if Navy` in the future, but should introduce profile dispatch / semantics adapter.

### 3.5 `tests/contracts` is the most suitable executable surface for initial decoupling

Analysis shows that `tests/contracts` is more suitable than `tests/runtime` as the verification surface for the first batch of splitting.

Reasons:

- `scenario_contract_runner` already has some common-core field validation and application logic.
- However, current contract payloads still carry many air combat semantics.
- They can be split with relatively low cost into:
  - `common core` contracts
  - `air` contracts
  - future `naval` contracts

In contrast, `tests/runtime` deeply depends on:

- cooperative takeoff
- runway / recovery
- formation role
- mission observation vector
- landing / terminal logic

Therefore runtime tests are better suited as a later migration surface.

### 3.6 `tools/eval` and `tools/diagnostics` are mostly still air semantics

The `eval` / `diagnostics` layer has been consolidated at the entry and common base level, but task semantics still mainly revolve around air combat/flight missions:

- `eval_task.py` currently has task families like `stable_flight / takeoff_roll / centerline / waypoint_nav`
- `eval_sb3.py` contains air combat artifacts such as cooperative formation role / final command code
- Cooperative trajectory diagnostic clearly revolves around takeoff, route, recovery, and formation

Therefore:

- Shared CLI / JSON / benchmark base can be retained and reused.
- Task taxonomy and metric semantics should be split after profile stabilization.

### 3.7 Existing Naval hooks mainly stay at the taxonomy layer

The current repository already has some usable naval warfare entry points, but most are still "type entry points", not runtime capability entry points:

- [src/components/basic/common.h](../../../../../src/components/basic/common.h) already has `UnitType::Ship`
- [src/components/tasking/tasking_enums.h](../../../../../src/components/tasking/tasking_enums.h) already has `ServiceProfile::Navy`
- [docs/standards/services/navy.md](../../../standards/services/navy.md) already has US Navy profile design notes

However, no mature naval runtime consumer has been found, indicating that naval warfare is currently better started from:

- Documentation
- Schema
- Common field contracts
- Profile-specific contracts

Rather than directly modifying the air combat tight-loop runtime.

## 4. Splitting Principles

### 4.1 Split by `common + air + naval`, not by `air + ship`

One of the most important conclusions of this topic:

- The `tasking` / `command` layer is not a platform layer.
- They describe semantics for joint layer, service layer, and mission organization layer.
- Therefore, they should not be directly split into `air` and `ship`.

Recommended hierarchy:

1. `common core`
2. `air profile`
3. `naval profile`

Where:

- `ship` is more suitable as a platform/execution layer object.
- `naval` is suitable as the splitting unit for the mission organization and control method layer.

### 4.2 First split "attribution" and "boundary", then behavior

The focus of the first splitting phase should be:

- File attribution
- Enum attribution
- Field attribution
- Python dispatch seam
- Contract seam

Not:

- Immediately rewriting control laws
- Immediately rewriting scenario formats
- Immediately turning `MissionCommand` into a completely new nested object

### 4.3 Compatibility layer must be explicitly retained for a period

Currently, many paths depend on old file names, old struct names, and Python binding symbols. Therefore, the first batch of splitting must by default retain:

- Compatibility umbrella headers
- Old binding export names
- Compatibility interpretation layer for old contract/JSON fields

Otherwise, the splitting itself will be overwhelmed by a large amount of mechanical migration noise.

### 4.4 Contract-first, then runtime/tooling

Recommended order:

1. Documentation/field attribution freeze
2. DTO/enum splitting
3. Python common/profile dispatch
4. `tests/contracts`
5. `tests/runtime`
6. `tools/eval` / `tools/diagnostics`
7. Maintained scenarios / training configs

## 5. Proposed Target Attribution

### 5.1 Fields/enums that can be considered `common core`

Proposed attribution to `common`:

- `ServiceProfile`
- `TaskFamily`
- `TacticalUnitType`
- `CommandRelationship`
- `AuthorityScope`
- `AssigneeKind`
- `CoordinationMode`
- `task_group_id`
- `supported_node_id`
- `supporting_node_id`
- `role_code`
- `relative_slot_code`
- `recovery_site_id`
- Fields related to `authority / issuer / assignee / parent node`

### 5.2 Fields/enums that should be attributed to `air`

Proposed attribution to `air`:

- `TaskType` current air combat task families
- `StationType`
- `LeaderPhase`
- `RecoveryApproachType`
- `TakeoffProcedureType`
- `TakeoffClearanceState`
- `RunwaySlotPosition`
- `FormationRole`
- `WingmanSlot`
- `FormationMode`
- `WingmanCommandMode`
- `recovery_runway_id`
- Current interpretation of `recovery_base_id`
- `takeoff_*`
- `runway_slot_id`
- `lead_aircraft_id`
- `formation_*`
- `wingman_*`
- `support_sector_id`

### 5.3 `CommMsgType` is suitable for extraction as a neutral communication layer

`CommMsgType` is currently defined in [src/components/tasking/pilot_report.h](../../../../../src/components/tasking/pilot_report.h), but is also used by `ActionCommand`, datalink, and track systems.

Therefore, it is recommended to later migrate to a neutral location, for example:

- `src/components/command/comm_message.h`
or
- `src/components/common/comm_message.h`

To avoid the structural smell of `command` depending backward on `tasking`.

## 6. Proposed Target Directory Structure

The following structure is the recommended direction, not required to be fully implemented in the first phase:

```text
src/components/tasking/common/
  core_tasking_enums.h
  task_order_core.h
  leader_intent_core.h
  pilot_report_core.h

src/components/tasking/air/
  air_tasking_enums.h
  task_order_air.h
  leader_intent_air.h
  pilot_report_air.h

src/components/tasking/naval/
  naval_tasking_enums.h
  task_order_naval.h
  leader_intent_naval.h
  pilot_report_naval.h

src/components/command/common/
  comm_message.h
  mission_command_core.h

src/components/command/air/
  mission_command_air.h
  pilot_action_air.h
  legacy_command_air.h
```

During the compatibility period, retain:

- `src/components/tasking/tasking_enums.h`
- `src/components/tasking/task_order.h`
- `src/components/tasking/leader_intent.h`
- `src/components/tasking/pilot_report.h`
- `src/components/command/mission_command.h`

as umbrella / compatibility headers.

## 7. Risks and Constraints

### 7.1 Binding and Python API risk

[src/interfaces/python/bindings_command.cpp](../../../../../src/interfaces/python/bindings_command.cpp) is currently a flat binding surface. Directly changing struct names, field names, or enum export names will simultaneously break:

- Python runtime
- Tests
- Tools
- Contract runner

Therefore, the first batch of splitting should by default not change user-visible binding names.

### 7.2 `MissionCommand` tight-loop risk

`MissionCommand` currently directly enters control laws and mission runtime, making it a high-risk behavioral surface. It is suitable for later splitting, not as a first-phase refactoring target.

### 7.3 Mission observation / checkpoint compatibility risk

Paths like `scenario_loader`, `universal_env`, `leader_env` have already solidified:

- Mission observation vector dimensions
- Cooperative slot / formation role interpretation
- Command code meaning

If profile dispatch is not well designed, it will directly affect:

- Existing checkpoints
- Existing training configs
- Existing smoke/runtime tests

### 7.4 Contract runner compatibility risk

`scenario_contract_runner` currently nominally supports common-core fields, but still defaults to using air-shaped runtime fixtures and mission semantics. During splitting, the contract runner's profile assumptions must be simultaneously cleaned up.

## 8. Splitting Priority Summary

Highest priority:

- Documentation and field attribution freeze
- `tasking_enums` common/air splitting design
- `TaskOrder / LeaderIntent / PilotReport` splitting design
- Dispatch seam design for `common_core_profile.py` and `leader_tasking.py`

Medium priority:

- `scenario_loader.py`
- `leader_env.py`
- `scenario_contract_runner.py`
- `tests/contracts/unit/comm/*`

Lower priority:

- `MissionCommand`
- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`
- `scenarios/*`
- `examples/config/*`

## 9. Current Conclusion

This topic is not suitable to start directly from "implementing naval warfare modules". Instead, the following must be completed first:

1. Structural boundary freeze for `common / air / naval`;
2. Splitting design for the chain `tasking/command -> Python profile/loader -> contracts/tests`;
3. Clarify the migration order: `MissionCommand` later, `TaskOrder/LeaderIntent/PilotReport` earlier.

See the accompanying freeze plan:

- [Common / Air / Naval Module Splitting Freeze Plan](../common_air_naval_modular_split_plan_20260515.zh.md)
