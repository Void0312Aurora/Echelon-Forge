<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md. Review before treating this file as authoritative. -->

# C2 Command Chain and Communication Progress Checkpoint

Status: `2026-05-17` archived progress checkpoint snapshot.

Related documents:

- [Freeze analysis baseline](../../c2_command_chain/c2_command_chain_realism_analysis_20260517.md)
- [Open issues analysis](c2_command_chain_unresolved_issues_20260517.zh.md)
- [Naval warfare progress checkpoint](../../naval/naval_progress_checkpoint_20260517.zh.md)
- [Sensor/situational awareness P1 implementation package](../sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md)
- [Weapon/guidance P1 implementation package](../weapon_guidance/weapon_guidance_realism_p1_implementation_package_20260517.zh.md)

Purpose of this document:

- Used to answer "how far has the current C2 command chain / CommandLink / DataLink progressed."
- Records the minimal closed loops that have been landed in the mainline; do not overstate these advancements as a complete tactical data link or full joint operations C2.
- Provides a unified status entry point for subsequent implementation, supplementary testing, or re-delegating sidecar agents.

## Zero. Current Phase Scope

The current more accurate scope should be unified as:

1. The `C2` direction has entered the "minimal engineering closed-loop integration into the mainline", not the freeze analysis stage.
2. However, it is still part of `P1-A integration wrap-up`, not a complete `tasking / network / authority` system.
3. It is currently more appropriate to treat it as:
   - `MissionCommand` fields, profile, codec, runtime, world-batch roundtrip have been basically connected
   - `RuntimeFacade / adapter / ScenarioLoader compat` still have remaining finish-up work
   - `CommandLink / DataLink / authority transfer` still remain at minimal engineering approximation

This means the current `C2` should neither be described as "completely untouched" nor as "high-fidelity C2 completed".

## I. Completed Items

### 1.1 Minimal Closure on Control Authority Competition

Completed:

1. `PilotAction.active=true` no longer unconditionally preempts `MissionCommand`.
2. Manual takeover is only triggered when `stick_roll / stick_pitch / rudder` exceed the minimal deadband.

Current effect:

- Autopilot will not be silently disengaged due to minor or unintentional pilot inputs.
- A minimal "requires obvious takeover action to switch" semantics exists between `MissionCommand` and pilot override.

Key files:

- [DefaultControlModel](../../../../src/models/air/default_control_model.cpp)
- [Control authority test](../../../../tests/runtime/multi_agent/test_control_authority_arbitration.py)

### 1.2 Navy `MissionCommand` Minimal Semantics Integration

Completed:

1. Navy `MissionCommand` has been supplemented with `reference_entity_id / station_radius_m / station_bearing_deg`.
2. These fields can now complete `binding / profile / runtime-state roundtrip`.
3. `set_unit_command()` for `Ship` uniformly writes to the `MissionCommand` side; ship main authority is no longer placed in `MovementCommand`.

Current effect:

- Naval commands no longer degrade into "hard-coded `command_code=3` absolute heading/speed".
- Ship minimal station control now has a structural entry point transferable via `MissionCommand`.
- Ship command authority has progressed from "writing a movement compatibility layer" to "primarily writing mission command."

Key files:

- [MissionCommand umbrella](../../../../src/components/command/mission_command.h)
- [MissionCommand naval fields](../../../../src/components/command/naval/mission_command_naval.h)
- [SimulationKernel command API](../../../../src/core/engine/simulation_kernel_command_api.cpp)
- [CommandLinkSystem](../../../../src/systems/systems/command_link_system.h)
- [Navy command mapping test](../../../../tests/runtime/mission/test_naval_mission_command_mapping.py)
- [Ship authority test](../../../../tests/runtime/mission/test_ship_mission_command_authority.py)
- [Mission state roundtrip test](../../../../tests/runtime/mission/test_mission_command_naval_fields_roundtrip.py)
- [Air mission roundtrip test](../../../../tests/runtime/mission/test_mission_command_air_fields_roundtrip.py)

### 1.3 ROE / Authority Minimal Fields and Runtime Gate

Completed:

1. `roe_state / engagement_authority_holder_id / engagement_authority_grantor_id` have been added to `LeaderIntent / MissionCommand / codec / binding / profile`.
2. Weapon release now has a minimal ROE gate:
   - `HOLD` prevents implicit firing
   - `TIGHT` requires target, authorization, and authority holder match

Current effect:

- `authorization_to_fire` is no longer the sole engagement control bit.
- The runtime can at least distinguish three minimal engagement constraints: `HOLD / TIGHT / legacy fallback`.

Key files:

- [LeaderIntent core](../../../../src/components/tasking/common/leader_intent_core.h)
- [MissionCommand core](../../../../src/components/command/common/mission_command_core.h)
- [Weapon runtime gate](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [ROE field test](../../../../tests/runtime/mission/test_mission_command_roe_fields.py)
- [ROE runtime test](../../../../tests/runtime/air_combat/test_weapon_roe_runtime.py)

### 1.4 `CommandLink` Queue Semantics Clarification and Test Closure

Completed:

1. `MissionCommand` pending queue now has minimal FIFO semantics.
2. Backlog is now supplemented with a minimal priority reordering and tail replacement of low-priority items when the queue is full.
3. The QoS test that previously misjudged normal sequential delivery as overwriting has been corrected.

Current effect:

- The mainline can now stably verify "the first submitted mission command is delivered first, later one later."
- When backlog is congested, high-priority engagement commands can now be inserted at the front or replace low-priority tail items.
- Queue / backlog status now also has a debug surface for directly observing pending and queued entries.
- However, this should still not be described as "complete command-link queue policy completed."

Key files:

- [Mission queue helper](../../../../src/components/command/command_link_qos.h)
- [CommandLink QoS test](../../../../tests/runtime/link/test_command_link_qos.py)

### 1.5 `DataLink` Advanced from "Unlimited Broadcast" to "Budgeted, Observable Congestion"

Completed:

1. `DataLink` now has independent `max_reports_per_update` and `max_messages_per_update`.
2. Explicit messages and track reports no longer share a single total budget.
3. `DataLink` now records per-frame and cumulative:
   - reports sent
   - messages sent
   - reports dropped
   - messages dropped
4. Python / runtime side can read these states via `debug_get_data_link_state()`.

Current effect:

- It is no longer possible to describe the current `DataLink` as "unlimited broadcast per frame."
- Minimal message prioritization and minimal throughput caps have entered the runtime.
- Congestion is no longer implicit behavior but has a visible state surface for debugging and testing.

Key files:

- [DataLink component](../../../../src/components/systems/data_link.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)
- [debug_get_data_link_state binding](../../../../src/interfaces/python/bindings_core.cpp)
- [DataLink QoS runtime test](../../../../tests/runtime/link/test_data_link_qos_runtime.py)

### 1.6 `RuntimeFacade` / World-batch Adapter Closed into Gatekeeping Mode

Completed:

1. `RuntimeFacade.runtime()` has been explicitly downgraded to a compatibility / diagnostics escape hatch.
2. The maintained Python mainline now exposes facade-shaped methods through explicit adapters.
3. Raw runtime/world penetrations in `world_batch_vec_env.py` and `leader_world_batch_runtime.py` have been centralized back into adapters, guarded by architecture tests.
4. World-setup compatibility entry points have been explicitly converged into compat helpers, rather than scattered forks in the business chain.

Current effect:

1. It is no longer appropriate to describe `RuntimeFacade` as "the main class can arbitrarily penetrate raw runtime."
2. However, this line cannot be said to be completely signed off; the compat surface still exists and adapter offloading still has remaining capacity.

Key files:

- [RuntimeFacade README](../../../../src/runtime/facade/README.md)
- [RuntimeFacade header](../../../../src/runtime/facade/runtime_facade.h)
- [adapter.py](../../../../python/rl/runtime/world_batch/adapter.py)
- [Runtime facade layering tests](../../../../tests/architecture/runtime_facade)
- [World setup compat tests](../../../../tests/runtime/core/test_world_setup_compat.py)

### 1.7 Air-to-Air Weapon Bridging Test Enhancement

Completed:

1. The smoke coverage of `fire_weapon_from_pilot_action()` now includes an assertion that it "respects `assigned_target_id` instead of firing blindly."

Current effect:

- The bridge `MissionCommand -> pilot-triggered weapon release` no longer only verifies "can fire," but begins verifying "fires at the correct target."

Key files:

- [Air combat 1v1 missile tests](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)

## II. Current Capability Assessment

The current C2 command chain mainline has progressed from "listing a set of defects in the freeze analysis" to "multiple minimal closed loops have entered the runtime mainline":

1. Control authority layer:
   - `PilotAction` and `MissionCommand` have minimal takeover threshold semantics.
2. Execution command layer:
   - Navy `MissionCommand` is no longer completely empty.
   - `Ship` authority has been primarily written to `MissionCommand`.
3. Engagement layer:
   - `ROE / authority holder` has begun entering the runtime gate.
4. Command delivery layer:
   - `MissionCommand` queue now has stable minimal FIFO verification.
5. Communication layer:
   - `DataLink` has evolved from "unlimited broadcast" to "separate budgets + observable congestion."
6. Runtime adapter layer:
   - The mainline usage surface of `RuntimeFacade` has been recovered to explicit adapters + gatekeeping tests.

However, this line cannot yet be called a complete "joint operations C2 / tactical datalink simulation" because:

1. `CommandLink` still lacks ACK / retransmission / multi-hop / true jitter.
2. `DataLink` still lacks relay / jamming / NPG / tasking message doctrine.
3. Naval tasking and fire-control AI remain minimal engineering approximations.
4. The semantic boundaries of `MissionCommand` (common / air / naval) are not yet fully closed.
5. The `RuntimeFacade / ScenarioLoader` compat surface has not been fully offloaded.

## III. Current Recommendations

If continuing to advance, the following order is recommended:

1. First, perform small-scale stress/scale supplementary tests on `DataLink` to confirm the stability of budgets and drop counts under more complex fan-out.
2. Then return to `CommandLink` to decide whether to introduce minimal priority queues or jitter approximations.
3. Simultaneously continue compressing the `RuntimeFacade / ScenarioLoader` compat surface to prevent raw runtime from re-entering the mainline.
4. Then evaluate whether to open deeper directions like naval tasking / engage-on-remote / relay.

The most important conclusion currently:

- This line is no longer just analysis documents.
- But it is still in the stage of "minimal engineering closed loops gradually integrating into the mainline", not "high-fidelity C2 completed".
