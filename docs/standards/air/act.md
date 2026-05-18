<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/act.zh.md. Review before treating this file as authoritative. -->

<!-- Machine-translated draft generated on 2026-05-18 from docs/standards/air/act.md. Review before treating this file as authoritative. -->

# Pilot Action Space Standard

> Scope note (2026-03-23): This document is an `air specialization` and applies only to platform execution action semantics under the air profile.
> Please first refer to [docs/standards/README.md](../README.md),
> [docs/standards/services/air_force.md](../services/air_force.md),
> [docs/standards/air/README.md](README.md) for the current standardized main baseline.

This document defines the operational commands that a "digital pilot" (RL Agent) can apply to the simulation environment. These operations strictly simulate the physical actions a real fighter pilot can perform in the cockpit via the control stick, throttle lever, and various electromagnetic switches.

It does not define:

- Task organization of joint/common core
- Service hierarchical structure
- Execution action standards for naval or ground warfare

## 1. Primary Controls
The most frequent operations, directly affecting the aircraft's aerodynamic surfaces.

| Action Name | Description | Value Range | Physical Meaning |
| :--- | :--- | :--- | :--- |
| `stick_pitch` | Elevator/horizontal stabilizer control | [-1.0, 1.0] | Pulling back is positive (pitch up), pushing forward is negative (pitch down) |
| `stick_roll` | Aileron control | [-1.0, 1.0] | Banking left is negative, banking right is positive |
| `rudder_pedals` | Rudder/nose wheel steering control | [-1.0, 1.0] | Left pedal is negative, right pedal is positive |
| `throttle_lever` | Throttle lever position | [0.0, 1.0] | 0.0-0.8 is military power, 0.8-1.0 is afterburner (AB) |

## 2. Secondary Controls
Used to adjust aircraft configuration and assist flight.

| Action Name | Description | Value Range | Remarks |
| :--- | :--- | :--- | :--- |
| `gear_handle` | Landing gear handle | {0, 1} | 0 is retract, 1 is extend |
| `flaps_switch` | Flaps switch | {Up, Takeoff, Landing} | Selector control |
| `speedbrake_switch` | Speed brake handle | {Retract, Extend} | Discrete or continuous control |
| `trim_pitch` | Pitch trim | [-1.0, 1.0] | Adjusts neutral stick pressure |

## 3. Sensors & Avionics
Manages information acquisition equipment.

| Action Name | Description | Value Range | Remarks |
| :--- | :--- | :--- | :--- |
| `radar_power` | Radar power/mode | {Off, Standby, On} | |
| `radar_scan_elevation` | Radar elevation scan center | degrees (deg) | |
| `radar_scan_azimuth` | Radar azimuth scan width | degrees (deg) | |
| `target_lock_btn` | Lock button (TMS Up) | Trigger | Used to designate a tracked target |

## 4. Weapon Management
Core operations for tactical execution.

| Action Name | Description | Value Range | Remarks |
| :--- | :--- | :--- | :--- |
| `master_arm_switch` | Master arm switch | {Safe, Arm} | |
| `weapon_select` | Weapon cycle selection | Discrete ID | Gun, short-range missile, medium-range missile |
| `pickle_btn` | Missile launch / bomb release | Trigger | |
| `trigger_btn` | Gun trigger | Hold | |
| `jettison_emergency` | Emergency jettison external tanks/stores | Trigger | Current `PilotAction` field; usually a red emergency button |

## 5. Operational Specifications
1.  **Continuity**: Control stick (`stick_pitch/roll`) and throttle (`throttle`) must be handled as continuous actions to simulate physical feedback.
2.  **Physical Latency**: There will be slight delays and physical constraints from pilot input through the on-board flight control system (FBW) to the actuators.
3.  **Safety**: The AI should not issue abrupt commands beyond human physical limits (e.g., going from full throttle to idle in 0.01 seconds); the model must incorporate smooth characteristics of human operation.
