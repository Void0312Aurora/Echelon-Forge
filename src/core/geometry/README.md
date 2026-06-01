# `src/core/geometry` Boundaries

`core/geometry` holds the runtime for spatial queries and geometry assistance. It serves simulation, sensor, visual, or mission queries, but does not own the world lifecycle.

## Allowed

- Spatial query runtime.
- Geometry query, auxiliary computations such as distance/line-of-sight/proximity relationships.
- Pure C++ query services callable by `core/engine` or `systems/`.

## Prohibited

- ECS system registration.
- Mission episode state machine.
- Python binding or facade.
- GPU kernel implementation.

## Migration Notes

If a query begins to depend on the lifecycle of a specific world owner, ownership should be kept in `core/engine`, and this directory should only retain the query service implementation.
