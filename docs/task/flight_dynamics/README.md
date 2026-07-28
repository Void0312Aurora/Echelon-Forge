# Flight Dynamics Tasks

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory is the archived/reference navigation entrypoint for the
`flight_dynamics` realism-analysis closure stream. It records the historical
flight, sensor, weapon, naval, and C2 analysis split that fed the current
multi-domain task tree. For active work, start from [../README.md](../README.md)
and the current domain entries for air combat, naval, ground, and simulation
architecture.

To determine the state of this historical stream, use the `2026-05-18` closure
markers in the analysis docs, not `archive/program/` or `archive/`.

## Historical Subproject Navigation

- [flight](./flight/README.md): flight dynamics, propulsion, stall, and high-AoA analysis.
- [sensor_situation](./sensor_situation/README.md): sensor, track, and data-link situational-awareness analysis.
- [weapon_guidance](./weapon_guidance/README.md): weapon chain, seeker, guidance, fuze, and damage analysis.
- [naval](./naval/README.md): historical naval realism analysis that now points forward to the active naval task line.
- [c2_command_chain](./c2_command_chain/README.md): `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` frozen analysis baseline.
- [program](./archive/program/README.md): deprecated mainline-status snapshot entry, kept only for history.

## Cross-Directory Linked Entry Points

- [task root](../README.md):
  current multi-domain task-area navigation and lifecycle labels.
- [air_combat task track](../air_combat/README.md):
  current combat and air-domain workline entry.
- [naval task track](../naval/README.md):
  active naval domain task line.
- [ground task track](../ground/README.md):
  early ground tasking/native-schema bootstrap line.
- [simulation_architecture task track](../simulation_architecture/README.md):
  shared runtime, contract, facade, and architecture closure line.
- [retained performance-runtime planning history](../archive/performance_runtime/README.md):
  archived planning context only; it is not a current execution entry.

## Recommended Starting Points

- [flight analysis](./flight/flight_dynamics_realism_analysis_20260516.zh.md):
  current flight-dynamics framing via the closure marker.
- [sensor analysis](./sensor_situation/sensor_situation_realism_analysis_20260516.zh.md):
  current sensor/data-link framing via the closure marker.
- [weapon analysis](./weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md):
  current weapon-chain framing via the closure marker.
- [naval analysis](./naval/naval_realism_analysis_20260516.zh.md):
  current naval framing via the closure marker.
- [C2 analysis](./c2_command_chain/c2_command_chain_realism_analysis_20260517.zh.md):
  current C2 framing via the closure marker.

## Document Organization Rules

1. Each direction gets its own subproject folder, and that folder's `README.md`
   is the local navigation entrypoint.
2. `*_analysis_*` docs are authoritative for current state when their closure
   marker says so.
3. `archive/program/` is deprecated and `archive/` is history only.
4. Do not open new active multi-domain implementation streams under this
   directory. Route them through the task root and the current domain-specific
   entries instead.
