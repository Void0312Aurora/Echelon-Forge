# `src/systems/domains/ground` Boundary

`systems/domains/ground` contains the per-tick progression logic for ground
platforms. It consumes `components/domains/ground/combat` and the shared combat
damage surface, but does not own mission/tasking orchestration or facades.

This directory owns one system, the ground damage response. It is not a complete
ground runtime: movement, terrain interaction, sensing, fires, logistics, and
observation export have no owner here. The system matches spawned ground entities and
advances the ground-owned state, and the effects route that feeds damage into that
state is reachable — the component id is resolved once per world in the composition
path — so a structural hit does apply a ground consequence to the elements this
system runs on.

## Allowed

- Per-tick progression of the ground-owned damage state and its projection into
  the shared platform capability fields.
- Damage-control sequencing for ground elements: fire load, ignition sources,
  structural loss, and casualties.
- Calls into the shared `systems/combat/damage_system_common.h` helpers, so
  ground loss semantics stay shared rather than forked.

## Forbidden

- Defining ground platform components or command/tasking DTOs.
- Mission rewards, termination, scenario compilation, or episode transitions.
- Python bindings, facades, training scripts, or multi-world owners.
- Ground movement, route following, terrain traversal, sensing, or fires, none
  of which this slice implements or claims.
- A ground-only scheduler, packet family, or command/status pipeline.

## Current Files

- [damage_system_ground.h](damage_system_ground.h)
  - Registers `GroundDamageStateUpdate`, advancing `GroundPlatformDamageState`
    and projecting it through `sync_platform_damage_loss_state`.

## Dependency Direction

This directory may consume `components/domains/ground`, `components/combat`, and
the shared combat damage helpers. It should not depend on `runtime/facade`,
`interfaces/python`, training/scenario glue, or a sibling domain.
