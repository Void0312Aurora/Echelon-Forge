# `src/systems/domains/air` Boundary

`systems/domains/air` owns per-tick air-domain runtime systems for flight control,
aerodynamic state, propulsion state, and aerodynamic force/moment effects.
These systems consume shared physics components, command bridge state, and
air-specific tuning/damage state, but they are not shared physics primitives.

## Allowed

- Air vehicle control, propulsion, aerodynamic state, lift/drag, and aero moment updates.
- Consumption of `components/domains/air/platform`, `components/physics`, and
  maintained air command bridges.
- Air-specific damage effects that directly alter flight dynamics.

## Forbidden

- Shared integration primitives such as force clearing, leapfrog integration, or ground contact.
- Naval or ground platform movement, sensing, fires, or damage ownership.
- Defining ECS components, command/tasking DTOs, Python bindings, facades, or batch runtime owners.

## Current Files

- [aero_state_system.h](aero_state_system.h)
  - Computes air-relative AoA, sideslip, dynamic pressure, and Mach state.
- [aerodynamics_system.h](aerodynamics_system.h)
  - Applies air-domain lift, drag, aero moments, stall, and aircraft damage effects.
- [control_system.h](control_system.h)
  - Bridges flight command state into the replaceable air control model.
- [propulsion_system.h](propulsion_system.h)
  - Advances jet propulsion spool, thrust, afterburner, and fuel-basis helper state.

## Removed Legacy Entries

The old `systems/physics/{aero_state,aerodynamics,control,propulsion}_system.h`
include paths have been removed. Code that needs air runtime systems must
include this directory directly.
