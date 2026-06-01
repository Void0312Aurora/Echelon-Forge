# `src/models/environment` Boundary

`models/environment` stores default implementations of environment models and environment snapshots.

Terrain and maritime/environment snapshots here are query models used by the
engine and systems. They do not constitute land-domain terrain control,
movement, sensing, fires, or damage runtime.

## Allowed

- Model implementations such as wind, terrain, environment snapshot, etc.
- Pure computation helpers required for environment queries.

## Prohibited

- ECS system registration.
- Runtime owner or batch runtime.
- Python binding.
- Land-domain terrain ownership or ground movement/sensing/fires/damage behavior.

## Migration Notes

Environment state components belong to `components/basic` or a more specific directory; environment computation models belong to this directory.
