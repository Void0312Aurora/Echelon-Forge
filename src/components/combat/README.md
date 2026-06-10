# `src/components/combat` Boundaries

`components/combat` holds combat-related ECS state, such as damage, health, weapon mounts, and scoring state.

The root combat surface now carries only shared combat state and common
weapon/damage primitives. Air, naval, and ground combat owner slices live under
`components/domains/<domain>/combat/`.

## Allowed

- Combat state components: health, damage, weapon, scoring.
- Domain-owned combat slices that remain plain ECS data, via
  `components/domains/<domain>/combat/`.
- Pure data read and written by weapon systems and damage systems.

## Disallowed

- Guidance, damage resolution, or firing sequence implementation.
- Physics motion state, sensor scanning state, or mission state.
- Python bindings and runtime owner.
- New domain-specific fires/damage schema ownership at the `components/combat`
  root.

## Migration Notes

Combat behavior goes into `systems/combat` or `models/weapons`; this directory retains serializable, bindable state data.
