# `src/models/domains/naval` Boundary

`models/domains/naval` holds naval-owned model adapters and placeholder routes consumed
by shared default models.

## Allowed

- Naval-specific model adapters that read naval components for shared models.
- Explicit placeholder effects routing that preserves legacy behavior until a
  maintained naval damage-fidelity owner exists.

## Forbidden

- ECS system registration.
- Naval component definitions or mission/tasking DTOs.
- Claiming complete naval damage fidelity from placeholder effects routes.

## Current Files

- [naval_sensor_maritime_adapter.h](naval_sensor_maritime_adapter.h)
  - Ship-specific maritime state and radar helper access for the generic sensor model.
- [default_effects_naval_domain.h](default_effects_naval_domain.h)
  - Placeholder naval effects routing that preserves finalize-only behavior.
