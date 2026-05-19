# WP4-D/E Policy, AgentRole, and Python Mirror Alignment Notes

Status: `2026-05-19` discovery notes. Documentation-only; no C++ or Python
runtime surface changes.

Language:

- English canonical: `wp4_policy_binding_alignment_notes_20260519.md`
- Chinese companion:
  [wp4_policy_binding_alignment_notes_20260519.zh.md](wp4_policy_binding_alignment_notes_20260519.zh.md)

Inputs reviewed:

- [WP4-D/E policy binding cluster](wp4_policy_binding_cluster_20260519.md)
- [WP4 facade alignment](facade_alignment_wp4_20260519.md)
- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- `python/rl/runtime/*`
- `python/rl/control/*`
- `gym_envs/*`
- `src/interfaces/python/bindings_runtime.cpp`

## 1. Classification Vocabulary

| Status | Meaning for WP4-D/E |
|--------|---------------------|
| `maintained` | Already routes through a facade-shaped request/result surface and can remain a supported frontend path once provenance fields are added. |
| `compatibility_adapter` | Useful migration path, but it lacks one or more WP4 fields such as `AgentRole`, `source_id`, `effective_time`, `valid_until`, `merge_policy`, or snapshot provenance. |
| `diagnostics_only` | Truth-derived, raw-runtime, oracle, or privileged helper path that must not become maintained policy input. |

Important naming caveat: many Python adapters call `AgentObservation` values
`truth`. That is not automatically raw `World Truth`; when the value came from
`ObservationBatchPacket.agent_observations`, it is facade-exported observation
data with a risky legacy name. When the value comes from direct `sim.*` or raw
runtime escape hatches, it is a compatibility or diagnostics boundary.

## 2. AgentRole Five-Element Mapping Draft

Architecture defines the five elements as `role`, `authority_scope`,
`information_state_source`, `decision_model_ref`, and `action_interface`.
`wp4_policy_binding_cluster_20260519.md` additionally recommends stable
`role_id`, `role_type`, and `maintained_status`. The current adapter mapping is:

| Current adapter role | role | authority_scope | information_state_source | decision_model_ref | action_interface | status |
|----------------------|------|-----------------|--------------------------|--------------------|------------------|--------|
| Single-agent Gym pilot | `agent_id` from `ScenarioLoader.load_scenario()`; role type implicit `autopilot_controller` or `pilot` | One entity selected as `is_agent` | `get_agent_observation` plus `get_instrument_state`; in batch path preferably `ObservationBatchPacket` | External RL policy, scripted controller, or caller-provided Gym action | `PilotAction` via `set_pilot_action` or `WorldPilotActionAssignment` | `compatibility_adapter` |
| Batch execution pilot | `WorldBatchVecEnv` handle with `world_index`, `entity_id`, and loader state | One entity per world handle | `RuntimeFacadeAdapter.read_truth_and_instruments()` using `ObservationBatchRequest` when available | External RL policy or `MultiTimescaleActionWrapper` | `WorldPilotActionAssignment` through `RuntimeFacadeAdapter.set_pilot_actions_batch()` | `compatibility_adapter`, close to maintained once intent metadata exists |
| Multi-agent roster slot | `MultiAgentControlSlot`: `world_index`, `entity_id`, `entity_name`, `roster_index`, `role_code`, `formation_role_id`, `policy_route` | Roster member entity and optional team/element metadata | `MultiAgentWorldRuntimeView.export_packet()` using `ObservationBatchRequest` when available | Per-slot policy route or caller-provided multi-agent policy | `WorldPilotActionAssignment` per entity | `compatibility_adapter` |
| Leader or C2 role | Leader env phase bucket plus task/order/intent state; role type implicit `flight_lead` or `coordinator` | Mission command, task order, leader intent, pilot report for the controlled entity or roster | Cached execution observation, instrument state, task/order state, and sometimes ownship observation named `truth` | `FrozenExecutionPolicyAdapter`, scripted C2 manager, or teacher baseline | `WorldMissionCommandAssignment`, `WorldTaskOrderAssignment`, `WorldLeaderIntentAssignment`, `WorldPilotReportAssignment` | `compatibility_adapter` |
| Scripted cooperative director | World-level `ScriptedCooperativeCoordinationDirector` | Formation offsets, leader/wingman role metadata, roster tasking fields | Loader mission command, cooperative state, and roster metadata | Scripted coordination policy | Command-chain assignment objects flushed by vec env | `compatibility_adapter` |
| Oracle or privileged helper | No maintained role id yet | Unbounded unless explicitly scoped by test | Raw `sim`, raw runtime, cached `truth`, scenario internals, privileged diagnostics | Test oracle, teacher, debug utility | Any direct mutation or hidden helper | `diagnostics_only` unless wrapped and scoped |

Proposed minimum `AgentRole` schema for later implementation:

```yaml
role:
  role_id: stable string or numeric id
  role_type: autopilot_controller | flight_lead | wingman | coordinator | human_operator | diagnostic_oracle
authority_scope:
  world_index: optional integer
  entity_ids: [entity ids]
  roster_scope: optional roster or team id
  allowed_families: [direct_control, mission_command, tasking, coordination, report]
information_state_source:
  kind: ObservationPacket | DecisionBelief | shared_tactical_picture | diagnostics_only_oracle
  consumed_snapshot_version: optional version
  view_spec_schema: optional ObservationViewSpec version
decision_model_ref:
  kind: learned_policy | scripted_controller | scripted_director | teacher_baseline | human | diagnostics_helper
  id: checkpoint path, controller class, manager name, or human source id
action_interface:
  kind: ActionIntentPacket | CoordinationIntentPacket | PilotActionAssignmentCompat | CommandChainAssignmentCompat
  merge_policy: last_write_wins | priority_override | reject_on_conflict | merge_by_field | append_only
maintained_status: maintained | compatibility_adapter | diagnostics_only
```

## 3. Action Intent Paths

| Path | Current behavior | Missing WP4 fields | Status |
|------|------------------|--------------------|--------|
| `gym_envs/universal_env_parts/actions.py::build_pilot_action` | Converts normalized Gym action arrays into `ef_py.PilotAction`. | `source_layer`, `source_id`, `input_snapshot_version`, `effective_time`, `valid_until`, `merge_policy`, `AgentRole`. | `compatibility_adapter` |
| `gym_envs/universal_env.py::step` | Direct single-world `sim.set_pilot_action(...)` then `sim.step()`. | Facade-compatible request boundary plus all intent metadata. | `compatibility_adapter`; not a maintained WP4 frontend path. |
| `python/rl/runtime/world_batch_vec_env.py::step_wait` | Builds `WorldPilotActionAssignment` and calls `RuntimeFacadeAdapter.set_pilot_actions_batch(...)`. | First-class `ActionIntentPacket` and `ActionHoldPolicy`. | `compatibility_adapter`, preferred current migration path. |
| `python/rl/runtime/single_world_batch_runtime.py::step` | Single-env wrapper around the same batch assignment path. | Same as batch path. | `compatibility_adapter`. |
| `python/rl/runtime/leader_world_batch_runtime.py::step_indices` | Batch leader execution handle builds `WorldPilotActionAssignment`. | Same as batch path. | `compatibility_adapter`. |
| `python/rl/runtime/multi_agent_runtime.py::apply_actions` | Per-roster-slot action dictionary becomes `WorldPilotActionAssignment`. | Per-slot `AgentRole` and action timing/conflict metadata. | `compatibility_adapter`. |

Implementation implication: do not add a public C++ binding yet. After WP4-A
stabilizes names, introduce a Python adapter object that can wrap existing
`PilotAction` assignments as `ActionIntentPacket`-equivalent metadata before
any binding expansion.

## 4. Coordination Intent Paths

| Path | Current behavior | Missing WP4 fields | Status |
|------|------------------|--------------------|--------|
| `gym_envs/leader_env_parts/bridges.py::LeaderCommandBridge` | Holds `TaskOrder`, `LeaderIntent`, and `PilotReport`; can sync directly to `loader.sim`. | Source identity, roster scope, update clock, merge policy, consumed observation version. | `compatibility_adapter`. |
| `gym_envs/leader_env_parts/decision_runtime/commands.py::apply_leader_command` | Decodes leader action into mission command, task, leader intent, and report state. | `CoordinationIntentPacket` boundary, conflict policy, and `AgentRole`. | `compatibility_adapter`. |
| `python/rl/runtime/world_batch_vec_env.py::_sync_command_chain_batch` | Flushes mission/task/leader/report assignments through `RuntimeFacadeAdapter`. | Intent packet metadata and deterministic merge contract. | `compatibility_adapter`, preferred current batch bridge. |
| `python/rl/runtime/cooperative_world_batch_vec_env.py::_sync_command_chain_batch` | Same command-chain flush for cooperative worlds and roster slots. | Per-role authority scope and merge policy. | `compatibility_adapter`. |
| `python/rl/runtime/world_batch/cooperative_director.py::ScriptedCooperativeCoordinationDirector` | Scripted world-level director mutates command-chain state before batch sync. | Explicit source layer/id, update clock, and produced tasking fields in a packet. | `compatibility_adapter`. |

Implementation implication: current coordination behavior is usable evidence for
`CoordinationIntentPacket`, but not yet the packet itself. It should be wrapped
after WP4-A names the maintained coordination surface.

## 5. Observation and Belief Input Paths

| Path | Current behavior | Status |
|------|------------------|--------|
| `RuntimeFacadeAdapter.export_observation_packet(...)` | Uses `RuntimeFacade.export_observation_packet(...)` when present, otherwise builds `_ObservationPacketCompat` from batch getters. | `maintained` when facade is present; fallback is `compatibility_adapter`. |
| `RuntimeFacadeAdapter.read_truth_and_instruments(...)` | Builds `ObservationBatchRequest` and returns `packet.agent_observations`, `packet.instrument_states`. Legacy names call observations `truth`. | `maintained` surface with naming/provenance gap. |
| `WorldBatchVecEnv._collect_observations(...)` | Reads observation/instrument packets, caches them, and builds policy observations. | `compatibility_adapter` until `ObservationViewSpec` and snapshot provenance are recorded. |
| `gym_envs/universal_env_parts/observations.py::build_universal_observation` | Builds policy observation dict from instrument state, agent observation, contacts, RWR, mission vector, optional proprio. | `compatibility_adapter`; can become maintained once view spec and allowed fields are explicit. |
| `python/rl/runtime/world_batch/observation_batching.py::compute_execution_observation_batch` | Compiled/batched observation builder from cached instrument and agent observation values. | `compatibility_adapter`; needs source packet/version metadata. |
| `MultiAgentWorldRuntimeView.export_packet(...)` | Uses `ObservationBatchRequest` when available and falls back to raw batch getters. | `maintained` surface when facade request is used; fallback is `compatibility_adapter`. |
| `python/rl/control/*` scripted controllers | Consume only observation dict keys such as `instruments` and `mission`; some stateful memory acts as implicit belief. | `maintained` if the input observation is maintained; `DecisionBelief` metadata is missing. |
| `FrozenExecutionPolicyAdapter` | Frozen SB3 policy inference wrapper over observation tensors. | Decision model reference exists; `DecisionBelief` contract is missing. |

There is no first-class `DecisionBelief` DTO or Python helper yet. Current
belief-like state exists as model latent state, scripted-controller memory,
teacher baselines, or cached leader window state. Those should be documented as
maintained only when derived from declared observations; truth-derived teacher
or debug baselines should be `diagnostics_only`.

## 6. World Truth and Oracle Risk Register

| Path | Risk | Required label |
|------|------|----------------|
| `RuntimeFacadeAdapter.world(...)`, `make_scenario_loader(...)`, and `_compat_runtime = facade.runtime()` | Centralized raw runtime escape hatch. This is acceptable as a migration adapter but must not be re-exported as maintained policy API. | `compatibility_adapter` |
| `bindings_runtime.cpp` exposing `WorldBatchRuntime` and `RuntimeFacade.runtime()` | Python can still reach raw batch runtime and world handles. | `compatibility_adapter`; `diagnostics_only` for policy truth use. |
| `gym_envs/universal_env.py` direct `sim.set_pilot_action`, `sim.step`, `sim.get_agent_observation`, visual observation calls | Legacy single-world environment bypasses facade-shaped request/result flow. | `compatibility_adapter` |
| `build_universal_observation(...)` using values named `truth` and direct `truth.x/y` for ILS/mission observation construction | May be facade-exported ownship observation, but provenance and view-spec permission are not explicit. | `compatibility_adapter`; `diagnostics_only` if raw truth or hidden scenario metadata is consumed by policy. |
| `gym_envs/scenario_loader/step_evaluation.py` and reward/runtime helpers using `truth_*` values | Valid for simulation facts and reward reports only when fact/shaping ownership is explicit; unsafe as policy observation oracle. | `compatibility_adapter` for reward/fact computation; `diagnostics_only` if fed into maintained policy belief. |
| Leader/C2 helpers using `truth_now` for station metrics or report location | Could be legitimate ownship/report state, but currently lacks source snapshot and role metadata. | `compatibility_adapter` |
| Visual observation direct calls through raw world or runtime compatibility helpers | The visual view may be valid observation data, but it bypasses `ObservationViewSpec` naming today. | `compatibility_adapter`; `diagnostics_only` for privileged debug views. |
| Scripted teachers, teacher baselines, and oracle diagnostics | May use knowledge not available to the controlled agent. | `diagnostics_only` unless inputs are proven to come from maintained observations. |

## 7. Python Binding Mirror Status

Current bindings mirror the stable WP4 maintained facade shells:

| C++ surface | Python mirror status |
|-------------|----------------------|
| `RuntimeCapabilities`, `RuntimeBatchConfig`, `BatchResetRequest` | Bound in `bindings_runtime.cpp`. |
| `BatchWorldSetupRequest` / `BatchWorldSetupResult` | Bound with current fields. |
| `ObservationBatchRequest` / `ObservationBatchPacket` | Bound with current include flags and packet vectors. |
| `EngagementBatchRequest` / `EngagementEventPacket` | Bound with track, launch, lifecycle, effects, damage, and diagnostics vectors. |
| `ExecutionBatchStepRequest` / `ExecutionBatchStepResult` | Bound with step requests, rewards, termination/truncation, info, and observation packet. |
| `RuntimeFacade` maintained methods | Bound for setup, reset, observation export, engagement export, execution step, and batch helpers. |

The bindings also expose compatibility surfaces:

| Surface | Status |
|---------|--------|
| `WorldBatchRuntime` | Compatibility-only. |
| `WorldBatchRuntime.world(...)` | Compatibility/diagnostics escape hatch. |
| `RuntimeFacade.runtime()` | Compatibility/diagnostics escape hatch. |
| Raw candidate-id and visual helpers | Compatibility until an `ObservationViewSpec` path owns their semantics. |

Do not bind these until WP4-A stabilizes names and fields:

- `ObservationViewSpec`,
- `DecisionBelief`,
- `AgentRole`,
- `ActionIntentPacket`,
- `ActionHoldPolicy`,
- `CoordinationIntentPacket`,
- request metadata fields: `source_layer`, `source_id`,
  `input_snapshot_version`, `effective_time`, `valid_until`, and
  `merge_policy`.

## 8. Follow-On Implementation Suggestions

1. `WP4-D1 AgentRole adapter sketch`: add a Python-side documentation or
   dataclass sketch mapping `ScenarioLoader` agent ids and roster slots to
   `AgentRole`, but do not bind it publicly before WP4-A surface names settle.
2. `WP4-D2 ActionIntent shim`: create a narrow Python compatibility shim that
   wraps `PilotAction` / `WorldPilotActionAssignment` with source id, effective
   time, validity, merge policy, and role metadata.
3. `WP4-D3 CoordinationIntent shim`: wrap leader command-chain assignments into
   a packet-equivalent object with source, roster scope, update clock, and merge
   policy.
4. `WP4-D4 Observation provenance pass`: rename or annotate Python variables
   where `AgentObservation` is called `truth`, and record source packet/version
   once the facade exposes snapshot metadata.
5. `WP4-D5 Oracle audit tests`: add architecture tests that fail maintained
   policy paths if they call raw `RuntimeFacade.runtime()`,
   `WorldBatchRuntime.world(...)`, or direct `sim.get_agent_observation(...)`
   outside registered compatibility adapters.
6. `WP4-E1 Binding mirror after WP4-A`: bind only stable DTO names and add
   field-presence tests; keep `WorldBatchRuntime` and `RuntimeFacade.runtime()`
   documented as compatibility-only.

## 9. Open Questions

1. Should `AgentObservation` fields such as ownship `x/y/z` be maintained
   policy observation fields by default, or only when an `ObservationViewSpec`
   explicitly allows ownship truth-state projection?
2. What object owns `SnapshotVersion` for Python `ObservationBatchPacket` once
   WP2.5 shard/version semantics are implemented?
3. Should visual observations be represented as an `ObservationViewSpec` field
   family or as a separate observation export surface?
4. Should leader teacher baselines be modeled as `DecisionBelief` with
   `diagnostics_only`, or as orchestration-layer supervisors with restricted
   authority?
5. Should `RuntimeFacadeAdapter.world(...)` remain callable, or should it move
   behind explicitly named diagnostics methods after WP4?
