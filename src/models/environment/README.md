<!-- Machine-translated draft generated on 2026-05-18 from src/models/environment/README.md. Review before treating this file as authoritative. -->

# `src/models/environment` Boundary

`models/environment` stores default implementations of environment models and environment snapshots.

## Allowed

- Model implementations such as wind, terrain, environment snapshot, etc.
- Pure computation helpers required for environment queries.

## Prohibited

- ECS system registration.
- Runtime owner or batch runtime.
- Python binding.

## Migration Notes

Environment state components belong to `components/basic` or a more specific directory; environment computation models belong to this directory.
