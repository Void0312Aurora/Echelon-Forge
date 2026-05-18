<!-- Machine-translated draft generated on 2026-05-18 from src/components/combat/README.md. Review before treating this file as authoritative. -->

# `src/components/combat` Boundaries

`components/combat` holds combat-related ECS state, such as damage, health, weapon mounts, and scoring state.

## Allowed

- Combat state components: health, damage, weapon, scoring.
- Pure data read and written by weapon systems and damage systems.

## Disallowed

- Guidance, damage resolution, or firing sequence implementation.
- Physics motion state, sensor scanning state, or mission state.
- Python bindings and runtime owner.

## Migration Notes

Combat behavior goes into `systems/combat` or `models/weapons`; this directory retains serializable, bindable state data.
