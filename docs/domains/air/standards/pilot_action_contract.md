# Pilot Action Contract

Language:
- English canonical: `pilot_action_contract.md`
- Chinese companion: [pilot_action_contract.zh.md](pilot_action_contract.zh.md)

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/domains/air/standards/pilot_action_contract.md`
Owner: `domains/air`
Last verified: `2026-08-08`

Status: specialization baseline for maintained air action input,
including the A5 runtime event-action overlay; this page does not by itself
accept learned-policy behavior.

This document defines the maintained air action surface for the current
repository. It is an interface contract, not a cockpit encyclopedia.

## Scope

The maintained action surface has two layers:

1. environment-facing action vectors
2. kernel-facing `PilotAction`

Primary references:

- [gym_envs/universal_env_parts/actions.py](../../../../gym_envs/universal_env_parts/actions.py)
- [gym_envs/universal_env_parts/spaces.py](../../../../gym_envs/universal_env_parts/spaces.py)
- [gym_envs/universal_env_parts/air_combat_event_action.py](../../../../gym_envs/universal_env_parts/air_combat_event_action.py)
- [src/components/command/pilot_action.h](../../../../src/components/command/pilot_action.h)
- [src/components/domains/air/command/control_input_resolution.h](../../../../src/components/domains/air/command/control_input_resolution.h)
- [tests/runtime/core/test_air_combat_hybrid_action.py](../../../../tests/runtime/core/test_air_combat_hybrid_action.py)
- [tests/runtime/air_combat/test_fire_action_release_gate.py](../../../../tests/runtime/air_combat/test_fire_action_release_gate.py)

## Action Modes

The Air action modes covered by this standard are:

| Mode | Dim | Purpose |
| :--- | ---: | :--- |
| `full` | 17 | full maintained action surface |
| `takeoff2` | 2 | reduced takeoff curriculum surface |
| `takeoff4` | 4 | reduced takeoff surface with lateral controls |
| `air_combat_hybrid_v1` | 12 | `1v1` air-combat training surface with continuous flight axes plus hybrid combat-command semantics |

`takeoff2` and `takeoff4` are training-oriented reduced interfaces. They do not
expose the full `PilotAction` surface directly.

`air_combat_hybrid_v1` is also a training-oriented surface. It keeps a flat
numeric transport vector for PPO/runtime compatibility, but its policy contract
is hybrid: selected dimensions are sampled and interpreted as Bernoulli switches,
one-step pulses, or categorical selectors rather than raw continuous cockpit
axes.

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

## `air_combat_hybrid_v1` Mode Mapping

The maintained `air_combat_hybrid_v1` transport vector maps as follows:

- `0`: `stick_pitch` continuous axis
- `1`: `stick_roll` continuous axis
- `2`: `rudder` continuous axis
- `3`: `throttle` continuous axis
- `4`: `radar_scan_az`, mapped to `+/-60 deg`
- `5`: `radar_scan_el`, mapped to `+/-30 deg`
- `6`: `radar_active` Bernoulli switch state
- `7`: `tms_up` one-step pulse generated from policy-command rising edge
- `8`: `master_arm` Bernoulli switch state
- `9`: `fire_weapon` one-step pulse generated from policy-command rising edge
- `10`: `fire_gun` one-step pulse generated from policy-command rising edge
- `11`: `weapon_select_id` categorical selector in `[0, 7]`

The `proprio` and `proprio_history` observations for this mode record the
effective transport action sent toward `PilotAction`, not the raw policy intent.
For pulse dimensions, a held policy command therefore appears as `1` only on the
rising-edge step and `0` on subsequent held steps.

## A5 Constrained Event-Action Overlay

Status: `2026-06-10` implementation contract for the A5 S1 C2/ROE
event-action runtime surface. This section freezes field names for the runtime
surface; it does not mark learned-policy behavior as accepted.

For scenarios that opt into the maintained A5 S1 C2/ROE contract,
`fire_weapon` is not treated as a raw policy-facing per-step threshold. Weapon
release is modeled as an event action:

```text
event_action in {hold, fire_once}
event_action_mask = [1, fire_mask]
```

The event-action overlay may still be transported through a flat action vector
for PPO/runtime compatibility, but policy log-prob, entropy, stochastic sampling,
and deterministic evaluation must use the masked event semantics.

Policy-visible event state:

| `engagement_state` | Meaning | Event support |
| :--- | :--- | :--- |
| `Hold` | C2/ROE, target, weapon, or mission state does not allow release. | `hold` only |
| `AuthorizedReady` | First-shot release is authorized and available. | `hold`, `fire_once` |
| `FiredAssess` | A release was accepted and assessment is pending. | `hold` only |
| `ReattackReady` | Follow-on release is explicitly authorized after assessment. | `hold`, `fire_once` |
| `Winchester` | No valid weapon remains or release path is unavailable. | `hold` only |

The final `fire_mask` must be derived from named components, including C2/ROE
authorization, target presence, shot budget, pending assessment, weapon/ammo
readiness, and reattack permission. Diagnostics should expose both the final
mask and the component or rejection reason that made `fire_once` unavailable.

Required runtime info names for A5 implementation:

- `engagement_state`
- `fire_mask`
- `fire_once_requested`
- `fire_once_accepted`
- `fire_once_rejected_reason`
- `release_executed`
- `post_launch_suppressed`
- `reattack_ready`

Minimum transition rule:

```text
AuthorizedReady + fire_once + fire_mask
  -> consume one release event
  -> enter FiredAssess
  -> suppress fire_once until explicit ReattackReady or a new authorization cycle
```

This overlay is intentionally separate from reward shaping. Rewards may value
outcome, timing, ammo cost, and tracking quality, but rewards should not be the
primary mechanism for teaching release legality, shot budget, or post-launch
suppression.

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
- In `air_combat_hybrid_v1`, `tms_up`, `fire_weapon`, and `fire_gun` are
  policy-facing pulse commands. Holding the policy command high does not keep the
  corresponding `PilotAction` trigger high after the first effective step.

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
