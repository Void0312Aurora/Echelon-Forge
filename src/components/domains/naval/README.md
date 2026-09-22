# `src/components/domains/naval` Boundary

This directory is the component-layer owner for naval-domain data and DTO
extensions. It groups naval platform state, combat components, command
extensions, and tasking extensions under one domain boundary.

## Entry Points

- [platform/README.md](platform/README.md)
- [combat/damage_naval.h](combat/damage_naval.h)
  - Declares `NavalDamageResponseProfile`: the naval-owned, data-declared coefficients for fire/flooding/hull-breach
    evolution, the severity-to-capability loss terms, and the mount-state coupling gain. Ships currently resolve
    the single admitted parity-default profile; `naval_damage_response_profiles()` is intentionally default-only
    until content selection and runtime evidence exist for another profile.
- [combat/weapon_naval.h](combat/weapon_naval.h)
- [command/README.md](command/README.md)
- [tasking/README.md](tasking/README.md)

## Damage Response

`systems/combat/damage_system_naval.h` owns the ship-only naval damage tick and no coefficients: it resolves the
admitted `NavalDamageResponseProfile`, applies its per-second rates using the Flecs step duration, evolves
fire/flooding/breach from it, and projects the result onto the shared
`PlatformDamageState` capability fields, and hands loss semantics to `sync_platform_damage_loss_state`. Weapon mount
state is measured correctly as a clamped mean `ready_count / max_ready_count`, but the admitted profile declares
`mount_response_weight = 0.0`, so the coupling is exactly neutral. Submarine damage response is intentionally not
claimed by this system yet. This is a damage-response mechanism only: it carries no naval weapon-release authority
(N5) and no kill/outcome authority (N6).
