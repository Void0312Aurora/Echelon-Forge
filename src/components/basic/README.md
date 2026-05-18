<!-- Machine-translated draft generated on 2026-05-18 from src/components/basic/README.md. Review before treating this file as authoritative. -->

# `src/components/basic` Boundaries

`components/basic` stores the lowest-level, cross-domain shared ECS components and tags.

## Allowed

- Basic state such as identity, side, position, lifecycle tag, etc.
- Lightweight components from environmental data that must be stored with the entity.
- Stable foundational fields that are commonly read by multiple systems.

## Prohibited

- Physics, combat, sensor, or task-specific state.
- Command/tasking DTOs.
- Runtime, system, or binding logic.

## Migration Notes

If a new field only serves a single business domain, it should be placed in the corresponding business directory instead of being put into `basic` to form an implicit global clutter layer.
