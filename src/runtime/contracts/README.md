# `src/runtime/contracts` Boundary

`runtime/contracts` stores the stable DTOs shared between `runtime/facade` and lower-level runtime owners. Types here may be referenced by the facade, engine, Python bindings, and tests, but they must not own world state, ECS registries, or system scheduling logic.

## Allowed

- Lightweight references such as `WorldEntityRef`.
- DTOs for batch setup, commands, tasking, and episode-step requests.
- Request/result types composed only of value types, component DTOs, and mission runtime DTOs.

## Forbidden

- `SimulationKernel`, `WorldBatchRuntime`, or other owner classes.
- Flecs system registration, step scheduling, or GPU helper implementations.
- Python/nanobind binding logic.
- Pulling in `core/engine/*` just for include convenience.

## Migration Notes

This directory is the likely starting point for a future `ef_contracts` target. New facade-facing types should be placed here first and then consumed by the facade or engine implementation.
