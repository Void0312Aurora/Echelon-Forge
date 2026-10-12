# `src/models/systems` Boundary

`models/systems` stores platform-system related model implementations, e.g., the default sensor and acoustic model implementations.

The directory is multi-domain aware for sensing/contacts, including air/visual
sensor behavior and naval/acoustic helpers. Ship-specific maritime sensor state
is routed through `models/domains/naval/naval_sensor_maritime_adapter.h` rather than
owned directly in the generic sensor model. It does not own full ground sensing
or land C2 runtime behavior.

## Allowed

- Replaceable computational models for platform systems such as sensor, acoustic/sonar, track, data-link, etc.
- Pure C++ logic that only depends on `core/interfaces` and component data.

## Prohibited

- Flecs system tick.
- Component definitions.
- Python binding or facade.
- Full ground sensing, terrain-control, or fires runtime.

## Default acoustic provider capability

The content loader parses Passive and Active sonar declarations, including inline
and mounted modules. Parsing does not establish that a provider supports the mode.
The default acoustic provider supports Passive only: `IAcousticModel::scan` returns
`UnsupportedMode` for Active and `Completed` for a supported scan, including one
with zero detections. `SonarSystem` accepts new contacts only on `Completed`, stores
the outcome in `Sonar::last_scan_status`, and logs
`runtime.acoustic.unsupported_mode` when a module enters an unsupported outcome.
`last_scan_time_s` records the last attempt, so consumers must also consult status.
Both inline and mounted status are preserved in state transfer; an older snapshot
without status defaults to `NotScanned` rather than asserting successful completion.
A future acoustic provider can implement Active through the same typed interface;
this change supplies no active-ping propagation or echo model.

## Migration Notes

The directory name is similar to `systems/systems`; new files must express the model type with specific business names to avoid generalized expansion.
