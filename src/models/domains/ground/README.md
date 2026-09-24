# `src/models/domains/ground` Boundary

`models/domains/ground` holds ground-owned model routing and consequence
application used by shared default models.

## Allowed

- Explicit ground target selection and consequence application that keeps ground
  concepts out of generic model files.
- Small owner-shell helpers that preserve legacy routing names.

## What the damage route is, precisely

`default_effects_ground_domain.h` selects a ground target only when it carries
the ground-owned `GroundPlatformDamageState` **plus** the shared
`HitboxConfig`/`SystemHealth`/`PlatformDamageState` surface, applies warhead
mechanism load into the ground state, projects that state into the shared
platform capability fields, and then calls the shared finalize. It is a
consequence ledger plus a bootstrap reachability path — nothing more.

The component id for that state is **supplied to the route, not derived here**. The
composition path resolves `GroundPlatformDamageState` once per world and passes the id
into the effects model, which forwards it to the selection predicate and to
`ecs_get_mut_id`. This file therefore names no component type in order to find one:
identity stays with the owner-derived registry and the engine's composition, and the
models layer does not open a second membership channel.

A ground target that does not satisfy the selection predicate falls back to
`is_default_effects_ground_placeholder_target` /
`resolve_default_effects_ground_placeholder_consequences`, which stay as the
unsatisfied-selection fallback only.

## Forbidden

- ECS system registration.
- Defining ground components (those live in `components/domains/ground`).
- Claiming route movement, ground sensing, ground fires, terrain-model fidelity,
  or a full ground damage model. The bounded infantry movement primitive is a
  system-layer consumer of `IEnvironmentModel`, not a model owned here.

## Current Files

- [default_effects_ground_domain.h](default_effects_ground_domain.h)
  - Ground-owned target selection and consequence application. The whole-body
    hitbox it resolves against is a provisional neutral extent synthesized at
    spawn, not authored ground geometry, so this file makes no ground damage
    fidelity claim.
