# `src/systems/core` Boundaries

`systems/core` holds general ECS operation systems. It should only contain cross-domain, per-tick basic world mutations.

## Allowed

- Systems related to operation/lifecycle.
- Basic logic such as general state cleanup and active state progression.

## Disallowed

- Physics, combat, platform systems, or visual-specific logic.
- Component definitions.
- Runtime owner or Python binding.

## Migration Notes

If logic only serves a specific business domain, it should be placed in the corresponding `systems/<domain>` directory, and should not expand `systems/core`.
