# `src/systems/physics` Boundary

`systems/physics` contains the progression logic for physics, the mature air/flight state path, and shared ground-contact primitives.

Ground contact here supports aircraft/terrain interaction and generic physics
constraints. It is not a land-domain movement model or full ground runtime.

## Allowed

- Systems for aerodynamics, control, forces, instruments, movement, leapfrog integration, ground contact, and related areas.
- Per-frame updates to `components/physics`, aviation models, and terrain/ground-contact state.

## Forbidden

- Defining physics components.
- Mission/tasking state machines.
- Python bindings, facades, or batch runtime.
- Land movement, sensing, fires, or damage runtime ownership.

## Migration Notes

If some logic interprets tasking/commands and turns them into physical actions, split it carefully: DTOs belong in `components/command` or `components/tasking`, mission interpretation belongs in `core/mission`, and physical execution belongs here.
