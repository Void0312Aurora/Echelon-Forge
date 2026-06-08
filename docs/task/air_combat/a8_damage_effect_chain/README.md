# A8 Damage Effect Chain

Status: `2026-06-08` active implementation. The shot record, part-failure
vocabulary, public failure-mode rows, propulsion-consumer slice, one
wing/control aerodynamic-consumer slice, and fixed fuel-leak/mass-response
evidence are in place.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task: [../README.md](../README.md)
- Sealed damage-model record:
  [../a2_high_fidelity_damage_model/README.md](../a2_high_fidelity_damage_model/README.md)
  and [../archive/a2_high_fidelity_damage_model/README.md](../archive/a2_high_fidelity_damage_model/README.md)
- Subproject creation standard:
  [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Subagent usage policy:
  [../../../standards/governance/subagent_usage_policy.md](../../../standards/governance/subagent_usage_policy.md)
- Damage and effects code entry points:
  [damage.h](../../../../src/components/combat/damage.h),
  [damage_system.h](../../../../src/systems/combat/damage_system.h),
  [default_effects_model.cpp](../../../../src/models/weapons/default_effects_model.cpp)
- Flight and propulsion consumers:
  [aerodynamics_system.h](../../../../src/systems/physics/aerodynamics_system.h),
  [propulsion_system.h](../../../../src/systems/physics/propulsion_system.h)
- MQ-9 / AIM-120C fixtures:
  [mq9_reaper.json](../../../../examples/config/database/aircraft/units/mq9_reaper.json),
  [aim_120c.json](../../../../examples/config/database/weapons/air_to_air/aim_120c.json)

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
| Flight and propulsion consumers | active implementation | Propulsion consumes damage even when explicit engine tuning is enabled; aerodynamics now consumes structural, hydraulic, axis-control, and asymmetry damage as limited coefficient/authority changes. | The aero response is still synthetic and scalar; it is not aircraft-specific control-law calibration. |
| Fuel and mass consumers | active evidence | A fixed center-fuel-cell hit now exposes fuel-leak and fire-source modes, then drains fuel and mass through the maintained runtime path. | This is leak/mass and fire-risk evidence, not a full fire-spread or crash lifecycle. |
| Test evidence | active | MQ-9/AIM-120C fixed checks, public failure-mode guards, a tuned-engine propulsion damage check, fixed MQ-9 right-aileron short/long response checks, and a fixed center-fuel-cell leak/mass response check exist. | Runtime tests are engineering checks, not real-world lethality evidence. |

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
| `P4 Consumer Integration` | Feed concrete damage into propulsion, fuel, sensors, fire, and flight forces. | P3 effects exist. | Engine, wing/control, fuel, and sensor damage alter the maintained simulation paths. | partial: propulsion, wing/control aero, and fuel-leak/mass evidence pass |
| `P5 Scenario Validation` | Prove the chain with fixed MQ-9 / AIM-120C cases. | P4 implementation passes focused tests. | Tests explain rear, wing/control, fuel, and sensor/data-link outcomes over time. | partial pass: includes fixed fuel-leak/mass case |
| `P6 Acceptance` | Decide accepted or held and record residuals. | P5 evidence complete. | Parent README and status docs state the honest capability and remaining gaps. | planned |

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
  plus the fifth-wave acceptance in
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md).

## Outputs And Evidence

Expected outputs:

- A shot effect record that can be inspected from tests and debug APIs.
- Component damage records that name the kind of physical or functional damage.
- Updated propagation from component damage into existing propulsion, fuel/mass,
  sensor, fire, and flight/aerodynamic consumers.
- Focused MQ-9 / AIM-120C regression tests for rear-engine, wing/control,
  fuel/leak/mass, fire-risk, and sensor/data-link cases.
- Documentation that keeps estimated engineering behavior separate from real
  weapon lethality claims.

## Acceptance Gate

This subproject can be marked accepted only when:

- Structured aircraft no longer rely on direct health subtraction as the primary
  explanation for missile effects.
- A recorded shot explains the chain from fuze through damaged part and later
  aircraft behavior.
- Engine or propeller damage affects thrust through the propulsion path.
- Wing, control-surface, or structural damage affects aerodynamic/control
  behavior through the maintained flight path.
- Fuel damage affects leak, mass, fire risk, or supply behavior through existing
  fuel and fire paths.
- MQ-9 / AIM-120C tests verify both the immediate damage record and the later
  aircraft response.
- Documentation still refuses real-world kill probability, deterministic fuze,
  or stock AIM-120C/MQ-9 lethality claims.

## Residuals And Next Steps

- Public shot rows, concrete part-failure vocabulary, fixed MQ-9/AIM-120C
  checks, the tuned-engine propulsion consumer, one wing/control aerodynamic
  consumer, and one center-fuel-cell leak/mass runtime check are integrated.
- The next runtime step should broaden consumer coverage only through existing
  maintained systems, with particular care around broader fire behavior,
  sensor/data-link consequences, and aircraft-specific control-law calibration.
- Long-run right-aileron damage can drive the damaged MQ-9 to near-ground
  response while the clean baseline holds level flight, but ground-impact crash
  propagation is still not implemented as a maintained outcome. The current
  ground-contact path needs a public lifecycle state or residue surface before
  it can be accepted as more than immediate deletion/loss.
- Full calibration of fragment patterns, blast loads, target vulnerability, and
  aircraft-specific failure thresholds remains deferred.

## Archive

Current A8 records are live. Superseded scans, rejected chains, or dated probes
move to [archive/README.md](archive/README.md) only after a replacement current
status or acceptance surface exists.
