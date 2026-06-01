# `src/components/systems` Boundaries

`components/systems` holds platform system state components, including communications, data links, electronic warfare, navigation, logistics, sensors, sonar, and track management.

These state components are multi-domain aware for air/naval platform systems and
contact evidence. They do not define a full ground sensing, fires, logistics, or
C2 component model.

## Allowed

- comm, data link, sensor, sonar, EW, navigation, logistics, track management state.
- data that the corresponding `systems/systems` tick logic needs to read and write.

## Not Allowed

- Platform system update/tick/scan/track fusion behavior.
- mission/tasking DTOs.
- Python bindings, facades, or batch runtime logic.
- Native ground-domain platform-system schemas before ownership is defined.

## Migration Note

The directory name is broad, but currently represents "platform system components." If `systems/systems` is renamed later, this directory should also be evaluated for renaming to `components/platform`.
