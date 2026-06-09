# `src/models/ground` Boundary

`models/ground` holds ground-owned placeholder model routes used by shared
default models.

## Allowed

- Explicit ground placeholder routing that preserves legacy behavior.
- Small owner-shell helpers that prevent ground concepts from being hidden in
  generic model files.

## Forbidden

- ECS system registration.
- Ground component definitions.
- Claiming full ground movement, sensing, fires, or damage runtime maturity.

## Current Files

- [default_effects_ground_domain.h](default_effects_ground_domain.h)
  - Placeholder ground effects routing that preserves finalize-only behavior.
