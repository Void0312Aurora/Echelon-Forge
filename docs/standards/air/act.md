# Pilot Action Contract

Language:
- English canonical: `act.md`
- Chinese companion: [act.zh.md](act.zh.md)

Status: `2026-05-18` specialization baseline for maintained air action input.

This document defines the maintained air action surface for the current
repository. It is an interface contract, not a cockpit encyclopedia.

## Scope

The maintained action surface has two layers:

1. environment-facing action vectors
2. kernel-facing `PilotAction`

Primary references:

- [gym_envs/universal_env_parts/actions.py](../../../gym_envs/universal_env_parts/actions.py)
- [gym_envs/universal_env.py](../../../gym_envs/universal_env.py)
- [src/components/command/pilot_action.h](../../../src/components/command/pilot_action.h)
- [src/components/command/air/control_input_resolution.h](../../../src/components/command/air/control_input_resolution.h)

## Action Modes

The maintained environment modes are:

| Mode | Dim | Purpose |
| :--- | ---: | :--- |
| `full` | 17 | full maintained action surface |
| `takeoff2` | 2 | reduced takeoff curriculum surface |
| `takeoff4` | 4 | reduced takeoff surface with lateral controls |

`takeoff2` and `takeoff4` are training-oriented reduced interfaces. They do not
expose the full `PilotAction` surface directly.

## `full` Mode Mapping

The maintained `full` action vector maps as follows:

- `0`: `stick_pitch`
- `1`: `stick_roll`
- `2`: `rudder`
- `3`: `throttle`
- `4`: `gear_handle`
- `5`: `flaps`
- `6`: `speedbrake`
- `7-8`: brake inputs folded into `brake`
- `9`: `radar_active`
- `10`: `radar_scan_az`
- `11`: `radar_scan_el`
- `12`: `tms_up`
- `13`: `master_arm`
- `14`: `fire_weapon`
- `15`: `fire_gun`
- `16`: `weapon_select_id`

## Canonical `PilotAction` Fields

The kernel-facing `PilotAction` fields currently exposed are grouped as:

### Continuous Axes

- `stick_pitch`
- `stick_roll`
- `rudder`
- `throttle`
- `gear_handle`
- `flaps`
- `speedbrake`
- `brake`
- `radar_scan_az`
- `radar_scan_el`

### Switches And Triggers

- `brake_left`
- `brake_right`
- `radar_active`
- `tms_up`
- `master_arm`
- `fire_weapon`
- `fire_gun`
- `jettison_emergency`
- `program_chaff`
- `program_flare`

### Selectors And Validity

- `weapon_select_id`
- `active`

## Interpretation Rules

- `normalize_action()` enforces shape and clipping at the environment boundary.
- `flaps`, `speedbrake`, and `brake` are normalized through helper logic before
  entering `PilotAction`.
- `radar_scan_az` and `radar_scan_el` are environment-normalized inputs mapped
  into angle values for the kernel-facing action.
- `weapon_select_id` is a selector, not a continuous control axis.

## Reduced-Mode Overrides

`takeoff2` and `takeoff4` do not just expose fewer fields; they also apply
automatic overrides:

- unspecified fields are zeroed or disabled
- the reduced modes still emit a valid `PilotAction`
- `gear_handle` is automatically managed based on current radar altitude

These modes are therefore training convenience surfaces layered on top of the
same runtime action carrier.

## Protection And Gate Rules

The maintained action contract includes several interpretation rules that are
not raw player controls:

- `PilotAction.active` gates whether the action is treated as valid
- `PilotAction` takes precedence over legacy movement-command fallbacks where
  the runtime resolves between them
- left/right brake flags may force full brake behavior on the ground-control
  side
- weapon release still depends on downstream command/ROE/runtime checks in
  addition to `master_arm` and `fire_weapon`

## Ownership Boundary

Keep in air specialization:

- stick/throttle/gear/flaps/speedbrake semantics
- radar scan controls exposed directly to the pilot surface
- weapon-selection and trigger semantics at the pilot interface
- reduced takeoff curriculum action modes

Keep out of this document:

- joint/common command relationships
- service-level tasking doctrine
- low-level aerodynamic, propulsion, or weapon model implementation details

## Non-Goals

This document does not standardize a `trim_pitch` field, an explicit human
smoothness model, or a full avionics HOTAS manual. If the runtime does not
currently expose a field through `PilotAction` or the maintained environment
surface, it should not be presented here as part of the maintained contract.
