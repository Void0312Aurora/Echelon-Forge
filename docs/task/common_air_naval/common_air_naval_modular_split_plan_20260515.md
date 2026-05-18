<!-- Machine-translated draft generated on 2026-05-18 from docs/task/common_air_naval/common_air_naval_modular_split_plan_20260515.zh.md. Review before treating this file as authoritative. -->

# Common / Air / Naval Module Split Freeze Plan

Status: `2026-05-15` frozen execution version; `WP0 / WP1 / WP2 / WP3` completed, `WP4` completed first phase shared base / air adapter / dispatch seam and second phase profile back-connection / compatibility landed and passed focused acceptance, `WP5` completed, `WP6` completed, `WP7` started and completed first two batches of skeleton / contract / public DTO-binding-roundtrip landed, `WP8` completed `MissionCommand common + air` compatible split, consumer/json symmetry wrap-up and focused regression acceptance.
Document positioning:

- This document freezes a module split plan around `common / air / naval`.
- The goal of this round is to first stabilize boundaries, compatibility layers, and verification surfaces, without directly introducing a complete naval combat runtime.
- This document does not authorize semantic rewrites beyond the scope of the work packages; all implementations shall be accepted per work package.

Verification criteria: For implementations involving Python / nanobind / runtime, use the repository virtual environment and local build artifacts for acceptance by default, i.e.:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop \
  ./.venv/bin/python -m pytest
```

Do not use the system Python as the final acceptance criteria.

## I. Goals

The goal of this plan is not to "immediately create a naval training mainline", but to establish a mergeable structural foundation for subsequent parallel development of air and naval warfare.

The core issues to be resolved in this round:

1. Separate `joint/common core` and `air specialization` from the current mixed DTO.
2. Establish a landing point for a future `naval profile`, but without forcing the complete implementation of a naval runtime in this round.
3. Freeze the compatible split route of the `tasking/command -> Python runtime -> contracts/tests` chain.
4. Avoid continuing to pile new semantics through `if Navy` within the current `air-first` structure.

## II. Current Assessment

According to the supporting analysis document [Common / Air / Naval Module Split Analysis](./archive/common_air_naval_modular_split_analysis_20260515.zh.md), the current repository already has the following conditions:

- The standard documentation layer can already support the modeling route of `joint/common core + service profile + specialization`;
- Entry points such as `ServiceProfile::Navy` and `UnitType::Ship` already exist;
- DTOs, Python helpers, contract runners, tests and tool layers are still significantly `air-first`;
- `TaskOrder / LeaderIntent / PilotReport` are suitable as the first batch of structural split targets;
- `MissionCommand` is a high-risk tight-loop structure and should be handled later.

## III. Non-Goals

This round does not do:

- Rewriting aerodynamics or control laws.
- Directly introducing a complete naval mission runtime.
- Batch-modifying all scenario / training configs to a multi-service format.
- Disposing of old struct names, old header file names or old Python binding export names in a single effort.
- Refactoring `MissionCommand` into a brand new nested object and simultaneously rewriting all downstream consumers.
- Rewriting the existing cooperative takeoff / cruise / landing mainline behaviors.

This round allows:

- Creating new `common/air/naval` target directories and READMEs.
- Creating new compatibility umbrella headers.
- Creating new Python dispatch/helper modules.
- Structurally splitting `tests/contracts`.
- Backfilling boundaries for `docs/standards`, `docs/task` and essential `README` files.

## IV. Overall Strategy

### 4.1 Split Order

Adopt the following sequence:

1. Documentation and schema boundary freeze
2. C++ common enum / DTO core extraction
3. `TaskOrder / LeaderIntent / PilotReport` air split
4. Python profile / loader / env dispatch split
5. `tests/contracts` migration
6. `tests/runtime`, `tools/eval`, `tools/diagnostics`, scenarios/configs migration
7. `naval` profile skeleton and minimum contract landing
8. `MissionCommand` deferred refactoring

### 4.2 Compatibility Strategy

First-phase batches default to retaining:

- Old header file paths
- Old struct names
- Old Python binding export names
- Compatible interpretation layer for old scenarios / contracts

The purpose of the compatibility strategy is not to maintain a dual track for a long time, but to reduce the merge risk of each phase.

### 4.3 Directory Strategy

The target structure adopts three layers:

```text
common
air
naval
```

Not adopted:

```text
air
ship
```

Reasons:

- The `tasking/command` layer describes service/ mission organization semantics, not a single platform physical model;
- `ship` is more suitable for platform/execution layer semantics;
- `naval` is the mission/control profile layer aligned with `air`.

## V. Frozen Work Packages

### WP0: Document and Field Attribution Freeze

Goal:

- First, clearly define the boundaries of `common / air / naval`;
- Clarify which fields and enumerations must belong to `common`, and which must belong to `air`;
- Clarify that for `naval`, only a skeleton is established in this round, without directly committing to a complete runtime.

Freeze scope:

- `docs/task` this topic analysis/plan documents
- `docs/standards/joint/*`
- `docs/standards/services/*`
- `docs/standards/document_alignment_map.md`
- Essential `src/components/*/README.md`

Explicitly not done:

- Any behavioral code migration
- Any runtime semantic changes

Deliverables:

- Analysis document
- Frozen plan document
- Field/enum attribution table

Acceptance criteria:

- `common` and `air` field attributions are clear
- `naval` boundary for this round is clear
- Subsequent code implementation does not need to re-debate field attributions

Current status:

- Completed: `docs/task` analysis and plan documents landed
- Completed: `docs/standards/document_alignment_map.md`, `docs/standards/joint/command_and_modeling_baseline.md`, `docs/standards/services/navy.md`, `docs/standards/naval/README.md` boundary backfill
- Completed: `src/components/tasking/README.md` and `src/components/command/README.md` directory boundary descriptions

### WP1: Extract Common Enum and Neutral Communication Layer

Goal:

- Extract truly joint-layer common enumerations from `tasking_enums.h`;
- Move `CommMsgType` from `pilot_report.h` to the neutral communication layer.

Freeze scope:

- `ServiceProfile`
- `TaskFamily`
- `TacticalUnitType`
- `CommandRelationship`
- `AuthorityScope`
- `AssigneeKind`
- `CoordinationMode`
- `CommMsgType`

Suggested target structure:

```text
src/components/tasking/common/core_tasking_enums.h
src/components/command/common/comm_message.h
```

Compatibility requirements:

- Keep `src/components/tasking/tasking_enums.h`
- Keep compatibility for old includes in `src/components/tasking/pilot_report.h`

Explicitly not done:

- Migrating all fields of `TaskOrder` / `LeaderIntent` / `MissionCommand` in this phase

Acceptance criteria:

- C++ build succeeds
- `ef_py` binding build succeeds
- Old include path still works
- No change to existing runtime behavior

Risk notes:

- Need to synchronize `bindings_command.cpp`
- Need to be aware of dependencies on `CommMsgType` in `legacy_command.h`, datalink, track manager

Current status:

- Completed: `src/components/tasking/common/core_tasking_enums.h` extracted common enums
- Completed: `src/components/command/common/comm_message.h` hosts neutral `CommMsgType`
- Completed: Compatibility includes still maintained externally via `tasking_enums.h`, `pilot_report.h`, `comm.h`
- Completed: `ef_core` / `ef_py` build and focused pytest verification

### WP2: Extract Common Core of `TaskOrder / LeaderIntent / PilotReport`

Goal:

- Establish file boundaries for common/air without breaking public struct names and most downstream call methods;
- Reserve a clean landing point for subsequent `naval` extensions.

Freeze scope:

- [src/components/tasking/task_order.h](../../../src/components/tasking/task_order.h)
- [src/components/tasking/leader_intent.h](../../../src/components/tasking/leader_intent.h)
- [src/components/tasking/pilot_report.h](../../../src/components/tasking/pilot_report.h)

Suggested target structure:

```text
src/components/tasking/common/
  task_order_core.h
  leader_intent_core.h
  pilot_report_core.h

src/components/tasking/air/
  task_order_air.h
  leader_intent_air.h
  pilot_report_air.h
```

Compatibility strategy:

1. First create target files and umbrella includes.
2. Keep `TaskOrder`, `LeaderIntent`, `PilotReport` names unchanged.
3. Keep flat DTO compatibility period for downstream.

Explicitly not done:

- Immediately change structs to deeply nested objects
- Simultaneously rewrite all Python consumers

Acceptance criteria:

- `SimulationKernel` / `WorldBatchRuntime` / `RuntimeFacade` build passes
- `bindings_command.cpp` exports maintain compatibility
- `tests/leader/test_common_core_semantics.py`
- `tests/world_batch/test_world_batch_runtime.py`
  related field smoke passes

Risk notes:

- `runtime facade`, `world_batch_contracts` directly expose these DTOs
- Include dependency direction must be controlled when migrating old fields

Current status:

- Completed: `TaskOrder`, `LeaderIntent`, `PilotReport` split into `common/*_core.h` and `air/*_air.h`
- Completed: Old umbrella headers continue to expose original struct names externally, and maintain flat field access through `Core + Air` compatibility shells
- Completed: `bindings_command.cpp` compatibility export verified
- Completed: `tests/leader/test_common_core_semantics.py`, `tests/runtime/facade/test_runtime_facade.py` and `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` focused acceptance

### WP3: Extract Air-Only Enums and Air Extension

Goal:

- Move air-combat-specific task families, phases, recovery, takeoff, runway, formation fields from common structures clearly down to `air`.

Freeze scope:

- `TaskType`
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

And clarification of attribution for the following air-only fields:

- `recovery_runway_id`
- `recovery_base_id`
- `takeoff_*`
- `runway_slot_id`
- `lead_aircraft_id`
- `formation_*`
- `wingman_*`
- `support_sector_id`

Explicitly not done:

- Adding naval counterpart implementation
- Changing cooperative air mainline behavior

Acceptance criteria:

- `tasking_enums.h` degenerates to umbrella / compatibility header
- New `air_tasking_enums.h` added
- Existing air combat runtime behavior remains unchanged

Risk notes:

- Many formation / takeoff / landing tests in `tests/runtime` depend on these enums

Current status:

- Completed: Added `src/components/tasking/air/air_tasking_enums.h` as air-only enum owner
- Completed: `tasking_enums.h` degenerated to `common + air` compatibility umbrella
- Completed: `task_order_air.h`, `leader_intent_air.h`, `mission_command.h` and `bindings_command.cpp` changed to explicitly depend on air enum owner
- Completed: `ef_core` / `ef_py` build passes, and `tests/leader/test_common_core_semantics.py`, `tests/leader/test_two_ship_contract_fields.py`, `tests/runtime/facade/test_runtime_facade.py`, `tests/runtime/mission/test_mission_runtime.py`, `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` focused acceptance passes

### WP4: Python Profile/Dispatch Split

Goal:

- Transition the Python side from "pseudo common, actually air-first" to explicit dispatch.

Freeze scope:

- `python/rl/common_core_profile.py`
- `python/rl/leader_tasking.py`
- `gym_envs/scenario_loader.py`
- `gym_envs/leader_env.py`
- `python/rl/multi_agent_runtime.py`
- `python/testing/scenario_contract_runner.py`

Suggested target structure:

```text
python/rl/profile/common_core_base.py
python/rl/profile/air_profile.py
python/rl/tasking_bridge.py
python/rl/tasking_air_adapter.py
gym_envs/tasking_runtime_dispatch.py
gym_envs/leader_semantics_adapter.py
```

In-phase split strategy:

1. First extract shared base for enum/default/plumbing.
2. Then extract air profile helper.
3. Then introduce dispatch seam for loader / env.
4. Temporarily do not introduce complete naval adapter, only keep interface.

Explicitly not done:

- Immediately modify mission observation vector structure
- Immediately convert existing checkpoints to new semantics

Acceptance criteria:

- Shared / air logic separation in `common_core_profile`
- Shared bridge and air adapter separation in `leader_tasking`
- `scenario_loader` / `leader_env` can use air profile through adapter/dispatch
- Existing air scenarios smoke do not degrade

Risk notes:

- Mission observation dimensions and command code compatibility are most sensitive
- Old checkpoint / eval tool chain depends on existing air-first interpretation

Current status:

- Completed: Added `python/rl/profile/common_core_base.py`, hosting shared enum/default/plumbing helper
- Completed: Added `python/rl/profile/common_core_defaults.py`, hosting shared common-core default/inference helper
- Completed: Added `python/rl/profile/air_profile.py`, hosting air task-family/task-type, route/recovery and kernel mission-command helper
- Completed: Added `python/rl/tasking_air_adapter.py` and `python/rl/tasking_bridge.py`, establishing default air adapter and profile dispatch seam
- Completed: `gym_envs/scenario_loader.py`, `gym_envs/leader_env.py`, `python/testing/scenario_contract_runner.py` changed to use default air profile via dispatch
- Completed: air semantics and shared default/inference in `python/rl/common_core_profile.py` are now hosted via the `profile` submodule, while old export surface is retained as compatibility shell
- Completed: `infer_route_ref_id`, `infer_recovery_*`, `build_kernel_mission_command` in `python/rl/leader_tasking.py` are now hosted via `air_profile`, while old entry points and `ef_py` patch compatibility are maintained
- Completed: `python/rl/tasking_air_adapter.py` clearly aggregates common-core defaults/spec from `common_core_profile` and air semantics from `air_profile`
- Completed: `./.venv/bin/python -m py_compile` covers `common_core_profile.py`, `leader_tasking.py`, `tasking_air_adapter.py`, `tasking_bridge.py` and `python/rl/profile/*`
- Completed: `tests/leader/test_common_core_semantics.py`, `tests/leader/test_task_order_randomization.py`, `tests/leader/test_two_ship_contract_fields.py`, `tests/runtime/mission/test_leader_tasking_runtime.py`, `tests/runtime/facade/test_runtime_facade.py`, `tests/runtime/mission/test_mission_runtime.py` and `tests/world_batch/test_world_batch_runtime.py -k command_chain_roundtrip` focused acceptance passed (`53 passed` + `1 passed`)
- Not completed: further physical migration of `RuleBasedLeaderPhaseManager` / `ScriptedC2TaskManager` and `_apply_task_order_overrides`; dispatch transformation of `multi_agent_runtime.py` and wider contract/runtime entry points

### WP5: Migrate `tests/contracts` to Common-First

Goal:

- Transform `tests/contracts` into the first executable verification surface truly organized by `common / air / future naval`.

Freeze scope:

- `python/testing/scenario_contract_runner.py`
- `tests/contracts/unit/comm/*`
- `tests/contracts/chain/*`

Suggested direction:

- `common core` contracts only verify:
  - `service_profile`
  - `task_family`
  - `tactical_unit_type`
  - `command_relationship`
  - `authority_scope`
  - `task_group_id`
  - `supported/supporting`
  - `role_code`
  - `coordination_mode`
  - `recovery_site_id`
- Air-specific contracts continue to stay in the `air` semantic set

Explicitly not done:

- Migrating all runtime tests in this phase

Acceptance criteria:

- `scenario_contract_runner` supports common-core contract and air contract branching
- `tests/contracts/unit/comm/*` contains common-core baselines that do not depend on runway/takeoff/formation
- Existing air contracts continue to pass

Current status:

- Completed: `python/testing/scenario_contract_runner.py` introduces common-core / air-specific assertion layering inside `task_order_and_mission_link`, old `check_kind` and old spec paths remain compatible
- Completed: `python/testing/scenario_contract_runner.py` adds two common-first unit contract entry points: `task_order_common_core` and `scenario_loader_common_core_semantics`
- Completed: `scenario_loader_mission_semantics` supports branching writing of `expected_task_order_common_core`, `expected_task_order_air` and `expected_post_transition_air`, while continuing to be compatible with old `expected_task_order` / `expected_post_transition`
- Completed: Added `tests/contracts/unit/comm/task_order_common_core_defaults.json`, providing a common-core default propagation baseline independent of runway/takeoff/formation
- Completed: Added `tests/contracts/unit/comm/scenario_loader_common_core_semantics.json`, providing scenario loader common-core normalization baseline
- Completed: `tests/runners/test_contract_batches.py --group same_process` includes the two common-first contracts, and continues to cover the old `task_order_and_mission_link.json` and `scenario_loader_mission_semantics.json`
- Completed: `./.venv/bin/python -m py_compile python/testing/scenario_contract_runner.py tests/runners/test_contract_batches.py`
- Completed: `tests/runners/test_contract_batches.py --group same_process` focused acceptance passed (4 contracts passed)
- Completed: `tests/leader/test_common_core_semantics.py` and `tests/leader/test_two_ship_contract_fields.py` focused regression passed (9 passed)
- Not completed: physical migration of air-only contracts under `tests/contracts/unit/comm/` and establishment of `unit/air` / `unit/naval` directory families; wider unit/runtime contracts still awaiting continued common-first transformation

### WP6: Adaptation of `tests/runtime`, `tools/eval`, `tools/diagnostics`

Goal:

- After the `common/air` split is stable, let the runtime tests and tooling layer follow the structured approach.

Frozen scope:

- `tests/runtime/*`
- `tools/eval/*`
- `tools/diagnostics/*`

Phase strategy:

- First adapt the shared CLI / common helper
- Then adapt the air-specific taxonomy
- This phase does not require new naval eval/diagnostic mainline

Explicitly not done:

- Immediately add a naval mission evaluation family
- Batch rewrite the cooperative diagnostics chart semantics

Acceptance criteria:

- `eval_task.py` / `eval_sb3.py` still run the air mainline
- `diagnostics` shared base remains non-regressive
- Runtime tests adapted to the field paths after common/air split

Current status:

- Done: Added [python/mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py), unifying names, `mode_code`, dimensions, and field name taxonomy for mission observation modes.
- Done: [python/env_config.py](../../../python/env_config.py), [gym_envs/universal_env.py](../../../gym_envs/universal_env.py), [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py), [tools/eval/sb3_eval_base.py](../../../tools/eval/sb3_eval_base.py), [tools/diagnostics/analyze_cooperative_observation_scales.py](../../../tools/diagnostics/analyze_cooperative_observation_scales.py) integrate the shared taxonomy, while preserving original CLI cooperative gating and runtime behavior.
- Done: Added [tests/runtime/mission/test_mission_obs_taxonomy.py](../../../tests/runtime/mission/test_mission_obs_taxonomy.py), locking the `mode_code` / dim / field layout consistency between shared taxonomy and runtime entry points.
- Done: `mission_obs_taxonomy` added a shared helper mapping field names to indices; core mission assertions in [tests/runtime/mission/test_mission_runtime.py](../../../tests/runtime/mission/test_mission_runtime.py), [tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py](../../../tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py), [tests/runtime/multi_agent/test_multi_agent_runtime.py](../../../tests/runtime/multi_agent/test_multi_agent_runtime.py) have converged from magic indices to the shared taxonomy.
- Done: `./.venv/bin/python -m py_compile` covers WP6 new and modified files.
- Done: `tests/runtime/mission/test_mission_obs_taxonomy.py`, `tests/runtime/mission/test_mission_runtime.py`, `tests/runtime/multi_agent/test_multi_agent_runtime.py`, `tests/runtime/multi_agent/test_multi_agent_benchmark.py` focused regression passes (`34 passed`).
- Done: `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`, `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`, `tests/runtime/execution/test_execution_episode_batch_prepare.py`, `tests/runtime/execution/test_execution_episode_controller.py` extended regression passes (`37 passed, 8 subtests passed`).
- Done: In the second batch of first regression, `tests/runtime/mission/test_mission_obs_taxonomy.py`, `tests/runtime/mission/test_mission_runtime.py`, `tests/runtime/multi_agent/test_multi_agent_runtime.py`, `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py` pass (`51 passed`).
- Done: In the second batch of associated regression, `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`, `tests/runtime/execution/test_execution_episode_batch_prepare.py`, `tests/runtime/execution/test_execution_episode_controller.py`, `tests/runtime/multi_agent/test_multi_agent_benchmark.py` pass (`20 passed, 8 subtests passed`).
- Done: `tests/contracts/unit/config/env_config_resolution.json` contract runs through directly.
- Done: The `mission_obs_mode` CLI selection set in `python/rl/multi_agent_benchmark.py`, `tools/diagnostics/benchmarks/visual_resolution.py`, `tools/diagnostics/benchmarks/world_batch_vec_env.py` is uniformly integrated into the shared taxonomy.
- Done: Within WP6 scope, the config/runtime/tests/eval/diagnostics shared convergence for mission observation taxonomy is closed.
- Not done: If later entering `WP7`, new profile-aware assertions and entry points for naval-specific runtime/eval/diagnostics are still needed, but this is beyond WP6.

### WP7: Naval Profile Skeleton and Minimal Contract Implementation

Goal:

- After the common/air boundaries are stable, establish a truly implementable `naval` module entry point for parallel development of naval operations.

Frozen scope:

- `docs/standards/services/navy.md`
- `docs/standards/naval/*` (if newly added)
- `src/components/tasking/naval/*`
- `tests/contracts/unit/naval/*` (if newly added)

This phase only recommends:

- Naval enum and DTO extension skeleton
- Minimal naval contract schema
- Minimal contract runner dispatch

Explicitly not done:

- Complete fleet/formation runtime
- Complete naval leader env
- Complete naval eval/diagnostic suite

Acceptance criteria:

- `naval` directory and README in place
- At least one set of profile-specific contracts executable
- Does not affect existing air mainline

Current status:

- Done: Added skeleton for `src/components/tasking/naval/README.md`, `naval_tasking_enums.h`, `task_order_naval.h`, `leader_intent_naval.h`, `pilot_report_naval.h` as future naval DTO extension landing points.
- Done: Added `python/rl/profile/naval_profile.py` and `python/rl/tasking/naval_adapter.py`, and made `python/rl/tasking/bridge.py` perform profile-aware dispatch for `tasking_profile = naval` / `service_profile = Navy`.
- Done: `python/rl/tasking/common_core_profile.py` now has naval-aware common-core defaulting paths, capable of maintaining minimal naval semantics like `Navy + Escort + Screen + CommandNode` for `task_order / leader_intent / pilot_report`.
- Done: Added `tests/contracts/unit/naval/task_order_naval_profile_defaults.json` and `tests/contracts/unit/naval/scenario_loader_naval_common_core_semantics.json`; both minimal naval contracts pass execution.
- Done: Added `tests/leader/test_naval_profile_semantics.py`, which passes acceptance together with existing common-core/runtime regression.
- Done: `TaskOrder / LeaderIntent / PilotReport` have officially integrated `TaskOrderNaval / LeaderIntentNaval / PilotReportNaval`, no longer just standalone skeleton header files.
- Done: `bindings_command.cpp` now exports `NavalWarfareRole` / `NavalStationType`, and exposes naval fields such as `warfare_role_code`, `officer_in_tactical_command`, `naval_station_type`.
- Done: Clone whitelist in `gym_envs/leader_env.py`, `tests/leader/test_naval_contract_fields.py`, `tests/world_batch/test_world_batch_runtime.py` have completed binding/clone/roundtrip verification for naval fields.
- Not done: Complete naval leader/runtime/eval/diagnostics have not started; subsequent work should expand incrementally on this skeleton.

### WP8: MissionCommand Refactoring Deferred

Goal:

- After the common/air/naval structural layer and Python dispatch are stable, then handle the common/air layering of `MissionCommand`.

Frozen scope:

- `src/components/command/mission_command.h`
- `src/models/air/default_control_model.cpp`
- `src/core/mission/episode/detail/*`
- `src/systems/physics/instrument_system.h`
- `bindings_command.cpp`

Suggested direction:

- `mission_command_core.h`
- `mission_command_air.h`
- Compatible with `mission_command.h`

Explicitly not done:

- Introducing complete naval execution command in this phase

Acceptance criteria:

- Common / air boundary of `MissionCommand` is clear
- Existing air control / episode / instrument semantics do not regress
- Codec / equality / facade export compatibility period is clear

Risk note:

- This phase is the highest-risk phase in the entire chain
- Must only be entered after previous work packages are stable

Current status:

- Done: Added `src/components/command/common/mission_command_core.h` carrying common fields: `cmd_heading_deg`, `cmd_altitude_m`, `cmd_speed_mps`, `command_code`, `route_ref_id`, `assigned_target_id`, `authorization_to_fire`, `active`.
- Done: Added `src/components/command/air/mission_command_air.h` carrying air-only fields: recovery, takeoff, formation offset, etc.
- Done: `src/components/command/mission_command.h` changed to a compatibility umbrella header, continuing to expose the flat `MissionCommand` name and field access.
- Done: `bindings_command.cpp` can continue exposing existing flat `MissionCommand` fields without changing export names; Python side remains compatible.
- Done: Added `tests/runtime/mission/test_mission_command_split_semantics.py`, covering binding field exposure and direct-kernel roundtrip.
- Done: `gym_envs/scenario_loader/runtime_state.py`, `src/core/mission/episode/detail/mission_command_codec.cpp`, `src/core/mission/episode/detail/episode_transition_runtime.cpp` have completed consumer/json symmetry for `MissionCommand`; fields like `formation_*`, `assigned_target_id`, `authorization_to_fire`, `recovery_approach_type` (common/air) maintain fidelity in episode/runtime-state roundtrip.
- Done: `python/rl/profile/air_profile.py` corrected accidental overwrite of mission-level `MissionCommand` fields by zero-valued `leader_intent`, ensuring consistency between loader mission command and kernel command construction.
- Done: Focus regression passes: `tests/runtime/mission/test_leader_tasking_runtime.py`, `tests/world_batch/test_world_batch_runtime.py`, `tests/runtime/execution/test_execution_episode_state.py`, `tests/runtime/execution/test_execution_episode_controller.py`, `tests/runtime/facade/test_runtime_facade.py`, `tests/runtime/mission/test_mission_runtime.py`, `tests/runtime/multi_agent/test_cooperative_world_batch_vec_env.py`, `tests/world_batch/test_world_batch_vec_env.py`.
- Not done: `MissionCommand` has not yet entered the `naval` execution command layering; only `common + air` structure and compatibility layer are frozen in this phase.

## VI. Phase Dependencies

Dependency order:

```text
WP0
 -> WP1
 -> WP2
 -> WP3
 -> WP4
 -> WP5
 -> WP6
 -> WP7
 -> WP8
```

Notes:

- `WP2` and `WP3` can partially interleave, but field ownership freezing must be completed first.
- `WP4` should not be earlier than `WP2/WP3`; otherwise, Python dispatch will lack a stable landing point.
- `WP8` must be done last.

## VII. Unified Acceptance Requirements

Each code phase should by default complete one or more of the following verification:

- `cmake --build build-workshop --target ef_core ef_py -j2`
- `./.venv/bin/python -m py_compile ...`
- `./.venv/bin/python -m pytest -q tests/contracts ...`
- `./.venv/bin/python -m pytest -q tests/runtime ...`

If a phase only involves documentation, code verification can be skipped, but it must be explicitly stated "no code touched".

## VIII. Document Constraints

This document is the only phase planning document for this topic.

Subsequent advancement requirements:

- Prioritize backfilling the status of corresponding work packages in this document.
- If supplementary special research is needed, auxiliary documents can be added.
- Auxiliary documents must not again assume the responsibility of parallel phase planning.

## IX. Current Frozen Conclusions

Current frozen conclusions are as follows:

1. This topic adopts `common + air + naval`, not `air + ship`.
2. `TaskOrder / LeaderIntent / PilotReport` are split first, `MissionCommand` is split later.
3. Python layer adopts the dispatch / adapter route, not continuing to pile on `if Navy`.
4. `tests/contracts` migrate before `tests/runtime`.
5. `naval` first batch only does schema / contract skeleton, does not directly promise a full runtime.
