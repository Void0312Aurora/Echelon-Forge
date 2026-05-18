<!-- Machine-translated draft generated on 2026-05-18 from src/components/systems/README.md. Review before treating this file as authoritative. -->

# `src/components/systems` Boundaries

`components/systems` holds platform system state components, including communications, data links, electronic warfare, navigation, logistics, sensors, and track management.

## Allowed

- data link, command link, sensor, EW, navigation, logistics, track management state.
- data that the corresponding `systems/systems` tick logic needs to read and write.

## Not Allowed

- Platform system update/tick/scan/track fusion behavior.
- mission/tasking DTOs.
- Python bindings, facades, or batch runtime logic.

## Migration Note

The directory name is broad, but currently represents "platform system components." If `systems/systems` is renamed later, this directory should also be evaluated for renaming to `components/platform`.
