# `src/components/combat` Boundaries

`components/combat` holds combat-related ECS state, such as damage, health, weapon mounts, and scoring state.

The component surface includes generic weapon/damage state and naval weapon
system data, but it is data only. It is not evidence that a ground fires/damage
component model or full naval engagement owner has landed.

## Allowed

- Combat state components: health, damage, weapon, scoring.
- Naval weapon-system state that remains plain ECS data.
- Pure data read and written by weapon systems and damage systems.

## Disallowed

- Guidance, damage resolution, or firing sequence implementation.
- Physics motion state, sensor scanning state, or mission state.
- Python bindings and runtime owner.
- Ground fires/damage schema ownership.

## Migration Notes

Combat behavior goes into `systems/combat` or `models/weapons`; this directory retains serializable, bindable state data.
