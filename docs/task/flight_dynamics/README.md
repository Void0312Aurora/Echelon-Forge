# Flight Dynamics Tasks

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory is the navigation entrypoint for the `flight_dynamics` realism
workstream. Dated documents under each subdirectory are snapshots of one
analysis pass, implementation package, taskboard, or checkpoint. For current
context, start from the local `README.md` or the newest status/taskboard/checkpoint
doc in that slice rather than treating one dated analysis as the whole state.

## Subproject Navigation

- [program](./program/README.md): mainline status, global taskboard, and staged scheduling entrypoint.
- [flight](./flight/README.md): flight dynamics, propulsion, stall, and high-AoA analysis packages.
- [sensor_situation](./sensor_situation/README.md): sensor, track, and data-link situational-awareness docs.
- [weapon_guidance](./weapon_guidance/README.md): weapon chain, seeker, guidance, fuze, and damage-realism docs.
- [naval](./naval/README.md): naval-realism freeze analysis and mainline linkage notes.
- [c2_command_chain](./c2_command_chain/README.md): `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` workstream.

## Recommended Starting Points

- [current realism program status](./program/realism_program_current_status_20260517.zh.md):
  current overview of the program track and linked subprojects.
- [realism P1 taskboard](./program/realism_program_p1_taskboard_20260517.zh.md):
  current staged `P1` breakdown.
- [C2 command-chain and communications checkpoint](./c2_command_chain/c2_command_chain_progress_checkpoint_20260517.zh.md):
  latest checkpoint for C2 and data-link work.
- [naval progress checkpoint](../naval/naval_progress_checkpoint_20260517.zh.md):
  cross-directory naval checkpoint that still feeds this mainline.

## Document Organization Rules

1. Each direction gets its own subproject folder, and that folder's `README.md`
   is the local navigation entrypoint.
2. `*_analysis_*` docs keep their frozen analysis framing and should not be
   treated by themselves as the latest implementation state.
3. `*_implementation_package_*`, `*_taskboard_*`, `current_status`,
   `progress checkpoint`, and `unresolved issues` docs carry implementation
   scope, scheduling, or current tracking state.
4. When a new direction is split out further, create the subfolder and local
   README first, then add analysis or implementation docs under it.
