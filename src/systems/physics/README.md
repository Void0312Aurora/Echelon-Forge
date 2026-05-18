# `src/systems/physics` Boundary

`systems/physics` contains the progression logic for physics and flight state.

## Allowed

- Systems for aerodynamics, control, forces, instruments, movement, leapfrog integration, ground contact, and related areas.
- Per-frame updates to `components/physics` and aviation models.

## Forbidden

- Defining physics components.
- Mission/tasking state machines.
- Python bindings, facades, or batch runtime.

## Migration Notes

If some logic interprets tasking/commands and turns them into physical actions, split it carefully: DTOs belong in `components/command` or `components/tasking`, mission interpretation belongs in `core/mission`, and physical execution belongs here.
