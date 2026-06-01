# `src/components/command` Boundary

`components/command` is the home directory for pilot actions, mission commands, command links, and legacy control commands. The old `components/physics/action.h` is retained as a compatibility umbrella include.

Similar to tasking, the command side is now documented as a common foundation
with air and naval extensions, rather than an `air + ship` split. `common`
carries cross-domain command transport and shared execution intent, `air`
carries the mature aviation execution surface, and `naval` carries the
maintained first-stage ship/maritime command slice. Ground command/tasking
bootstrap evidence has not landed here as a maintained command subdomain.

## Allowed

- `PilotAction` and its action-space configuration.
- `MissionCommand`, the execution command DTO issued by upper-layer tasks or training environments.
- `MovementCommand`, `ActionCommand`, and other legacy command surfaces, but only as compatibility DTOs owned by explicit bridge seams.
- `CommandLink`, `CommandLag`, pending commands, and other command link states.

## Not Allowed

- `TaskOrder`, `LeaderIntent`, `PilotReport`, and other C2/tasking states; these go into `components/tasking`.
- Physics integration, control law execution, sensor scanning, or weapon guidance logic.
- JSON codec, episode transition, reward breakdown; these belong in `core/mission`.
- Python binding code.

## Split Direction

- `common command` holds cross-domain shared execution semantics: for example, command transport, latency/drop, pending delivery, and basic command vectors reusable across multiple domains.
- `air command` holds the currently aviation-specific execution surface: `PilotAction`, existing legacy flight control surfaces, and command extensions with route/recovery/takeoff/runway/formation semantics.
- `naval command` models the current ship/maritime execution DTO slice separately, including stationing, embarked helo launch/recovery, OTH relay, and naval surface-engagement command codes. Do not directly generalize air’s heading/altitude/runway/recovery combinations into a “ship command”.
- `ground command` is not a maintained C++ command slice yet. Keep land movement/sensing/fires control out of `common/` until the ground schema/runtime owner is defined.

## Notes on `MissionCommand`

`MissionCommand` has completed the first stage of compatible splitting into `common + air`, but it remains a high-risk consumer convergence point on the command side:

- In terms of code structure, `mission_command.h` is now only a compatibility umbrella, externally exposing the flat `MissionCommand`, while the underlying layers have been split into `common/mission_command_core.h` and `air/mission_command_air.h`.
- Semantically, it remains deeply coupled with the air execution surface and directly connects to command delivery, mission episode state, mission runtime JSON codec, instrumentation/observation, and the air control model.
- Therefore, subsequent work should prioritize maintaining the existing flat compatibility layer and consumer symmetry, rather than aggressively pushing toward nested objectification or broader domain-specific execution splits at this layer.

At the code level, `CommandLink` is closer to a truly shared core than `MissionCommand`; `MissionCommand` currently still looks more like a “shared shell + a lot of air payload”.

## Dependency Direction

Command DTOs can be consumed by `systems/`, `core/engine`, `core/mission`, `runtime/facade`, and `interfaces/python`. They do not depend on these layers in reverse.

Maintained air-control consumers must resolve legacy command fallback through
`air/control_input_resolution.h`. Ad-hoc `MovementCommand`/`ActionCommand`
probing inside maintained systems is not an allowed pattern.

Current explicit compatibility seams that may still depend on `legacy_command.h`:

- `src/components/command/legacy_command_bridge.h`
- `src/systems/core/operation_system.h`
- `src/systems/systems/command_link_system.h`
- compatibility-only or still-unmigrated consumers guarded by architecture tests

## Migration Notes

Already implemented:

- `pilot_action.h`
- `mission_command.h`
- `command_link.h`
- `legacy_command.h`
- `naval/mission_command_naval.h`

WP0 document scope:

- Prioritize identifying truly shared command transport / base intent.
- Air-specific semantics have been separated from the shared layer into `MissionCommandAir`, but a flat compatibility shell is still maintained.
- Naval-specific command semantics have landed in `MissionCommandNaval`, without using the “air + ship” dichotomy.
- Ground command semantics remain held; use only shared typed setup/capability evidence until a maintained ground command schema is introduced.

New code should include specific header files and should no longer depend on `components/physics/action.h`.
