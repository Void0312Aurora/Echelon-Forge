# Runtime Workflow and Contract Baseline

Language:
- English canonical: `runtime_workflow_and_contract_baseline.md`
- Chinese companion: [runtime_workflow_and_contract_baseline.zh.md](runtime_workflow_and_contract_baseline.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/runtime_workflow_and_contract_baseline.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-08-08`

Status: maintained runtime workflow and contract baseline, subordinate to the
[strict simulation architecture baseline](simulation_system_architecture_design.md).

This document fixes the maintained workflow boundary between:

- scenario/task input orchestration in Python
- command/behavior bridge logic in the scenario loader
- pure computation in the C++ mission runtime
- episode/controller state assembly and roundtrip

It is the standards entrypoint for "how the current code actually works" when
that answer affects naming, ownership, or contract design.

## Purpose

The repository no longer benefits from treating the runtime as a single opaque
"environment step". The maintained workflow has distinct layers, and standards
work needs to respect them.

This document therefore answers:

1. Which stage owns what kind of data?
2. Which seams are stable enough to standardize?
3. Which responsibilities must not leak across the Python/C++ boundary?

## Maintained Workflow

The current high-level workflow is:

`scenario JSON -> load/compile -> normalize task + mission command -> behavior/command-chain update -> runtime step inputs -> C++ mission/runtime products -> episode/controller roundtrip`

In repository terms, the main stages are:

1. scenario loading and normalization
2. command-chain and behavior update
3. step-evaluation input assembly
4. pure mission/runtime computation
5. product application, status tracking, and episode roundtrip

## Stage 1: Scenario Loading And Normalization

Primary code entrypoints:

- [gym_envs/scenario_loader/loading.py](../../../gym_envs/scenario_loader/loading.py)
- [gym_envs/scenario_loader/core.py](../../../gym_envs/scenario_loader/core.py)

This stage owns:

- scenario JSON loading and compilation handoff
- randomization seed preparation
- active roster and world layout setup
- `task_order` and `mission_command` normalization
- waypoint cache materialization
- initial target resolution and scenario-side metadata setup

This stage does not own:

- command delivery semantics
- pure reward/termination computation
- doctrine ownership of field names

## Stage 2: Behavior And Command-Chain Update

Primary code entrypoints:

- [gym_envs/scenario_loader/behavior_runtime/command_chain.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain.py)
- [gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py](../../../gym_envs/scenario_loader/behavior_runtime/command_chain_owner.py)
- [gym_envs/scenario_loader/behavior_runtime/behavior_phase_owner.py](../../../gym_envs/scenario_loader/behavior_runtime/behavior_phase_owner.py)
- [gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py](../../../gym_envs/scenario_loader/behavior_runtime/post_waypoint_transition.py)

This stage owns:

- `MissionCommand` and `CommandLink` bridge behavior
- phase transitions and command-chain ownership
- synchronization of mission-command state into the kernel/runtime boundary
- pending post-waypoint or landing transition activation

Stable contract implication:

- behavior phase ownership and command-chain ownership are first-class seams
- command generation is not the same thing as command execution
- command replacement must clear or preserve state intentionally, not by
  accident

## Stage 3: Step-Evaluation Input Assembly

Primary code entrypoints:

- [gym_envs/scenario_loader/mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py)
- [gym_envs/scenario_loader/step_evaluation.py](../../../gym_envs/scenario_loader/step_evaluation.py)
- [gym_envs/scenario_loader/navigation_runtime/](../../../gym_envs/scenario_loader/navigation_runtime)

This stage owns:

- mission-observation input assembly
- route/waypoint/nav products
- step-info input assembly
- safety and shaping input preparation before pure runtime computation

This stage is still a bridge layer. It may consume truth, instrument, runway,
route, and mission-command data together. That does not make all of those terms
common-core ontology terms.

## Stage 4: Pure C++ Mission/Runtime Computation

Primary code entrypoints:

- [src/core/mission/README.md](../../../src/core/mission/README.md)
- [src/core/mission/runtime/mission_runtime.cpp](../../../src/core/mission/runtime/mission_runtime.cpp)
- [src/core/mission/runtime/execution_step_runtime.cpp](../../../src/core/mission/runtime/execution_step_runtime.cpp)
- Frame contract [execution_frame_runtime.h](../../../src/core/mission/runtime/execution_frame_runtime.h); implementation owner [execution_episode_runtime.cpp](../../../src/core/mission/runtime/execution_episode_runtime.cpp)
- [src/core/mission/runtime/execution_observation_runtime.cpp](../../../src/core/mission/runtime/execution_observation_runtime.cpp)
- [src/core/mission/runtime/termination_runtime.h](../../../src/core/mission/runtime/termination_runtime.h)

This stage owns:

- mission observation products
- step-info products
- reward/termination/objective products
- execution-frame and execution-step runtime products
- deterministic pure computation over prepared inputs

This stage must remain free of:

- Python binding concerns
- scenario JSON parsing
- episode controller state import/export
- ad hoc loader-side command/phase ownership logic

## Stage 5: Product Application And Episode Roundtrip

Primary code entrypoints:

- [gym_envs/scenario_loader/execution_runtime/mainline.py](../../../gym_envs/scenario_loader/execution_runtime/mainline.py)
- [src/core/mission/episode/](../../../src/core/mission/episode)
- [tests/runtime/execution/test_execution_episode_controller.py](../../../tests/runtime/execution/test_execution_episode_controller.py)
- [tests/runtime/execution/test_execution_episode_state.py](../../../tests/runtime/execution/test_execution_episode_state.py)

This stage owns:

- applying runtime products back onto maintained episode/controller state
- reward breakdown persistence
- termination/status tracking
- import/export and roundtrip of episode state

It should not be merged back into pure runtime kernels.

## Stable Contract Objects

The following objects are stable enough to be treated as maintained workflow
contracts:

- `TaskOrder`
- `LeaderIntent`
- `MissionCommand`
- `CommandLink`
- `DataLink`
- mission observation mode contracts
- execution-step/frame runtime products
- termination-reason and reward-breakdown outputs

The current tests under [tests/runtime/](../../../tests/runtime/README.md) are the
main regression surface that keeps these contracts honest.

## Field Visibility Rules

Not every runtime field is visible in every observation mode.

Current maintained mission-observation contracts distinguish modes such as:

- `basic`
- `nav_v1`
- `nav_v2`
- `nav_v2_formation_v1`
- `nav_v2_formation_role_v1`
- `nav_v2_cooperative_takeoff_v1`
- `air_combat_c2_roe_v1`
- `air_combat_c2_roe_v2`
- `naval_screen_station_v1`

Standards implication:

- field visibility is mode-dependent
- formation fields are not automatically common fields
- takeoff/runway semantics remain air specialization even when they appear in a
  common runtime object
- air-combat C2/ROE fields belong to air specialization even when they mirror
  shared command-context identifiers
- naval screen/station fields belong to naval specialization

## Non-Goals

This document does not define:

- the full sensor/track/IFF contract
- the full weapon/seeker/fuze/damage contract
- platform physics implementation details

Those should be standardized in their own shared or specialized documents as
the repository converges them.

## Related Documents

- [Scenario Configuration Guide](../../operations/howto/scenario_configuration_guide.md)
- [Joint Command and Modeling Baseline](../../domains/joint/standards/command_and_modeling_baseline.md)
- [Joint Command-Link and Reporting Baseline](../../domains/joint/standards/command_link_and_reporting_baseline.md)
- [Simulation Conventions](simulation_conventions.md)
- [src/core/mission/README.md](../../../src/core/mission/README.md)
