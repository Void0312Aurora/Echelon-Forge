# Damage-To-Control Authority Coupling Gap

Document kind: `plan`
Lifecycle: `draft`
Canonical: `docs/systems/effects/work/issues/damage_control_authority_coupling_gap/README.md`
Owner: `systems/effects`
Last verified: `2026-08-08`

Status: `2026-06-15` retained / parked. This is a real behavior-modeling gap,
but it is not the current fire-window or lethality-chain core work item.

First observed: `2026-06-15`, while reviewing whether pilot, flight-control,
command/navigation, communication, or data-link component failures actually
change subsequent aircraft controllability.

Issue class: coupling gap between component damage state, platform kill flags,
control-command authority, command-link delivery, and data-link availability.

## Summary

The current damage chain can mark pilot/crew, flight-control, propulsion, and
mission effects on the aircraft and platform damage state. However, the command
and control paths can still continue to accept or deliver control inputs after
those functional failures are recorded.

In plain terms: a report can say the pilot is ineffective, crew kill is true, or
the communication/data-link component is damaged, while the simulation may still
continue to feed `PilotAction`, `MissionCommand`, `CommandLink`, or `DataLink`
behavior as if the authority path were still usable.

This should stay visible because it can make functional kills look weaker than
they are and can let damaged targets keep maneuvering or communicating in later
steps. It should not be fixed inside the current fire-window sweep unless that
work explicitly expands to control-authority consequences.

## Current Evidence

- [damage_air.h](../../../../../../src/components/domains/air/combat/damage_air.h)
  turns `flight_control_kill` or `propulsion_kill` into zero mobility
  capability and turns `crew_kill` into zero mission capability.
- [damage_system_common.h](../../../../../../src/systems/combat/damage_system_common.h)
  maps the platform damage values to `mission_kill`, `mobility_kill`,
  `sensor_kill`, and `loss_state`.
- [default_control_model.cpp](../../../../../../src/models/domains/air/default_control_model.cpp)
  still chooses control source from `PilotAction`, active `MissionCommand`, or
  lagged control state. It does not gate those sources on `crew_kill`,
  `pilot_effectiveness`, `mission_kill`, or `mobility_kill`.
- [control_input_resolution.h](../../../../../../src/components/domains/air/command/control_input_resolution.h)
  resolves `PilotAction`, `MissionCommandControlState`, and legacy commands
  from active flags, not from damage state.
- [command_link_system.h](../../../../../../src/systems/systems/command_link_system.h)
  delivers pending movement/action/mission commands through `CommandLink`
  timing state, with no damage-state gate.
- [data_link_system.h](../../../../../../src/systems/systems/data_link_system.h)
  uses `DataLink.active`, network id, range, horizon, and alliance matching; it
  does not appear to disable link behavior because a communication or avionics
  component was damaged.

## Impact

- Pilot or crew kills may be represented in reports without stopping manual or
  scripted control authority.
- Flight-control kills can degrade flight performance, but the controller can
  still try to command the aircraft.
- Communication or data-link damage may reduce mission or avionics capability
  without disabling command delivery, track sharing, or message exchange.
- Training and evaluation may underestimate functional kills if they only check
  physical destruction or if the damaged target keeps acting after a control
  authority failure.

## Non-Claims

- This issue does not say the current damage-chain probability work is invalid.
- This issue does not authorize a broad command/control rewrite.
- This issue does not require adding trajectory randomness to the current fire
  timing analysis.
- This issue does not claim every crew or communication hit must immediately
  destroy the target.

## Possible Follow-Up Gates

1. Define separate consequence rules for manned aircraft, UAVs, missiles, and
   autonomous platforms.
2. Decide what should happen when `crew_kill`, `flight_control_kill`,
   `mission_kill`, or communication/data-link component failures occur:
   disable input, hold last command, degrade control authority, force recovery,
   or mark uncontrollable.
3. Add explicit gates in control-input resolution, command-link delivery, and
   data-link sharing instead of relying only on report fields.
4. Add tests proving that a pilot/crew kill, flight-control kill, and data-link
   kill each change subsequent behavior in the intended way.
5. Keep fire-window and lethality-chain diagnostics reporting functional kills
   separately from physical destruction.

## Closure Criteria

- Functional kills have defined behavior consequences, not just report flags.
- Pilot/crew, flight-control, command/navigation, communication, and data-link
  failures have at least smoke-level runtime tests.
- Training/evaluation diagnostics distinguish destroyed, mission kill, mobility
  kill, crew kill, and control-authority loss.
- The follow-up does not silently weaken existing damage reports or legality
  gates.
