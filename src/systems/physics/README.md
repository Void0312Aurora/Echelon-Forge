# `src/systems/physics` Boundary

`systems/physics` contains shared physics progression logic. The canonical
air-domain runtime owner is `systems/domains/air`.

Ground contact here supports aircraft/terrain interaction and generic physics
constraints. It is not a land-domain movement model or full ground runtime.

## Allowed

- Shared systems for forces, instruments, movement, leapfrog integration, ground contact, and related areas.
- Per-frame updates to `components/physics` and terrain/ground-contact state.

## Forbidden

- Defining physics components.
- Mission/tasking state machines.
- Python bindings, facades, or batch runtime.
- Land movement, sensing, fires, or damage runtime ownership.

## Migration Notes

If some logic interprets tasking/commands and turns them into physical actions, split it carefully: DTOs belong in `components/command` or `components/tasking`, mission interpretation belongs in `core/mission`, and physical execution belongs here.

Air-only systems such as aerodynamic state, aerodynamic effects, flight control,
and propulsion are owned in `systems/domains/air`; the old `systems/physics/*` air-system
include paths have been removed.
