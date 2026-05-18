<!-- Machine-translated draft generated on 2026-05-18 from src/systems/systems/README.md. Review before treating this file as authoritative. -->

# `src/systems/systems` Boundary

This directory is a historical directory for platform system runtime, containing system logic such as command link, data link, EW, navigation, sensor, track manager, logistics, etc. The directory name is broad and should be renamed later, but no behavioral moves will be made before the freeze.

## Allowed

- Flecs tick/update logic for platform systems.
- Read/write access to state components in `components/systems`.
- Per-frame state advancement related to sensor/data-link/track-management models.

## Prohibited

- Adding new physics, combat, visual, or mission episode logic.
- Defining components or DTOs.
- Having batch runtime, facade, or Python binding.

## Migration Notes

Candidate renaming in the future:

- `src/systems/platform`
- `src/systems/avionics`
- `src/systems/mission_systems`

Before renaming, new files must express the specific business domain in the file name, avoiding continued use of generalized naming.
