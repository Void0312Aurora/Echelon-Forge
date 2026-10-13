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

## Passive acoustic source proxy

`default_acoustic_model.cpp` currently uses `passive_target_source_proxy.v1` for
targets without an admitted acoustic signature: 118 dB reference level plus
1.6 dB per m/s, with platform offsets of submarine stealth bias + 10 dB, ship
+ 16 dB, and aircraft + 18 dB (the current scan admits ship/submarine targets
only, so that aircraft helper branch is inactive). This is an engineering proxy for deterministic
runtime behavior. It is not a calibrated frequency-dependent signature, a
measured deployment range, or a replacement for source data. The receiver's
legacy `Sonar::source_level_*` fields no longer select the target emission.

The maintained C++ ownership baselines are
`src/tests/test_acoustic_model.cpp` cases `passive target source level is
invariant to receiver source settings` and `passive target source level follows
target speed`; historical detection, SNR, probability, or range reports that
used receiver-owned source settings must be recomputed against this proxy
version before comparison. In particular, the contact and maritime-noise cases in
`tests/runtime/naval/test_naval_asw_helo_runtime.py` consume the
`DDG-51_Flight_I_ASW_Helo_MVP` receiver's historical 118 dB / 1.7 dB-per-m/s
settings; target-speed SNR now uses the proxy's 1.6 coefficient. Historical CSG
traces using passive Virginia modules (0 / 0 source fields) or interpreting
235 dB Active DDG fields as passive target emission also need recomputation.
No calibrated operational claim is made until an
admitted signature provider and its calibration evidence replace the proxy.

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
