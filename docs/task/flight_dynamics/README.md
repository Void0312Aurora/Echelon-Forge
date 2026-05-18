# Flight Dynamics Tasks

Language:
- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

This directory is the navigation entrypoint for the `flight_dynamics` realism
workstream. To determine current state, use the `2026-05-18` closure markers in
the analysis docs, not `program/` or `archive/`.

## Subproject Navigation

- [flight](./flight/README.md): flight dynamics, propulsion, stall, and high-AoA analysis.
- [sensor_situation](./sensor_situation/README.md): sensor, track, and data-link situational-awareness analysis.
- [weapon_guidance](./weapon_guidance/README.md): weapon chain, seeker, guidance, fuze, and damage analysis.
- [naval](./naval/README.md): naval realism analysis.
- [c2_command_chain](./c2_command_chain/README.md): `MissionCommand / CommandLink / DataLink / ROE / naval command-chain` frozen analysis baseline.
- [program](./program/README.md): deprecated mainline-status snapshot entry, kept only for history.

## Cross-Directory Linked Entry Points

- [air_combat task track](../air_combat/README.md):
  current `1v1` workline entry.
- [performance_runtime task track](../performance_runtime/README.md):
  current runtime-performance planning entry.

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
3. `program/` is deprecated and `archive/` is history only.
4. When a new direction is split out further, create the subfolder and local
   README first, then add analysis or implementation docs under it.
