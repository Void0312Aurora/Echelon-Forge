# P8 Collaborative Execution Pipeline Discovery and Plan

Language:
- English canonical: `p8_cooperative_execution_pipeline_findings_and_plan.md`
- Chinese companion: [p8_cooperative_execution_pipeline_findings_and_plan.zh.md](p8_cooperative_execution_pipeline_findings_and_plan.zh.md)

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/learning/work/issues/p8_cooperative_execution_pipeline_findings_and_plan.md`
Owner: `learning/cooperative-training`
Last verified: `2026-08-08`
Content status: migrated pre-execution discovery snapshot; no active task is
authorized by this page.

Status: draft issue recording the `2026-05-11` facility inventory, design
constraints, and candidate next cuts. The original "in progress" wording is
historical; activation requires a newly frozen task boundary.

Document positioning:

- This document is not a new refactoring authorization form, but a discovery record and pre-execution plan for the P8 collaborative training direction.
- The goal is to reuse existing runtime / batch / leader-tasking facilities, avoiding making "dual-aircraft" a new dedicated silo.
- In the first phase of P8, the only minimum acceptance scenario is dual-aircraft cruise; the implementation form must be oriented towards `N` controllable platforms in the same world.

## I. Core Conclusion

P8 should not build a new pipeline serving only `TwoShipEnv`.

The current project already has most of the base needed for collaborative execution:

- `RuntimeFacade` / `WorldBatchRuntime` already use `WorldEntityRef(world_index, entity_id)` as the batch access unit.
- Batch runtime already supports batch writing of `PilotAction`, `MissionCommand`, `TaskOrder`, `LeaderIntent`, `PilotReport` to any entity.
- Batch runtime already supports batch reading of `AgentObservation`, `InstrumentState` and command/tasking/report objects from any entity.
- `ScenarioRuntime` can already spawn multiple entities in the same world and retains the mapping `entities: name -> entity_id`.
- `ScriptedC2TaskManager` / `RuleBasedLeaderPhaseManager` already provide scripted task/leader layer basics.
- `LeaderBatchedVecEnv` and `LeaderWorldBatchExecutionRuntimeGroup` have already verified the scheduling concept of "high-level window + batch execution policy inference + shared WorldBatchRuntime".

The real gap is in the Python training/environment wrapper layer:

- The existing `UniversalEnv` / `WorldBatchVecEnv` mainly organizes execution training by "one `agent_id` per world".
- The existing observation builder is centered on a single agent and has not yet organized multiple controllable members within the same world into the same collaborative batch.
- The existing training entry points only have two `agent_layer` types: `execution` / `leader`, and have not yet explicitly expressed "multi-entity collaborative execution within the same world".

Therefore, the first cut of P8 should fill:

```text
The roster / refs / observation / action mapping layer for multiple controllable entities within the same world
```

Rather than adding a new dedicated dual-aircraft environment.

## II. Design Boundaries

### 2.1 The Leader Layer is Not the Lead Aircraft

In this project, the "leader layer / element lead layer" is the tactical intent generation layer, not equivalent to the flight execution of the lead aircraft.

The correct chain is:

```text
C2 / TaskOrder
  -> Coordination Director / Element Lead Layer
  -> per-platform LeaderIntent / MissionCommand
  -> per-platform execution policy
  -> PilotAction
  -> WorldBatchRuntime step
```

Therefore:

- The leader layer can be scripted.
- The lead aircraft itself should still be flown by the execution layer policy or execution controller.
- The wingman is also flown by the same execution layer pipeline.

### 2.2 Dual-Aircraft is Just `N=2`

P8 phase 1 uses dual-aircraft cruise for verification, but the interface should not have hard-coded only-adapt-to-dual-aircraft.

Recommended abstractions:

- `world_index`
- `entity_id`
- `entity_name`
- `team_id` / `element_id`
- `role_code`
- `formation_role_id`
- `relative_slot_code`
- `reference_entity_name` / `reference_entity_id`
- `policy_route`

Dual-aircraft is two members of an element; four-aircraft is more roster members and more slot assignments.

These fields belong to roster / routing / logging metadata, not equivalent to execution policy input. P8-A should not directly stuff them into the observation of the execution layer for the convenience of shared models.

### 2.3 Policy Pipeline Priority Over Shared Model

A shared execution model is one configuration for policy routing, not the core goal of P8.

The same pipeline should support:

- All members share one execution policy.
- Different policies based on role.
- Some members scripted, some RL.
- Subsequent replacement of the scripted coordination director with RL or a planner.

### 2.4 Observations Must Adhere to Real-World Availability Principles

The sole admission criterion for execution layer input is: it is information a real pilot could receive via brief, cockpit instruments, mission system, radio, visual, radar, IRST, RWR, or data link.

Training convenience, shared model convenience, reward calculation convenience, debug convenience are not reasons to admit fields into policy input. The execution layer policy is not an observer of the simulation kernel, nor a consumer of trainer internal state.

Information allowed into policy should be explainable as:

- Visible on own cockpit/instruments.
- Mission or formation instructions received via mission computer / data link / radio.
- Assigned formation slot and mission brief.
- Relative information about friendly aircraft obtainable via visual, sensor, or data link.

Directly disallowed from policy:

- Unconditional global truth coordinates and velocities.
- Perfect errors used internally by reward.
- Future instructions, internal script state, trainer privileged state.
- States of other platforms not modeled through sensor/data link/mission system.
- Engineering labels designed only to distinguish shared model branches, but which a real pilot would not receive in that form.

## III. Existing Facility Inventory

### 3.1 C++ runtime / facade

Reusable facilities:

- `RuntimeFacade`
  - `set_pilot_actions_batch`
  - `set_mission_commands_batch`
  - `set_task_orders_batch`
  - `set_leader_intents_batch`
  - `set_pilot_reports_batch`
  - `export_observation_packet`
  - `step_execution_batch`
- `WorldBatchRuntime`
  - Batch command / observation / step helpers for any `WorldEntityRef`.
  - Batch queries for sensor / visual / comm candidates.

Design implication:

- P8 does not need to build a new "multi-aircraft runtime" from the bottom up.
- It should expand multiple members within the same world into a batch of refs, then reuse existing batch APIs.

### 3.2 Scenario runtime

Reusable facilities:

- In scenario, `entities` can declare multiple platforms.
- `apply_world_layout_to_kernel` and `load_compiled_scenario_batch` return the complete `entities` mapping.
- The existing `agent_id` is only a compatibility entry for the first `is_agent`, not implying that a scenario can only control one entity.

Gaps:

- An active controllable roster needs to be defined in configuration or scenario metadata.
- It needs to be clear which entities enter the policy batch and which are scripted / passive.

### 3.3 Python batch / leader facilities

Reusable facilities:

- `WorldBatchVecEnv` already has batch reset, command synchronization, action distribution, step, observation readback paths.
- `_RuntimeFacadeAdapter` already centrally encapsulates facade and compatible runtime access.
- `LeaderBatchedVecEnv` already has `ExecutionBatchPredictor` that can do one policy forward for a batch of execution observations.
- `LeaderWorldBatchExecutionRuntimeGroup` already has scheduling experience with shared world-batch execution runtime.
- `LeaderWindowRuntimeAdapter` already separates high-level decision window from low-level execution rollout.

Gaps:

- `WorldBatchVecEnv` currently organizes policy batches by env/world granularity, not by `WorldEntityRef` granularity.
- The execution layer observation builder currently constructs single-aircraft input.
- The train config does not yet have a `cooperative_execution` entry point.

## IV. Execution Layer Input Link Inventory and Augmentation Principles

This section first inventories existing execution policy input links, then discusses whether fields need to be added; it does not discuss privileged evaluation quantities used for reward/logging.

Key constraints:

- The first version must not stuff full tasking/formation data model fields into the execution layer for training convenience.
- Take the current actual execution layer policy input of approximately `26` scalars as the budget baseline; P8-A does not expand according to the full observation dict exportable by runtime.
- P8-A first reuses the existing `MissionCommand`, `contacts`, `visual`, sensor/datalink links; only if existing real-world information products cannot reach policy, then add minimal fields.
- New inputs must first be defined as information products a real pilot would receive, then enter policy; not the reverse: pick fields for training first, then retroactively construct a real-world explanation.
- Precise errors used by the trainer internally for reward are not entered into policy by default.

### 4.1 Own Platform Observations: Reuse Existing Inputs

Continue to retain existing execution layer inputs:

- `instruments`
- `contacts`
- `rwr`
- `mission`
- `visual`, if training configuration enabled
- `proprio`, if training configuration enabled

These correspond to own cockpit, sensors, and mission guidance products.

### 4.2 Mission Command Link

P8-A first version does not add "role number" or "team number". Roles should be determined by the task/formation pipeline; the execution policy only receives the task instructions, formation instructions, and sensor information a pilot would actually receive.

The existing `MissionCommand` already has an execution layer command entry:

```cpp
int formation_id;
double form_offset_x;
double form_offset_y;
double form_offset_z;
```

Therefore, P8-A's first priority is not to create a new `station_*` input, but to check and unblock the existing command -> mission observation link. Currently, `MissionObservationInputs` / `compute_mission_observation` only outputs `command_code`, heading, altitude, speed, and nav tail; it has not yet exposed `MissionCommand.form_offset_x/y/z` to the execution policy.

It is recommended to only include the existing `MissionCommand` formation offset into the `mission` block:

| Input | Meaning | Real-World Source | Required |
| --- | --- | --- | --- |
| `formation_id` | Formation/pattern instruction number, if provided by real mission system | Mission brief / Mission system / Radio | Optional |
| `form_offset_x` | Longitudinal offset of assigned slot relative to reference/formation coordinates | Formation instruction | Required |
| `form_offset_y` | Lateral offset of assigned slot relative to reference/formation coordinates | Formation instruction | Required |
| `form_offset_z` | Altitude offset of assigned slot relative to reference/formation coordinates | Formation instruction | Conditionally Required |

Explanation:

- These fields already exist in `MissionCommand` / `LeaderIntent` / Python binding; a parallel input should not be designed.
- `form_offset_*` is formation/slot instructions a pilot would receive, not real-time errors.
- The lead aircraft can receive `0,0,0` or element-level commands; there is no need to give the policy a `formation_role`.
- Wingman left/right, trail, echelon, etc., are naturally expressed by offsets; no need to add `wingman_slot_id` or `relative_slot_code`.

### 4.3 Contacts / Radar / Datalink Current Status and Gaps

The existing C++ `TrackData` already contains:

```cpp
id, range, azimuth, elevation, closing_speed, time_since_update, source, classification
```

But the current execution observation `contacts` token only exports:

```text
range, azimuth, elevation, closing_speed, time_since_update
```

This means the policy can see target motion quantities, but cannot see track source and identification results. For collaborative formation, the reference aircraft should come from a real information source:

- Visual: visual ARB already has `team` channel, can see visual products like bearing/depth/radial velocity of friendly aircraft in field of view.
- Radar/Sensor: `DefaultSensorModel` produces bearing/range/elevation/closing/signal, and enters `TrackDatabase`.
- Data Link: `TrackManagerSystem` already supports `ReportContact` messages to generate DataLink tracks.
- IFF/Identification: `TrackData.classification` exists, but the current execution layer contact vector does not expose it.

Therefore, the first version should not add parallel `ref_*` fields; the priority should be to evaluate whether to expose existing `TrackData.source` / `classification` as real avionics products in the contact token. Without friendly identification/data link sources, the model cannot magically know which contact is lead/wingman.

### 4.4 Inputs Not Added in the First Version

The following inputs, even if they have real-world sources, will not create new independent fields in the first version to avoid bypassing existing links:

- `formation_mode_id`
  - Real-world source: Radio/Mission system.
  - Reason for deferral: P8-A only does cruise hold, mode can be fixed; mode state stays in mission/leader pipeline, not directly stuffed into policy.
- `wingman_command_mode`
  - Real-world source: Radio/Data link.
  - Reason for deferral: First version only does hold slot, not rejoin/support/abort switching; to express, it should first be mapped to a specific command or offset of `MissionCommand`.
- Independent `ref_*` fields
  - Reason for deferral: Reference aircraft information should preferably come from `contacts`, visual ARB, sensor/datalink track. `closing_speed` is already in the contact token; reference aircraft altitude difference can be expressed by `elevation` / visual products.

### 4.5 Inputs Explicitly Excluded from First Version Policy

The following quantities do not enter P8-A first version execution policy:

- `team_id_norm`
- `element_id`
- `role_code`
- `formation_role`
- `relative_slot_code`
- `wingman_slot_id`
- `formation_template_id`
- `formation_contract_id`
- `formation_error_m`
- `slot_lateral_error_m`
- `slot_longitudinal_error_m`
- `slot_vertical_error_m`
- Reference aircraft position / velocity in global coordinates.
- Perfect friendly state not modeled through sensor, visual, or datalink.

These can remain in scenario/config, command/tasking/report, or reward/logging, but not as first version execution policy inputs.

### 4.6 Own Platform Task Command Input

The existing `mission` block already has task observations like command code / heading / altitude / speed. P8 needs to ensure each member receives its own per-platform command:

- Lead aircraft: tracks element-level cruise/route commands.
- Wingman: under the same element intent, additionally includes slot/reference platform constraints.

It is not recommended to share the same mission vector among all team members and let the model guess the role.

### 4.7 Quantities Not Entering Execution Policy, Only for Reward/Logging

The following quantities can be used for reward, diagnostics, contracts, visualization, but by default do not directly enter policy:

- `formation_error_m`
- `slot_lateral_error_m`
- `slot_longitudinal_error_m`
- `slot_vertical_error_m`
- Minimum separation statistics.
- Perfect friendly position/velocity in global world coordinates.
- Team-level success/failure internal state.

If in the future an error is desired as policy input, it must first be modeled as a real cockpit product, such as formation cue / datalink steering cue, with clear source, latency and availability written.

In other words, whether something can enter policy is not determined by its usefulness for training, but by whether the pilot can truly receive that information product.

## V. Next Execution Plan

The next step does not start with "adding dual-aircraft inputs", but with verifying the availability of existing links. Each cut must answer two questions:

- Where does this information come from for a real pilot?
- Can the existing link already deliver this information to the execution policy?

### P8-A1: Facility Verification Probe

Goal:

- Do not create a large new abstraction; first prove existing runtime can handle multi-entity control in the same world.

Content:

- Construct a minimal dual-aircraft air cruise scenario.
- Spawn two Blue aircraft in the same world.
- Construct two `WorldEntityRef`s from the `entities` mapping.
- Batch-read `ObservationBatchPacket`.
- Batch-write two `PilotAction`s.
- Step and verify both aircraft states changed.

Acceptance:

- Probe or pytest passes under `.venv` + `PYTHONPATH=build-workshop`.
- No dedicated C++ new interfaces beyond `agent_id`.

Recorded progress in the cited snapshot:

- Supplemented `tests/world_batch/test_world_batch_runtime.py::test_world_batch_runtime_controls_multiple_entities_within_same_world`.
- Passed under `.venv` + `PYTHONPATH=build-workshop`.
- Current conclusion: `WorldBatchRuntime`'s existing `WorldEntityRef -> get_*_batch / set_pilot_actions_batch / step_batch` links are sufficient to support multi-entity execution control in the same world; a dedicated dual-aircraft runtime does not need to be added first.

### P8-A2: Existing Mission Command Formation Field Link Verification

Goal:

- Verify that `MissionCommand.formation_id` / `form_offset_x/y/z` can travel from the leader/tasking pipeline into the kernel.
- Determine whether they are already included in the `mission` observation of the execution policy.

Content:

- Construct a `LeaderIntent` or `MissionCommand` with `form_offset_x/y/z`.
- Send via existing `set_mission_commands_batch` / `build_kernel_mission_command`.
- Read the kernel mission command for the corresponding entity, verify field fidelity.
- Construct the current `mission` observation, confirm current status: `compute_mission_observation` currently only outputs command/heading/altitude/speed/nav tail.

Acceptance:

- Form a contract/probe that locks in the fact: "existing command fields exist but observation not exposed".
- Do not change the default `mission_obs_mode` to avoid breaking P5/P7 frozen models.

Recorded progress in the cited snapshot:

- Supplemented `tests/runtime/mission/test_leader_tasking_runtime.py::test_build_kernel_mission_command_maps_formation_offsets`, confirming that the `LeaderIntent -> MissionCommand` mapping already includes `formation_id / form_offset_x/y/z`.
- Supplemented `tests/world_batch/test_world_batch_runtime.py::test_world_batch_runtime_mission_command_roundtrip_preserves_formation_offsets`, confirming that when using the existing command-link method, the kernel mission command roundtrip preserves formation offsets.
- Supplemented `tests/runtime/mission/test_mission_runtime.py::test_loader_mission_observation_current_contract_ignores_formation_offsets`, confirming that the current `MissionObservationInputs` / `compute_mission_observation` still only exposes command/heading/altitude/speed/nav tail, has not yet exposed formation offsets to the execution policy.

Additional notes:

- Running `tests/runtime/mission/test_mission_runtime.py` as a whole file under the current `.venv` is blocked by `gymnasium` dependency triggered by existing `UniversalEnv` tests; the targeted contract test added for P8-A2 itself passes.
- This phase still does not modify the default `mission_obs_mode` and old observation shapes.

### P8-A3: Minimal Extension of Cooperative Mission Observation

Goal:

- Only in the cooperative execution entry point, deliver realistically receivable formation instructions to the policy.

Suggestions:

- Add an explicit opt-in mission observation mode or configuration switch, e.g., `nav_v2_formation_v1`.
- In this mode, append existing `MissionCommand`'s `form_offset_x/y/z`, and optionally `formation_id`.
- Keep default dimensions of `basic` / `nav_v1` / `nav_v2` unchanged.

Acceptance:

- Single-aircraft old training configuration observation shapes unchanged.
- Cooperative execution configuration can get per-platform formation command.
- Tests must explain that these fields originate from mission brief / mission system / radio formation instructions.

Entry condition:

- After P8-A1 / P8-A2 completed, then do minimal opt-in extension.
- First cut only supplements existing `mission` link, does not introduce new parallel `station_*` observation block.

Recorded progress in the cited snapshot:

- Added explicit opt-in mission observation mode: `nav_v2_formation_v1`.
- Using the existing `mission_cmd -> MissionObservationInputs -> compute_mission_observation` link, `form_offset_x / form_offset_y / form_offset_z` are connected in this mode.
- Output dimensions of old modes `basic / nav_v1 / nav_v2` remain unchanged; new mode dimension is `17 = 4 + 10 + 3`.
- Explicitly guaranteed that when "there is no route guidance but formation instructions exist", the `nav` tail is zeroed and the `formation` tail is retained, not zeroed together.
- Python loader / env configuration / GPU batch export / CUDA mission packing are also connected synchronously.
- Supplemented targeted contract tests covering:
  - New mode appends formation offsets;
  - When no route guidance, formation offsets are still retained;
  - Old `nav_v2` mode continues to ignore formation offsets;
  - `nav_v2_formation_v1` loader / batch export shape and value contracts.

Current conclusion:

- P8-A3 is complete and maintains compatibility with the default observation shape for frozen single-aircraft models of P5/P7.
- The next phase should not stuff engineering labels into the `mission` block; subsequent cuts should turn to A4/A6, continuing to verify and supplement existing real information links for `contacts / visual / datalink`.

### P8-A4: Contacts / Visual / Radar Identification Link Verification

Goal:

- Do not add parallel `ref_*` fields; first confirm whether existing sensor products are sufficient to identify friendly/reference aircraft.

Content:

- Construct a dual-aircraft same-world scenario, ensure sensor/visual visibility.
- Check whether `TrackData.source` / `classification` in `AgentObservation.contacts` are correctly set.
- Check whether the current execution contact token discards `source` / `classification`.
- Check whether the visual ARB `team` channel can stably express visual clues for friendly aircraft.

Acceptance:

- If contact identification is sufficient, extend only the contact token; do
  not add a parallel reference input.
- If it is insufficient, repair the sensor/datalink/track-manager chain rather
  than exposing reference-aircraft truth to the policy.

Recorded progress in the cited snapshot:

- Tests recorded that the execution contact token remained five columns and
  omitted `TrackData.source` / `classification`.
- The visual ARB team channel was recorded as distinguishing friendly,
  hostile, and neutral contacts.
- The snapshot records `TrackManagerSystem` and `DataLinkFusionSystem`
  integration plus focused live-contract coverage for radar and shared-track
  provenance.

Recorded next priority: A4 was treated as complete in the cited snapshot and
A6 was selected to continue the reality-bounded contacts/visual/datalink input
contract without introducing parallel `ref_*` fields.

## Migration Boundary

The Chinese companion retains additional historical P8-A5 through P8-A8
planning detail. Those sections are not copied into this canonical draft as
current authority because their implementation state was not reverified in
the 2026-08-08 owner migration. Any of them requires a newly frozen task and
fresh acceptance evidence before activation.
