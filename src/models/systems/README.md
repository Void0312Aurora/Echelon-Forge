<!-- Machine-translated draft generated on 2026-05-18 from src/models/systems/README.md. Review before treating this file as authoritative. -->

# `src/models/systems` Boundary

`models/systems` stores platform system related model implementations, e.g., the default sensor model implementation.

## Allowed

- Replaceable computational models for platform systems such as sensor, track, data-link, etc.
- Pure C++ logic that only depends on `core/interfaces` and component data.

## Prohibited

- Flecs system tick.
- Component definitions.
- Python binding or facade.

## Migration Notes

The directory name is similar to `systems/systems`; new files must express the model type with specific business names to avoid generalized expansion.
