<!-- Machine-translated draft generated on 2026-05-18 from src/components/command/README.md. Review before treating this file as authoritative. -->

# `src/components/command` Boundary

`components/command` is the home directory for pilot actions, mission commands, command links, and legacy control commands. The old `components/physics/action.h` is retained as a compatibility umbrella include.

Similar to tasking, the subsequent split direction on the command side should be clearly defined as `common + air + naval`, rather than `air + ship`. `common` carries cross-domain command transport and shared execution intent, `air` carries the current aviation execution surface, and `naval` will later carry the ship/maritime execution surface.

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
- `naval command` will later model the ship/maritime execution surface separately; do not directly generalize air’s heading/altitude/runway/recovery combinations into a “ship command”.

## Notes on `MissionCommand`

`MissionCommand` has completed the first stage of compatible splitting into `common + air`, but it remains a high-risk consumer convergence point on the command side:

- In terms of code structure, `mission_command.h` is now only a compatibility umbrella, externally exposing the flat `MissionCommand`, while the underlying layers have been split into `common/mission_command_core.h` and `air/mission_command_air.h`.
- Semantically, it remains deeply coupled with the air execution surface and directly connects to command delivery, mission episode state, mission runtime JSON codec, instrumentation/observation, and the air control model.
- Therefore, subsequent work should prioritize maintaining the existing flat compatibility layer and consumer symmetry, rather than aggressively pushing toward nested objectification or naval execution split at this layer.

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
- Naval is modeled separately, without using the “air + ship” dichotomy.

New code should include specific header files and should no longer depend on `components/physics/action.h`.
