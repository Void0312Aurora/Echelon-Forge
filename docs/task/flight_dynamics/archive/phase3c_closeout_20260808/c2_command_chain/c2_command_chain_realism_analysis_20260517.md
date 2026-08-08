<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/archive/phase3c_closeout_20260808/c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md. Review before treating this file as authoritative. -->

# Chain of Command and C2 Communication Realism Analysis

Status: `2026-05-17` Frozen Analysis Version.

Related Files:

- [TaskOrder Component](../../../../../../src/components/tasking/task_order.h)
- [TaskOrderCore (Generic)](../../../../../../src/components/tasking/common/task_order_core.h)
- [TaskOrderAir (47 Fields)](../../../../../../src/components/tasking/air/task_order_air.h)
- [TaskOrderNaval (3 Fields)](../../../../../../src/components/tasking/naval/task_order_naval.h)
- [LeaderIntent Component](../../../../../../src/components/tasking/leader_intent.h)
- [LeaderIntentAir (33 Fields)](../../../../../../src/components/tasking/air/leader_intent_air.h)
- [LeaderIntentNaval (2 Fields)](../../../../../../src/components/tasking/naval/leader_intent_naval.h)
- [PilotReport Component](../../../../../../src/components/tasking/pilot_report.h)
- [MissionCommand Component](../../../../../../src/components/command/mission_command.h)
- [MissionCommandAir (12 Fields)](../../../../../../src/components/command/air/mission_command_air.h)
- [Command Component README (Boundary Statement)](../../../../../../src/components/command/README.md)
- [PilotAction Component](../../../../../../src/components/command/pilot_action.h)
- [MovementCommand / ActionCommand / CommandLag](../../../../../../src/components/command/legacy_command.h)
- [CommandLink / pending command components](../../../../../../src/components/command/command_link.h)
- [CommandLinkSystem (Delivery Scheduling)](../../../../../../src/systems/systems/command_link_system.h)
- [CommMessage / CommQueue / CommPacket](../../../../../../src/components/command/common/comm_message.h)
- [DataLinkSystem (Track Sharing + Message Distribution)](../../../../../../src/systems/systems/data_link_system.h)
- [MissionCommandCodec (JSON Codec)](../../../../../../src/core/mission/episode/detail/mission_command_codec.h)
- [ExecutionEpisodeController](../../../../../../src/core/mission/episode/execution_episode_controller.h)
- [DefaultControlModel (Command Consumer)](../../../../../../src/models/air/default_control_model.cpp)
- [SimulationKernel Command API](../../../../../../src/core/engine/simulation_kernel_command_api.cpp)
- [LeaderTasking (Python C2 Task Manager)](../../../../../../python/rl/tasking/leader_tasking.py)
- [LeaderCommandBridge](../../../../../../gym_envs/leader_env_parts/bridges.py)
- [LeaderEnv commands.py](../../../../../../gym_envs/leader_env_parts/decision_runtime/commands.py)
- [AirProfile (Air Command Construction)](../../../../../../python/rl/profile/air_profile.py)
- [NavalProfile (Naval Command Construction)](../../../../../../python/rl/profile/naval_profile.py)
- [C2 Communication and Command Chain Roadmap](../../../../../systems/command-tasking/work/issues/c2_communication.md)
- [Naval Mission Minimal Structure](../../../../../domains/naval/standards/minimal_task_structure.md)

Document Positioning:

- This document only records known deficiencies in the current chain of command and C2 communication pipeline, and their correspondence to real military command and control.
- It does not cover acceptable simplifications, does not provide prioritization, and does not give a work plan.
- The air and naval chains of command indeed have different structures and maturity levels in this project; this document discusses each separately and performs a cross-domain comparison at the end.

Current Status Guidance:

- This document is a frozen analysis input, not a current execution status board.
- For execution status and regression risks directly related to this analysis, refer only to the `2026-05-18` closure marker in this analysis.

## Addendum: `2026-05-18` Closure Mark

Mark Criteria:

- `Unresolved`: The original argument still largely holds.
- `Partially Resolved`: Partial implementation or shared contract closure exists, but the core gap remains.
- `Minimal Closure Exists`: Minimal runtime closed loop already exists; it is no longer appropriate to describe as "completely missing".
- `Resolved`: The old argument is no longer suitable as a description of the current state.

This addendum is only used to determine whether these `C2` arguments can still be directly regarded as current issues today.

| Item | Current Mark | Description |
|------|--------------|-------------|
| `2.1` Chain of command asymmetry by domain—naval side severely underdeveloped | `Partially Resolved` | Naval side is still significantly weaker than the air side, but has progressed from "severely underdeveloped" to a minimal engineering closure integrated into the mainline. |
| `2.2` `MissionCommand` is a "shared shell + heavy air load" | `Partially Resolved` | Overall still `air-shaped`, but naval-specific `station/reference` fields have been integrated. |
| `2.3` Naval command mapping bypasses all mission command | `Resolved` | Naval command mapping now carries `MissionCommand` semantics and runtime station/reference handling; the remaining gap is richer naval mission-phase semantics rather than total mission-command bypass. |
| `2.4` Two command pipelines coexist—`MovementCommand` not deprecated | `Partially Resolved` | Dual pipeline still exists, but `Ship`'s main authority has been reclaimed from `MovementCommand` to `MissionCommand`. |
| `2.5` `CommandLink` model is too simplified | `Partially Resolved` | `FIFO backlog + minimal priority reorder` exists, but still no `ACK/retry/jitter/multi-hop`. |
| `2.6` Communication message system has no bandwidth/electronic warfare constraints | `Partially Resolved` | No longer infinite broadcast; `budget/drop/debug` has been integrated, but still no `relay/jamming`. |
| `2.7` Control authority contention between `PilotAction` and `MissionCommand` | `Minimal Closure Exists` | Minimal `deadband` takeover semantics exist, but still lacks complete mode-state/hysteresis. |
| `2.8` No Rules of Engagement (ROE) state machine | `Partially Resolved` | Minimal `roe_state + authority gate` exists, but still not a complete `ROE` state machine. |
| `2.9` No engagement authority transfer in command relationships | `Unresolved` | authority transfer / revoke / inheritance still not implemented. |
| `2.10` Codec redundancy between `LeaderIntent ↔ MissionCommand` | `Partially Resolved` | Redundancy remains, but roundtrip/codec drift has been partially controlled by explicit gate tests. |
| `2.11` Formation control only modeled on the air side—no naval formation logic | `Partially Resolved` | Naval side still lacks a complete formation control loop, but has minimal `station/reference/formation` carrier. |

---

## 1. Current Chain of Command Architecture

The project implements a five-layer chain of command, extending from strategic task allocation to physical control surfaces:

```
Layer 5: TaskOrder        → C2 tasking (who executes what mission, where, with whom)
Layer 4: LeaderIntent     → Leader decision (current phase, target heading/altitude/speed, engagement authorization)
Layer 3: MissionCommand   → Compiled execution command (heading/altitude/speed consumable by autopilot/ship)
Layer 2: MovementCommand  → Legacy generic movement instruction (or PilotAction → direct stick/throttle)
Layer 1: ControlModel     → Physical execution (FBW autopilot / ship heading-speed tracking)
```

Commands flow through `CommandLink` (latency + packet loss), and are delivered after a delay via `Pending*Command` queues.

---

## 2. Known Distortion Points

### 2.1 Chain of Command Asymmetry by Domain—Naval Side Severely Underdeveloped

The air command chain has 47 fields in TaskOrderAir + 33 fields in LeaderIntentAir + 12 fields in MissionCommandAir, covering formation, takeoff, approach, wingman, CAP station, etc. The naval side `TaskOrderNaval` / `LeaderIntentNaval` / `PilotReportNaval` actually share the same pair of fields:

```cpp
// naval_tasking_enums.h + task_order_naval.h / leader_intent_naval.h / pilot_report_naval.h
NavalWarfareRole warfare_role_code;    // ScreenCommander / SurfaceActionCommander / ...
NavalStationType naval_station_type;   // Screen / Support / PatrolStation / ...
// TaskOrderNaval additionally has: officer_in_tactical_command
```

Real naval chain of command is at least as complex as the air side—the C2 of a carrier strike group involves:

- **Composite Warfare Commander (CWC)** concept: decomposes tactical command into multiple functional commanders such as Anti-Air Warfare Commander (AAWC), Anti-Submarine Warfare Commander (ASWC), Anti-Surface Warfare Commander (SUWC), each with independent responsibilities and engagement authority
- **Hierarchical delegation of Weapon Release Authority**: from Officer in Tactical Command (OTC) down to Warfare Commander → Unit Commander → Weapon Control Officer (WCO). Different weapon types have different engagement authority thresholds (CIWS for self-defense is automatic, anti-ship missiles require AAWC authorization, land attack requires OTC authorization)
- **Cooperative Engagement Capability (CEC)**: allows one ship to use another ship's radar data for fire control solution and launch missiles. CEC is currently not modeled at all—no "engage on remote" semantics, no shooter-sensor pairing
- **Command relationship framework of Link 16**: J12.x series messages carry tasking orders, engagement status, and weapon coordination. Current `DataLinkSystem` only shares `ContactList` without carrying any tasking
- **Dynamic OTC transfer for maritime formations**: when the OTC ship is damaged or communication is lost, command authority must be transferred according to a preset succession order. Currently no command authority transfer logic

### 2.2 MissionCommand is a "Shared Shell + Heavy Air Load"

The source README candidly acknowledges this:

> `CommandLink` is closer to a true shared core than `MissionCommand`; `MissionCommand` currently still looks more like a "shared shell + heavy air load".

```cpp
// MissionCommand flat structure
cmd_heading_deg, cmd_altitude_m, cmd_speed_mps  // Generic, from MissionCommandCore
command_code (0/1/2/3/4 = IDLE/TAKEOFF/VECTOR/ROUTE/LANDING)  // Generic
// But the command_code value range is entirely flight semantics—IDLE/TAKEOFF/LANDING are meaningless for ships

// MissionCommandAir: 12 fields are all aviation-specific
recovery_base_id, recovery_runway_id, recovery_approach_type  // Landing/Approach
takeoff_procedure_id, takeoff_clearance_id, takeoff_interval_s, runway_slot_id  // Takeoff
formation_id, form_offset_x/y/z  // Formation
```

Real naval MissionCommand (or "movement instruction/station instruction") should include:

- **Station assignment**: bearing and distance relative to a reference unit (usually HVU or formation flagship) (e.g., "DDG-51 station 10 nmi ahead of HVU, port 30°"), rather than absolute heading/altitude
- **Patrol zone/search sector**: the screen ship's sector of responsibility
- **Threat axis**: expected threat direction, affecting the screen ship's priority station and sensor orientation
- **Rules of Engagement status**: WEAPONS FREE / WEAPONS TIGHT / WEAPONS HOLD distinction
- **Emission Control (EMCON) status**: limiting radar/communication emissions to reduce detection probability
- **Ships should not have "command_code = TAKEOFF/LANDING"**—current naval profiles hardcode `command_code = 3 (ROUTE)`, equating all destroyer behavior to "fly along a route"

### 2.3 Naval Command Mapping Bypasses All Mission Command

`naval_profile.py:build_kernel_mission_command()` simply extracts heading/speed from `task_order` and hardcodes the command code to 3. This means:

- **No mission phase transitions**: The air side has a complete state machine (SCRAMBLE → CAP → RTB → RECOVER_LAND) (`ScriptedC2TaskManager`, 701 lines), while the naval side has no equivalent—the DDG-51 remains in the same state from start to finish
- **No station arrival/departure determination**: The air CAP has station arrival detection based on radius-altitude-speed intervals. The naval side has no screen station arrival criteria
- **No mission-driven sensor/weapon state switching**: Air mission state affects radar mode, weapon selection, fuel management. On the naval side, sensors and weapons are completely outside mission control (partly because they don't yet have runtime implementations)

### 2.4 Two Command Pipelines Coexist—MovementCommand Not Deprecated

Two active command injection channels exist in the source, independent of each other:

```
Channel A: TaskOrder → LeaderIntent → MissionCommand → MissionCommand autopilot
Channel B:                 └→ set_unit_command() → MovementCommand → various consumers
Channel C: set_pilot_action() → PilotAction → ControlModel (bypassing all upper layers)
```

`MovementCommand` and `ActionCommand` are marked as "legacy", but are still actively used through:

- `SimulationKernel::set_unit_command()` — writes to `MovementCommand`, bypassing `MissionCommand`
- `CommandLinkSystem` has three independent delivery systems: `CommandLinkMovement`, `CommandLinkAction`, `CommandLinkMission`
- Naval commands have a special branch in `command_link_system.h:72-84`: after delivering MissionCommand, an additional derived MovementCommand is generated

Real command chains do not differentiate between "mission commands" and "movement commands" as two independent pipelines—this is not a two-path design, but a hierarchical command decomposition:

```
Mission-type command ("screen HVU against threats from 090")
  → Station assignment ("station 10 nmi ahead of HVU")
    → Movement instruction ("heading 090, speed 15kt")
      → Autopilot/helmsman/engine control (rudder angle + throttle)
```

The coexistence of two pipelines means the same entity may simultaneously hold inconsistent MissionCommand and MovementCommand, and the consumer (control model) has no clear prioritization or conflict resolution semantics.

### 2.5 CommandLink Model is Too Simplified

The current command latency model independently applies to each command:

- Fixed latency `latency_s` (seconds)
- Independent packet loss probability `drop_prob` [0, 1]
- Delivery decision is deterministic pseudo-random (SplitMix64, based on `floor(current_time*1000) ^ entity_id`)

Real tactical data link command delivery faces more complex constraints:

- **Slot contention**: Link 16's TDMA slots are scarce. During intense operations, multiple commands queue for the same slot, generating **queuing delay**, whose statistical properties are heavy-tailed—occasionally causing jitter of several seconds
- **Command priority**: Not all commands are equal—engagement commands have higher priority than station adjustment commands. When bandwidth is saturated, lower priority commands are delayed to the next frame
- **Command sequence integrity guarantee**: Real systems need to guarantee command sequence integrity and order—if command #3 is delivered before command #2, it may cause contradictory states. Current per-frame independent packet loss determination has no sequence number/sorting/deduplication
- **No acknowledgment/retransmission**: Link 16 point-to-point messages have ACK/NACK mechanisms. Important commands will be retransmitted if unacknowledged. Current commands have no feedback after sending—the sender does not know if the receiver received it
- **Latency parameter is a unit-level constant**: Real latency depends on: network topology (number of hops), slot allocation period (usually 3-12 seconds), and slot offsets of sender and receiver. A command from AWACS to F-16 experiences AWACS→Link 16 slot→F-16 reception processing, total latency 0.5-6 seconds. A single `latency_s` cannot express multi-hop and slot wait structure
- **Only one command is delivered at a time**: `Pending*Command` retains only the latest command pending delivery. If the sender emits a second command before the first is delivered, the first is silently overwritten. In rapidly changing tactical situations, this may cause critical command loss

### 2.6 Communication Message System Has No Bandwidth/Electronic Warfare Constraints

The `DataLinkSystem`'s `CommPacket` distribution mechanism is lossless:

- Between any two entities on the same network + same faction + within line of sight, messages are always delivered instantly and without error
- No bandwidth cap—unlimited messages can be broadcast in a single frame
- The 0.5-second TTL clearing of messages is an engineering approximation (cleaning old inbox entries), not a real communication constraint

Real tactical communication faces:

- **Electronic warfare (jamming)**: Enemy jamming can reduce or block communications in specific frequency bands. Link 16 uses frequency-hopping spread spectrum (FHSS) to resist jamming, but data can still be lost under strong jamming
- **Relay constraints between platforms**: Not all platforms can directly communicate with all others. Beyond-line-of-sight communication requires relay nodes, introducing additional latency and single points of failure
- **Shared bandwidth between voice and data**: Actual available bandwidth is shared between data (J-series messages) and voice (encrypted digital voice)

### 2.7 Control Authority Contention Between PilotAction and MissionCommand

`DefaultControlModel::update()` lines 119-130:

```cpp
if (has_pilot) {
    // [A] Manual / RL Control ——direct stick usage
} else if (has_mission) {
    // [B] Mission-command autopilot ——convert MissionCommand to stick values
} else {
    // [C] No Command ——only SAS damping
}
```

When both `PilotAction` and `MissionCommand` exist and are active, `PilotAction` unconditionally overrides `MissionCommand`. This priority logic is not documented anywhere, and the consumer has no "conflict warning"—if the RL strategy accidentally activates PilotAction during MissionCommand execution, the autopilot is silently disabled.

Real modern aircraft (F-16, F/A-18) have explicit **autopilot/manual control mode switching** logic:

- Autopilot disengagement requires a definite pilot action (pressing the disengage button on the stick) or automatic disengagement when stick force exceeds a threshold
- When the autopilot is active, small stick movements (e.g., pilot unintentional touch) should not cause disengagement
- Restoring autopilot requires an explicit "re-engage" action

Currently there is no hysteresis, no disengagement threshold, no re-engage logic—it's simply `if (pilot && pilot->active)` switching.

### 2.8 No Rules of Engagement (ROE) State Machine

`MissionCommandCore` has `authorization_to_fire` (bool), but this is an instantaneous snapshot state, not a rule-driven state machine.

Real Rules of Engagement:

- **WEAPONS HOLD**: Fire only in self-defense (enemy has already fired or clearly demonstrates imminent intent to fire)
- **WEAPONS TIGHT**: Fire only after positively confirming target identity as hostile and having engagement authorization
- **WEAPONS FREE**: May fire on any target not identified as friend
- Transitions between states require specific conditions (IFF identification, threat assessment, commander approval), and typically have post-engagement review
- ROE state is linked with IFF state—a target classified as "suspect" cannot be engaged under WEAPONS TIGHT, but can under WEAPONS FREE

The current `authorization_to_fire` boolean compresses the entire ROE dimension into a single bit.

### 2.9 No Engagement Authority Transfer in Command Relationships

Neither the air side nor the naval side models the delegation and transfer of Engagement Authority.

In real joint operations:

- AWACS can delegate engagement authority to the flight lead of a fighter formation
- The flight lead can further delegate to wingmen
- Formal "engagement status" reports exist on the data link: ENGAGED, ENGAGING, ENGAGE (engagement permission)
- When the authorizing node is shot down or communication is lost, there is a preset succession chain for engagement authority

Current `leader_intent.authorization_to_fire` and `mission.assigned_target_id` can only express "the flight lead has assigned a target and authorized firing", but cannot express the inheritance, revocation, transfer, or succession of authority.

### 2.10 Codec Redundancy Between LeaderIntent ↔ MissionCommand

The C++ side has `MissionCommandCodec` (JSON serialization/deserialization), and the Python side has `build_kernel_mission_command()` (reconstructing MissionCommand from Python dict). The two codec paths are maintained independently:

- C++ codec in `mission_command_codec.h` / `.cpp`, responsible for `ExecutionEpisodeState::mission_command_json`
- Python builder in `air_profile.py:529`, responsible for building a MissionCommand C++ object from `leader_intent` + `loader.mission_cmd`
- The two paths differ in parsing logic for `command_code`: the Python side uses `parse_mission_command_from_dict()` to infer directly from JSON fields, while the C++ side uses `build_state_mission_command_json()` to serialize from structs. If the default values or enum mappings for a certain field differ, silent divergence can occur.

### 2.11 Formation Control Only Modeled on the Air Side—No Naval Formation Logic

`LeaderIntentAir` contains complete formation control fields: `formation_id`, `form_offset_x/y/z`, `FormationMode` (LineAbreast / EchelonLeft / EchelonRight / Wedge / Trail, etc.), `WingmanCommandMode`, `join_flag`, `split_flag`, etc.

The naval side has no equivalent – no multi-ship formation stations (sector screen / circular screen / column), no inter-ship distance maintenance, and no coordinated formation turns (simultaneous turn vs sequential turn).

Real naval formations – even the simplest two-ship screen – require:

- Station definition for the screening ship relative to the HVU (bearing + range from HVU)
- Continuous monitoring and correction of station-keeping errors
- Coordinated maneuvering when the formation changes course/speed
- Repositioning of the screening ship when the threat axis changes

Currently, the DDG-51 is placed 8 nmi ahead of the HVU and operates at the same course and speed – this is an initial geometric condition, not the product of a formation control loop.

---

## III. Summary of Air vs Naval Command Chain Differences

| Dimension | Air | Naval |
|-----------|-----|-------|
| TaskOrder-specific fields | 47 fields (runway/formation/CAP/approach) | 3 fields (warfare_role / station_type / OTC) |
| LeaderIntent-specific fields | 33 fields (formation/wingman/support anchor) | 2 fields (warfare_role / OTC) |
| MissionCommand-specific fields | 12 fields (takeoff/landing/runway/approach/formation) | None. Naval uses generic MissionCommandCore |
| command_code semantics | Full range (IDLE/TAKEOFF/VECTOR/ROUTE/LANDING) | Hardcoded to 3 (ROUTE) |
| Control model | Full FBW + autopilot (takeoff/cruise/approach modes) | None. Bridged back to heading-speed tracking via MissionCommand→MovementCommand |
| Mission phase state machine | Exists (SCRAMBLE→CAP→RTB→RECOVER_LAND) | None |
| Coordination modes | Independent / Attached / Recover | Screen / Support / Detached |
| Formation control | Complete (5 formation modes + station offsets + join/disengage) | None. Initial geometry set only by scenario JSON |
| Mission families | Transit / Patrol / Recover | Escort / Patrol / Recover |
| Post-delivery command processing | FBW autopilot consumes MissionCommand | `command_link_system.h` has a dedicated Ship→MovementCommand branch |

**Core asymmetry**: On the air side, the penetration from TaskOrder down to ControlModel is fully end-to-end (all five layers have code). On the naval side, layers 2-1 (MovementCommand → ControlModel) borrow legacy aviation code layers, and layers 5-3 have only three placeholder fields. The naval command chain is currently an "aviation pipeline with naval enums hung on top."

---

## IV. Expressions That Should Be Avoided for Now

To prevent semantic drift later, the following expressions should be explicitly avoided for now:

1. The current command chain should **not** be called "joint operations C2 simulation" – it is an **"aviation mission-based command + naval enumeration placeholders + legacy movement command pipeline"**.
2. The current `TaskOrderNaval` / `LeaderIntentNaval` should **not** be called "naval mission-based command" – they are **"shared aviation command framework + 2-3 naval enum field placeholder extensions"** with no station assignment semantics, no engagement authority delegation, and no patrol zone/threat axis modeling.
3. The current `CommandLink` should **not** be called "tactical data link command delivery simulation" – it is **"per-command fixed delay + independent packet loss probability"** with no slot contention, no command priority, no acknowledgment/retransmission, and no sequence number guarantee.
4. The current datalink message system should **not** be called "tactical communication simulation" – it is **"same-network, same-side, lossless instant message broadcast"** with no bandwidth constraints, no jamming/electronic countermeasures, and no relay requirements.
5. The current `authorization_to_fire` should **not** be called "Rules of Engagement (ROE) modeling" – it is **"a single boolean switch"** with no WEAPONS HOLD/TIGHT/FREE state machine, no IFF integration, and no engagement authority delegation.
6. The current naval command mapping should **not** be called "ship C2" – it is **"a heading-speed tracker with hardcoded command_code=3 (ROUTE)"** with no station control, no patrol zone, no threat response, and no formation coordination.

This conclusion is frozen until the command chain/C2 effort is explicitly reopened.
