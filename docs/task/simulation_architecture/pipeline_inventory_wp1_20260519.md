# WP1 Pipeline Inventory

Status: `2026-05-19` inventory draft.

Language:

- English canonical: `pipeline_inventory_wp1_20260519.md`
- Chinese companion: [pipeline_inventory_wp1_20260519.zh.md](pipeline_inventory_wp1_20260519.zh.md)

Architecture baseline:

- [simulation system architecture design](../../plan/architecture/simulation_system_architecture_design.md)
- [simulation architecture task entry](README.md)

This document maps the current codebase onto the canonical `P0-P10` semantic
lifecycle and identifies where the current implementation already behaves like
a temporal DAG. It is a read-only inventory and gap analysis. It does not
authorize implementation by itself; it prepares the evidence needed for `WP2
Contract Freeze`.

## 1. Summary

The repository already has real assets across the whole `P0-P10` semantic
lifecycle.
The strongest current ownership is around:

- `P1 WorldSetup`,
- `P2 TaskingIntent`,
- `P5 PhysicsStep`,
- `P6 SenseTrackLink`,
- `P10 ObservationExport`.

The weakest contract surfaces are around:

- `P4 PlatformControl` as a facade-visible stage,
- `P7 FireControlLaunch` as a typed launch request/event boundary,
- `P8 MunitionLifecycle` as a lifecycle packet,
- `P9 EffectsDamage` as a damage report contract.

The main structural risk is not absence of behavior. The behavior exists. The
risk is that several stages still meet in broad runtime owners, especially
`SimulationKernel`, `WorldBatchRuntime`, `ExecutionEpisodeController`, and
`simulation_kernel_weapon_api.cpp`. WP2 should therefore freeze stage-node
contracts, not only packet names.

The second structural risk is cross-layer coupling. The simulation layer is
the center of project fidelity, but the current policy and orchestration
layers also assemble observations, shape rewards, request actions, coordinate
multi-agent intent, and mirror episode state. WP2 should therefore freeze both
simulation-internal contracts and the policy/orchestration contracts that touch
them.

## 2. Stage Inventory

| Stage | Maturity | Current assets | Evidence | Gap / risk |
|-------|----------|----------------|----------|------------|
| `P0 ContentCompile` | partial | Unit/content presets and setup-facing DTOs exist. | [default_unit_factory.h](../../../src/models/core/default_unit_factory.h:71), [world_batch_contracts.h](../../../src/runtime/contracts/world_batch_contracts.h:19), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:396) | Content compile and world setup still meet in runtime setup paths; spawn-time combat overrides blur content vs setup. |
| `P1 WorldSetup` | strong but coupled | Batch reset, terrain/wind/zone setup, spawn, time-step setup, and facade setup calls exist. | [runtime_facade.h](../../../src/runtime/facade/runtime_facade.h:41), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:107), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:234) | Good facade access exists, but setup still depends on concrete `WorldBatchRuntime` behavior. |
| `P2 TaskingIntent` | strong but compatibility-heavy | `TaskOrder`, `LeaderIntent`, `PilotReport`, mission commands, episode state, and batch assignment paths exist. | [world_batch_contracts.h](../../../src/runtime/contracts/world_batch_contracts.h:77), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:146), [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:124) | `MissionCommand` remains a flat compatibility aggregation point; tasking and execution intent still overlap in consumers. |
| `P3 CommandDelivery` | present but not narrow | Command-link systems materialize pending movement/action/mission commands; facade can batch mission command assignment. | [command_link_system.h](../../../src/systems/systems/command_link_system.h:19), [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:169), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:142) | Command packet ownership is still broad; `MissionCommand` carries tasking, execution, and engagement fields. |
| `P4 PlatformControl` | partial | Pilot/action DTOs, air control model, and control system stage exist. | [bindings_command.cpp](../../../src/interfaces/python/bindings_command.cpp:260), [default_control_model.cpp](../../../src/models/air/default_control_model.cpp:101), [control_system.h](../../../src/systems/physics/control_system.h:12) | Control is real, but no dedicated facade-level platform-control packet or stage contract is visible. |
| `P5 PhysicsStep` | strong internally | Force clear, aero state, propulsion, force accumulation, aerodynamics, contact, rotational integration, leapfrog, and naval kinematics are registered. | [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:172), [force_system.h](../../../src/systems/physics/force_system.h:60), [leapfrog_system.h](../../../src/systems/physics/leapfrog_system.h:44) | The physics chain is scheduled, but a replaceable `IPhysicsBackend` style boundary is not yet a public contract. |
| `P6 SenseTrackLink` | strong internally, partial contract | Sensors, sonar, track fusion, data link, EW, and observation fallback logic exist. | [default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp:312), [track_manager_system.h](../../../src/systems/systems/track_manager_system.h:240), [data_link_system.h](../../../src/systems/systems/data_link_system.h:76) | There is no distinct `TrackPacket` ownership boundary in facade/contracts yet. |
| `P7 FireControlLaunch` | behavior-rich, contract-weak | Missile launch, naval launch, target selection, envelopes, ammo/cooldown, pilot-triggered firing, and naval auto-fire exist. | [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:353), [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp:147), [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:191) | Launch selection, envelope checks, ammo, spawning, and naval variants are concentrated in one kernel API; no typed launch request/event contract is visible. |
| `P8 MunitionLifecycle` | behavior present, contract-weak | Missile runtime initialization, guidance model, and guidance system exist. | [default_unit_factory.h](../../../src/models/core/default_unit_factory.h:579), [default_guidance_model.cpp](../../../src/models/weapons/default_guidance_model.cpp:410), [guidance_system.h](../../../src/systems/combat/guidance_system.h:8) | Munition lifecycle state is not yet exposed as a clear packet family or facade contract. |
| `P9 EffectsDamage` | behavior present, report contract missing | Effects model, damage system, and debug hit API exist. | [default_effects_model.cpp](../../../src/models/weapons/default_effects_model.cpp:129), [damage_system.h](../../../src/systems/combat/damage_system.h:42), [simulation_kernel_damage_debug_api.cpp](../../../src/core/engine/simulation_kernel_damage_debug_api.cpp:9) | Damage behavior exists, but there is no dedicated `DamageReport` or event-diagnostic contract replacing ad hoc health/debug surfaces. |
| `P10 ObservationExport` | strong | Observation packet, instrument state, mission runtime observation, and facade export exist. | [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:49), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:251), [simulation_kernel_observation_api.cpp](../../../src/core/engine/simulation_kernel_observation_api.cpp:318) | Observation export is strong, but launch/damage event diagnostics are not yet tied into one explainable trace. |

## 3. Cross-Stage Coupling Hotspots

These files are not wrong; they are the current places where multiple
architecture stages meet. They should guide WP2/WP3 boundaries.

| Hotspot | Current role | Pipeline concern |
|---------|--------------|------------------|
| [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:54) | Registers command-link, control, physics, sensor/track/data-link, embarked-air ops, weapon release, instruments, damage, EW, and logistics. | One registration spine wires `P3-P10`; useful today, but it can hide stage ownership. |
| [simulation_kernel.cpp](../../../src/core/engine/simulation_kernel.cpp:147) | Advances world state and performs naval weapon auto-fire in the same step path. | `P5` world advance and `P7` fire-control behavior are adjacent in the same owner. |
| [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:521) | Applies batch world setup and spawn-time overrides. | `P0` content, `P1` setup, and combat defaults can mix during setup. |
| [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:196) | Owns execution episode flow, reward, termination, transition, and observation aggregation. | `P2`, `P10`, reward, and termination are bundled in one mission runtime flow. |
| [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:422) | Owns launch selection, envelope checks, ammo/cooldown, munition spawning, and naval launch variants. | Main `P7-P8` contract risk; behavior exists but packet boundaries are not yet narrow. |

## 4. Facade And Contract Coverage

Current facade coverage is uneven:

- Strong: setup/reset (`P1`), tasking assignment/export (`P2`), execution batch
  stepping, and observation export (`P10`).
- Partial: command delivery (`P3`) through mission command assignment.
- Weak: platform control (`P4`), launch/fire-control (`P7`), munition lifecycle
  (`P8`), and damage reporting (`P9`) as typed request/result families.

Important risks:

1. `RuntimeFacade::runtime()` remains a compatibility and diagnostics escape
   hatch. It is intentionally documented, but it is still a bypass path.
2. Python bindings still expose `WorldBatchRuntime` directly for compatibility.
3. `world_batch_contracts.h` mixes setup, command, tasking, and observation
   structures in one broad header.
4. `MissionCommand` is still a compatibility aggregation point rather than a
   narrow command packet.

## 5. Temporal DAG Findings

The current implementation is already closer to a clocked graph than to a
linear equal-step pipeline:

| Finding | Evidence | WP2 implication |
|---------|----------|-----------------|
| Physics is internally multi-stage and likely higher cadence than command/tasking. | [simulation_kernel_systems.cpp](../../../src/core/engine/simulation_kernel_systems.cpp:172), [leapfrog_system.h](../../../src/systems/physics/leapfrog_system.h:44) | `P5` should declare a physics clock domain and substep/sync policy. |
| Command delivery has latency/drop state and pending queues. | [command_link_system.h](../../../src/systems/systems/command_link_system.h:19) | `P3` should be event/latency driven rather than same-window by default. |
| Sensor/track/data-link behavior is not naturally equal-rate with physics. | [default_sensor_model.cpp](../../../src/models/systems/default_sensor_model.cpp:312), [data_link_system.h](../../../src/systems/systems/data_link_system.h:76) | `P6` needs sensor scan and fusion clock domains plus track snapshot rules. |
| Fire-control and launch use stateful ammo/cooldown/envelope checks. | [simulation_kernel_weapon_api.cpp](../../../src/core/engine/simulation_kernel_weapon_api.cpp:353) | `P7` should emit timestamped launch events instead of implying immediate linear handoff. |
| Guidance and fuze behavior can run at a different cadence from launch decisions. | [default_guidance_model.cpp](../../../src/models/weapons/default_guidance_model.cpp:410), [guidance_system.h](../../../src/systems/combat/guidance_system.h:8) | `P8` needs guidance-rate, seeker-rate, and fuze/event-driven node contracts. |
| Damage is naturally event-driven and feeds back into future platform/sensor/weapon capability. | [damage_system.h](../../../src/systems/combat/damage_system.h:42) | `P9` should cross an event/state barrier before later capability changes are read. |
| Observation export is a snapshot/export surface, not necessarily a per-stage mutation point. | [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:251) | `P10` should declare snapshot version and sync policy. |

WP2 should treat `P0-P10` as the semantic stage vocabulary and define the
actual execution constraints as stage-node contracts:

1. `semantic_stage`,
2. `read_set`,
3. `write_set`,
4. `clock_domain`,
5. `latency_policy`,
6. `sync_policy`,
7. data-derived same-window edges,
8. state-store shard versioning,
9. deterministic event ordering,
10. nested or explicitly merged clock-domain scheduling.

## 6. Validation Inventory

Existing tests already cover several important boundaries:

| Validation area | Evidence | Notes |
|-----------------|----------|-------|
| Facade layering | [test_runtime_facade_layering.py](../../../tests/architecture/test_runtime_facade_layering.py:41) | Blocks raw runtime escape outside adapters and checks contract header hygiene. |
| Build layering | [test_cmake_target_readiness.py](../../../tests/architecture/test_cmake_target_readiness.py:25) | Protects grouped source readiness for future target splits. |
| Facade behavior | [test_runtime_facade.py](../../../tests/runtime/facade/test_runtime_facade.py:213) | Covers setup, observation export, execution batch stepping, and state advancement. |
| Mission/runtime bridge | [test_mission_runtime.py](../../../tests/runtime/mission/test_mission_runtime.py:86) | Strong `P2/P6/P10` coverage around mission observation, route guidance, live tracks, and datalink. |
| Sensor/track realism | [test_sensor_situation_realism_p0.py](../../../tests/runtime/air_combat/test_sensor_situation_realism_p0.py:62) | Strong `P6` coverage. |
| Air weapon realism | [test_weapon_guidance_realism_guards.py](../../../tests/runtime/air_combat/test_weapon_guidance_realism_guards.py:167) | Strong air-side `P7-P9` behavior coverage. |
| ROE gating | [test_weapon_roe_runtime.py](../../../tests/runtime/air_combat/test_weapon_roe_runtime.py:53) | Relevant to `P2/P3/P7` authority boundaries. |
| Naval engagement | [test_naval_ship_database.py](../../../tests/runtime/naval/test_naval_ship_database.py:30) | Rich naval-side sensor, mount, launch, CIWS, and damage coverage. |
| Batch runtime | [test_world_batch_runtime.py](../../../tests/world_batch/test_world_batch_runtime.py:184) | Validates setup, stepping, observation, and timing in batch runtime. |
| Local smoke | [ci_smoke_suite.json](../../../tests/smoke/ci_smoke_suite.json:1) | Maintained smoke set includes architecture, facade, env config, and world batch tests. |

Missing validation:

1. A single cross-domain engagement pipeline test that proves air and naval
   launch/damage behavior share the same lifecycle.
2. A facade-only engagement path test showing launch, damage, and observation
   are reachable through facade-shaped APIs or explicit compatibility adapters.
3. A diagnostics trace that ties launch, munition lifecycle, effects, damage,
   and observation export into one explainable story.
4. A stage-aligned local non-RL smoke test that explicitly exercises the new
   `P0-P10` architecture vocabulary.

## 7. Cross-Layer Coupling Findings

The current inventory identifies five system-level coupling points that WP2
should treat as architecture contract inputs, not incidental Python/C++
implementation details.

| Coupling point | Current evidence | WP2 implication |
|----------------|------------------|-----------------|
| Observation assembly crosses simulation and policy concerns. | [mission_obs_taxonomy.py](../../../python/mission_obs_taxonomy.py:127), [mission_observation.py](../../../gym_envs/scenario_loader/mission_observation.py:209), [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:49) | Freeze `ObservationViewSpec`: policy/test owns schema, encoding, and normalization; simulation/facade owns queryable snapshots and packet export. |
| Reward and termination are split between compiled mission runtime and Python step assembly. | [execution_episode_controller.cpp](../../../src/core/mission/episode/execution_episode_controller.cpp:143), [mainline.py](../../../gym_envs/scenario_loader/execution_runtime/mainline.py:309), [reward_runtime/](../../../gym_envs/scenario_loader/reward_runtime/) | Freeze `RewardSpec`, `RewardReport`, `TerminationSpec`, and reason-source attribution. Semantic termination should be compiled/facade-recoverable; shaping may remain experiment-configurable. |
| Coordination intent is produced outside the simulation DAG but writes tasking/command DTOs. | [cooperative_director.py](../../../python/rl/runtime/world_batch/cooperative_director.py:141), [cooperative_world_batch_vec_env.py](../../../python/rl/runtime/cooperative_world_batch_vec_env.py:617), [world_batch_runtime.cpp](../../../src/core/engine/world_batch_runtime.cpp:619) | Freeze `CoordinationIntentPacket` and facade assignment paths for scripted, learned, and human directors. |
| Policy inference cadence and simulation cadence are not the same clock. | [wrappers.py](../../../python/rl/control/wrappers.py:30), [operation_layer.md](../../forward/operation_layer.md:12), [runtime_facade.cpp](../../../src/runtime/facade/runtime_facade.cpp:195) | Freeze `ActionIntentPacket` and `ActionHoldPolicy`: effective time, validity window, hold/interpolation/expiry, and P3/P4/P5 consumption boundary. |
| Episode lifecycle is mirrored across compiled runtime and Gymnasium adapters. | [execution_episode_controller.h](../../../src/core/mission/episode/execution_episode_controller.h:20), [runtime_facade_types.h](../../../src/runtime/facade/runtime_facade_types.h:79), [universal_env.py](../../../gym_envs/universal_env.py:229), [core.py](../../../gym_envs/scenario_loader/core.py:1140) | Freeze `EpisodeLifecycleContract`: compiled/facade owns authoritative phase and semantic termination; adapters mirror status and request reset/truncation. |

These findings do not reduce the priority of simulation fidelity. They clarify
which external producers and consumers must be modeled so that the simulation
layer can remain authoritative as RL, batch evaluation, and service deployment
grow around it.

## 8. WP2 Contract Freeze Inputs

WP2 should not start with field-level rewrites. It should first freeze packet
ownership, facade exposure, stage-node read/write sets, and timing policy for
the weakest stages.

Recommended WP2 topics:

1. `TrackPacket` ownership: decide whether track export belongs in
   `components`, `runtime/contracts`, or a facade-only observation packet.
2. `LaunchRequest` / `LaunchEvent`: split fire-control intent from munition
   spawning and naval/air launcher variants.
3. `MunitionLifecyclePacket`: define what state is contract-worthy and what
   remains component-internal.
4. `EffectsEvent` / `DamageReport`: define a report surface that can cover HP,
   subsystem damage, soft-kill, mission kill, and diagnostics.
5. `MissionCommand` containment: freeze what remains compatibility-only and
   what moves into narrower tasking/command/engagement packets.
6. Facade escape policy: keep `RuntimeFacade::runtime()` for diagnostics, but
   block new maintained engagement work from depending on it.
7. Stage-node timing policy: freeze clock domains, latency rules, and feedback
   barriers for command, sensor, launch, guidance, fuze, damage, and export
   nodes.
8. DAG composition rule: freeze edge derivation from `read_set` and
   `write_set`, and mark cross-window feedback through `StateStore` or
   `EventQueue`.
9. Event ordering rule: freeze deterministic `(timestamp, priority, event_id)`
   ordering for launch, fuze, damage, report, and observation events.
10. Clock-domain rule: keep nested triggering as the default and require an
    explicit merge policy for independent clocks.
11. `ObservationViewSpec`: freeze which side owns field selection, encoding,
    normalization, schema version, required/optional fields, compatibility
    checks, and snapshot source.
12. `ActionIntentPacket` / `ActionHoldPolicy`: freeze policy-action effective
    time, validity window, hold/interpolation/expiry, and the `P3/P4/P5`
    boundary.
13. `RewardSpec` / `RewardReport`: freeze the split between simulation facts
    and experiment shaping using the architecture fact/shaping criterion,
    including mirror snapshot version and latency when Python computes reward.
14. `TerminationSpec` / `EpisodeStatus`: freeze semantic termination versus
    training/test truncation and require reason-source attribution.
15. `EpisodeLifecycleContract`: freeze compiled/facade authority for episode
    phase, transition, and reset while allowing Gymnasium/batch mirrors.
16. `CoordinationIntentPacket`: freeze how scripted, learned, and human
    directors write tasking or command intent through facade-compatible paths.
17. Cross-layer `merge_policy`: choose one of `last_write_wins`,
    `priority_override`, `reject_on_conflict`, `merge_by_field`, or
    `append_only` for each producer path.
18. External-input injection: decide whether each action/coordination path uses
    same-window injection or a later `effective_time`.
19. Observation compatibility: label schema changes as minor-compatible or
    major-incompatible and define checkpoint-loading behavior.

## 9. WP3 Engagement Pilot Inputs

The engagement pilot should begin only after WP2 names the packet boundaries.
The most useful pilot should prove:

1. aircraft pylon launch and naval mount launch use one stage vocabulary,
2. fire-control produces a typed launch event,
3. clock domains differ where needed without creating a private vertical stack,
4. munition lifecycle uses common state concepts even when guidance differs,
5. effects and damage produce a report visible to observation/diagnostics,
6. the local smoke path does not require RL dependencies.

## 10. Current Status

WP1 has enough evidence to proceed to `WP2 Contract Freeze`.

The architecture framework itself is now closed. Future findings should be
routed by layer: direct architecture patch for `B` contract semantics, task
plan for `C` implementation alignment, and separate layer-specific architecture
document for `D` internal design blanks.

The current implementation is best described as:

- behavior-rich,
- internally stage-shaped,
- already suggestive of a temporal DAG,
- partially facade-aligned,
- not yet contract-narrow for engagement and damage.

That is a good place to be before the next step. The code already has enough
real behavior to inventory; the next task is to narrow the contracts without
pretending the current compatibility surfaces do not exist.
