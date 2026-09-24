# `src/systems/domains/ground` Boundary

`systems/domains/ground` contains the per-tick progression logic for ground
platforms. It consumes `components/domains/ground/combat` and the shared combat
damage surface, but does not own mission/tasking orchestration or facades.

This directory owns two bounded systems: the ground damage response and the
single-agent infantry movement primitive. It is not a complete ground runtime:
route following, general passability, sensing, fires, logistics, and observation
export remain outside this admission. The damage system matches spawned ground
entities and advances the ground-owned state, while `GroundInfantryMovement`
consumes the maintained `MissionCommand` ground slice and applies deterministic
surface/slope costs plus the environment's local sampled transition check.

## Allowed

- Per-tick progression of the ground-owned damage state and its projection into
  the shared platform capability fields.
- Deterministic horizontal movement for individual Ground fixtures with an active
  `MissionCommandGround::MoveStatic` directive, using shared terrain surface and
  slope queries.
- Damage-control sequencing for ground elements: fire load, ignition sources,
  structural loss, and casualties.
- Calls into the shared `systems/combat/damage_system_common.h` helpers, so
  ground loss semantics stay shared rather than forked.

## Forbidden

- Defining ground platform components or command/tasking DTOs.
- Mission rewards, termination, scenario compilation, or episode transitions.
- Python bindings, facades, training scripts, or multi-world owners.
- Ground route following, general passability planning, formations, sensing, or
  fires, none of which this slice implements or claims.
- A ground-only scheduler, packet family, or command/status pipeline.

## Current Files

- [damage_system_ground.h](damage_system_ground.h)
  - Registers `GroundDamageStateUpdate`, advancing `GroundPlatformDamageState`
    and projecting it through `sync_platform_damage_loss_state`.
- [movement_system.h](movement_system.h)
  - Registers `GroundInfantryMovement`, the bounded `MoveStatic` consumer and
    kinematic step for the individual infantry fixture.

## Dependency Direction

This directory may consume `components/domains/ground`, `components/combat`, and
the shared combat damage helpers. It should not depend on `runtime/facade`,
`interfaces/python`, training/scenario glue, or a sibling domain.
