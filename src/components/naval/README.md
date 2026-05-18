<!-- Machine-translated draft generated on 2026-05-18 from src/components/naval/README.md. Review before treating this file as authoritative. -->

# `src/components/naval` Boundary

`components/naval` holds static/slowly-changing platform state components for surface vessels, submarines, and ship-based aviation operations. It stores naval platform data and deck operation status, and is not responsible for command interpretation, tick advancement, or mission/runtime orchestration.

## Allowed

- Pure data fields such as surface vessel and submarine platform performance, dimensions, maneuver envelope.
- Lightweight state components required for ship-based helicopter/deck operations.
- Naval platform DTOs readable by `systems/naval`, `models/`, and `core/mission`.

## Forbidden

- Ship/submarine motion integration, sea-state advancement, or aircraft scheduling logic; these belong in `systems/naval`.
- Naval mission command, command link, or tasking/C2 DTOs.
- Python bindings, facade request/result, or environment glue.
- Directly owning entity lifecycle or helo spawn/recovery runtime owner.

## Current Files

- [ship_platform.h](ship_platform.h)
  - Surface vessel platform parameters, e.g., displacement, dimensions, speed, turning, seakeeping, and crew complement.
- [submarine_platform.h](submarine_platform.h)
  - Submarine platform parameters, e.g., underwater speed, depth envelope, stealth bias, and depth maneuverability.
- [embarked_air_ops.h](embarked_air_ops.h)
  - Ship-based aviation operation status, e.g., active helo, launch/recovery offset, OTH relay related flags.

## Dependency Direction

This directory is a data layer. `systems/naval`, `core/mission`, `runtime/facade`, and `interfaces/python` may consume these components; this directory must not have reverse dependencies on those upper layers.
