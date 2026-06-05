# `src/components/command/ground` Boundary

This directory is the maintained C++ owner-slice home for early ground command
DTOs. It currently exposes static tasking intent through `MissionCommandGround`
only.

## Allowed

- `MissionCommandGround` as a static task/status command slice projected through
  the flat `MissionCommand` compatibility shell.
- Objective/area references, ground static task mode, tactical commander ID, and
  tactical cadence metadata.
- JSON round-trip and episode equality support for those static fields.

## Not Allowed

- Route-following, speed/acceleration, terrain passability, sensing, fires,
  damage, suppression, or combat outcome controls.
- Replacing the accepted tasking bridge with a ground-only command pipeline.
- Generalizing ground-specific execution controls into `common/` before the
  corresponding runtime owner is accepted.

## Current Slice

`MissionCommandGround` is a command-side carrier for G0/G1 static task metadata.
It is not a movement command and does not prove G2 route movement.
