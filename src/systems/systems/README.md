# `src/systems/systems` Boundary

This directory is a historical directory for platform system runtime, containing system logic such as command link, data link, EW, navigation, sensor, sonar, track manager, logistics, etc. The directory name is broad and should be renamed later, but no behavioral moves will be made before the freeze.

The current platform-system runtime supports air/naval contact and communication
flows, but it does not provide a full ground sensing, fires, or land C2 runtime.

## Allowed

- Flecs tick/update logic for platform systems.
- Read/write access to state components in `components/systems`.
- Per-frame state advancement related to sensor/data-link/track-management models.
- Sonar/acoustic and other naval-aware platform-system ticks when they remain within this historical platform-system boundary.

## Prohibited

- Adding new physics, combat, visual, or mission episode logic.
- Defining components or DTOs.
- Having batch runtime, facade, or Python binding.
- Native ground-domain platform runtime ownership before the split is defined.

## Migration Notes

Candidate renaming in the future:

- `src/systems/platform`
- `src/systems/avionics`
- `src/systems/mission_systems`

Before renaming, new files must express the specific business domain in the file name, avoiding continued use of generalized naming.
