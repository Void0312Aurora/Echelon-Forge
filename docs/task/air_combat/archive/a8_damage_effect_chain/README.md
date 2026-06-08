# A8 Damage Effect Chain

Status: `archived on 2026-06-08 / accepted with deferred residuals`.

A8 is accepted for the bounded damage-effect-chain slice: public shot rows,
concrete synthetic failure modes, and fixed MQ-9/AIM-120C-like cases now
explain the path from detonation to damaged part and maintained-system response.
Covered responses include propulsion, wing/control aerodynamics, fuel/leak/mass,
broader fire, data-link mission/sensor degradation, and original-entity
ground-contact lifecycle observability.

The original path `docs/task/air_combat/a8_damage_effect_chain/` is now a
lightweight pointer README only.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent archive index: [Air Combat Archive](../README.md)
- Parent air-combat task: [Air Combat](../../README.md)
- Sealed damage-model record:
  [a2_high_fidelity_damage_model pointer](../../a2_high_fidelity_damage_model/README.md)
  and [a2_high_fidelity_damage_model archive](../a2_high_fidelity_damage_model/README.md)
- Subproject creation standard:
  [Subproject Creation Standard](../../../../agent/rules/subproject_creation_standard.md)
- Subagent usage policy:
  [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)
- Damage and effects code entry points:
  [damage.h](../../../../../src/components/combat/damage.h),
  [damage_system.h](../../../../../src/systems/combat/damage_system.h),
  [default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- Flight and propulsion consumers:
  [aerodynamics_system.h](../../../../../src/systems/physics/aerodynamics_system.h),
  [propulsion_system.h](../../../../../src/systems/physics/propulsion_system.h)
- MQ-9 / AIM-120C fixtures:
  [mq9_reaper.json](../../../../../examples/config/database/aircraft/units/mq9_reaper.json),
  [aim_120c.json](../../../../../examples/config/database/weapons/air_to_air/aim_120c.json)

## Purpose

A2 left a useful structured damage runtime, but recent AIM-120C versus MQ-9
checks show that a recorded hit can still be hard to explain as a physical
sequence. This subproject standardizes the path from detonation to aircraft
behavior: what the warhead did, which part of the aircraft it damaged, which
function degraded, and how the existing flight, propulsion, fuel, and sensor
systems then expressed the result.

The goal is not a new "shot down" switch. A damaged engine should reduce thrust
through the propulsion path; a damaged control actuator should reduce roll,
pitch, or yaw control through the flight path; a damaged fuel cell should leak,
burn, or change mass over time. The final outcome is observed after the aircraft
simulation responds.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Fuze and detonation records | active input | `damage_system.h` records proximity/contact fuze state and forwards detonations into the effects model. | A recorded detonation does not prove the damage sequence is complete. |
| Part-level damage inventory | active input | `damage.h` plus MQ-9 JSON define hit boxes, named parts, groups, and dependencies. | The names are engineering scaffolds until calibrated data replaces them. |
| Warhead-to-part effect model | primary cut point | `default_effects_model.cpp` and detail files compute mechanism loads, affected components, and current failure probability. | This is the first implementation cut point, but the current values are estimates, not AIM-120C truth. |
| Damage-to-aircraft state | active input | `AircraftDamageStateUpdate` maps parts into propulsion, fuel, sensors, fire, and broad flight limits. | Keep this as the downstream bridge; do not replace it with a direct kill rule. |
| Flight and propulsion consumers | accepted slice | Propulsion consumes damage even when explicit engine tuning is enabled; aerodynamics now consumes structural, hydraulic, axis-control, and asymmetry damage as limited coefficient/authority changes. | The aero response is still synthetic and scalar; it is not aircraft-specific control-law calibration. |
| Fuel and mass consumers | accepted evidence | A fixed center-fuel-cell hit now exposes fuel-leak and fire-source modes, then drains fuel and mass through the maintained runtime path. | This is leak/mass and fire-risk evidence, not a full fire-spread or crash lifecycle. |
| Fire consumers | accepted evidence | A fixed left-wing fuel-cell hit grows fire and secondary damage; a rear-engine hit seeds engine fire-zone state and later propulsion loss without requiring fire growth when no flammable exposure exists. | This is deterministic engineering evidence, not calibrated fire truth. |
| Sensor and data-link consumers | accepted evidence | A fixed data-link transceiver hit exposes `data_loss`, remains non-authoritative, and later reduces mission/sensor/survivability plus avionics/crew/navigation state through maintained platform damage. | This proves a mission/sensing consequence, not active MQ-9 message traffic or a crash requirement. |
| Ground-contact lifecycle | accepted slice | Ground contact now exposes `landed_airframe` versus `crashed_wreck` state through a debug surface, with tests for safe runway contact, severe impact, and low-speed non-crash contact. | This is accepted as original-entity observability for A8; first-class debris/residue objects are deferred. |
| Test evidence | accepted evidence | MQ-9/AIM-120C fixed checks, public failure-mode guards, a tuned-engine propulsion damage check, fixed MQ-9 right-aileron short/long response checks, fixed center-fuel-cell leak/mass response, fixed broader-fire response, fixed data-link mission/sensor response, and ground-contact lifecycle checks exist. | Runtime tests are engineering checks, not real-world lethality evidence. |
| Deferred residuals | deferred | P6 explicitly defers calibrated warhead/fire/target-vulnerability truth, aircraft-specific control-law fidelity, platform-family expansion, real-world Pk/fuze/stock lethality authority, and first-class debris/residue objects. | These are outside the accepted A8 slice and require separate data/model admission. |

## Scope

In scope:

- Define a standard shot effect record that explains each shot in plain stages:
  fuze, detonation point, warhead action, affected aircraft part, functional
  change, and later flight/propulsion/sensor response.
- Normalize damage effect types such as cut, puncture, blast deformation, fuel
  leak, hydraulic loss, electrical loss, data loss, fire source, and structural
  weakening.
- Connect part damage to existing consumers: propulsion, fuel and mass, sensor,
  fire spread, and the flight/aerodynamic force path.
- Add fixed MQ-9 / AIM-120C tests that check the sequence, not only the final
  alive/dead result.
- Keep legacy health values as a compatibility readout only for structured
  aircraft.

Out of scope:

- A direct "hit means crash" or "AIM-120C always kills MQ-9" rule.
- A separate "can maintain flight" decision that bypasses the flight and
  propulsion systems.
- Real-world probability of kill, deterministic fuze truth, classified weapon
  data, or a claim that current AIM-120C values are authoritative.
- Broad aircraft-data calibration beyond the narrow engineering scaffolds needed
  to make the effect chain inspectable.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Create the follow-on work surface without changing runtime behavior. | User requested a standard damage-effect chain and subproject. | README, current status, task clusters, archive index, and parent links exist. | pass |
| `P1 Structure Evidence` | Confirm the current hit, effect, part, and flight-consumer structure. | P0 docs exist. | Read-only findings identify code entry points, gaps, and safe write sets. | pass for planning |
| `P2 Shot Effect Record` | Define the per-shot record that explains what happened and why. | P1 confirms fields and consumers. | Tests can assert fuze, detonation, part effect, and consequence stages. | pass |
| `P3 Part Effect Vocabulary` | Represent physical damage types instead of one generic damage amount. | P2 record is stable. | Component damage records can name leaks, cuts, fire sources, data loss, and structure weakening. | pass |
| `P4 Consumer Integration` | Feed concrete damage into propulsion, fuel, sensors, fire, and flight forces. | P3 effects exist. | Engine, wing/control, fuel, sensor, and fire damage alter the maintained simulation paths. | pass for accepted A8 slice; calibration/platform expansion deferred |
| `P5 Scenario Validation` | Prove the chain with fixed MQ-9 / AIM-120C cases. | P4 implementation passes focused tests. | Tests explain rear, wing/control, fuel/fire, and sensor/data-link outcomes over time. | pass for fixed MQ-9/AIM-120C-like cases; real lethality/Pk deferred |
| `P6 Acceptance` | Decide accepted or held and record residuals. | P5 evidence complete. | Parent README and status docs state the honest capability and remaining gaps. | accepted with deferred residuals |

## Task Clusters

- Task cluster plan:
  [a8_damage_effect_chain_task_clusters_20260607.md](a8_damage_effect_chain_task_clusters_20260607.md)
- Current status:
  [a8_damage_effect_chain_current_status_20260607.md](a8_damage_effect_chain_current_status_20260607.md)
- Dispatch queue:
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- Latest implementation notes:
  [a8_w7_propulsion_tuning_consumer_20260608.md](a8_w7_propulsion_tuning_consumer_20260608.md)
  and [a8_w8_aero_consumer_20260608.md](a8_w8_aero_consumer_20260608.md)
  plus the ninth-wave P6 acceptance in
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md).

## Outputs And Evidence

Expected outputs:

- A shot effect record that can be inspected from tests and debug APIs.
- Component damage records that name the kind of physical or functional damage.
- Updated propagation from component damage into existing propulsion, fuel/mass,
  sensor, fire, and flight/aerodynamic consumers.
- Focused MQ-9 / AIM-120C regression tests for rear-engine, wing/control,
  fuel/leak/mass, fire behavior, and sensor/data-link cases.
- Documentation that keeps estimated engineering behavior separate from real
  weapon lethality claims.

## Archived Acceptance Gate

This package is sealed with bounded acceptance:

- structured aircraft no longer rely on direct health subtraction as the primary
  explanation for this missile-effect chain;
- recorded shots explain the chain from fuze through damaged part and later
  aircraft behavior;
- engine, wing/control, fuel, fire, sensor/data-link, and ground-contact
  responses are covered by focused maintained-system evidence;
- MQ-9 / AIM-120C-like tests verify both the immediate damage record and later
  aircraft response;
- documentation still refuses real-world kill probability, deterministic fuze,
  or stock AIM-120C/MQ-9 lethality claims.

Calibration-grade warhead/fire/target truth, aircraft-specific control-law
fidelity, platform-family expansion, real-world Pk/fuze/stock lethality
authority, and first-class debris/residue objects remain deferred.

## Residuals And Next Steps

- Public shot rows, concrete part-failure vocabulary, fixed MQ-9/AIM-120C
  checks, the tuned-engine propulsion consumer, one wing/control aerodynamic
  consumer, one center-fuel-cell leak/mass runtime check, one broader-fire
  runtime check pair, one data-link mission/sensor runtime check, and one
  ground-contact lifecycle surface are integrated.
- Long-run right-aileron damage can drive the damaged MQ-9 to near-ground
  response while the clean baseline holds level flight. Severe ground contact
  can now be observed as `crashed_wreck`, while safe or low-speed contact stays
  observable as `landed_airframe`.
- Debris/residue entities are deferred; original-entity `landed_airframe` /
  `crashed_wreck` observability is accepted for this A8 slice.
- Full calibration of fragment patterns, blast loads, target vulnerability,
  release-grade fire truth, aircraft-specific control-law behavior, and
  platform-family thresholds remains deferred.

## Archive

- Closeout:
  [a8_damage_effect_chain_closeout_20260608.md](a8_damage_effect_chain_closeout_20260608.md)
- Parent archive index: [Air Combat Archive](../README.md)
- Pointer README:
  [a8_damage_effect_chain](../../a8_damage_effect_chain/README.md)
- Internal superseded-note archive: [archive/README.md](archive/README.md)
