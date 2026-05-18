<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p1_implementation_package_20260517.zh.md. Review before treating this file as authoritative. -->

# Sensor/Situation Realism P1 Implementation Package

Status: `2026-05-17` Converged version after acceptance.

Related Documents:

- [Analysis of Sensor and Situation Awareness Realism](sensor_situation_realism_analysis_20260516.zh.md)
- [Verification and Implementation Plan for Sensor/Situation Awareness Realism](sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [Sensor/Situation Realism P0 Implementation Package](sensor_situation_realism_p0_implementation_package_20260516.zh.md)
- [Realism Task Master List](../program/realism_program_taskboard_20260516.zh.md)
- [Sensor/Situation Realism P0 Reference Notes](sensor_situation_realism_p0_reference_notes_20260516.md)

Document Purpose:

- Advance Direction 2 from `P0 skeleton is in place` to `P1: integrable, exposable, and continuable for calibration`.
- Clearly identify which issues must be handled as `pre-integration wrap-up` first, and which can be conservatively included in `P1` for deepening realism.
- Document the compatibility risks already exposed during this acceptance into the task package, to avoid later work based only on an idealized system.

---

## I. P1 Positioning

`P1` no longer addresses "whether the skeleton exists", but rather two types of problems:

1. The fields and semantics already landed in `P0` must be fully connected through `loader / factory / observation / python binding / test contracts`
2. Without introducing large-scale architectural rewrites, advance sensor/situation from "trainable at the run level" to "more credible in engineering terms"

In other words, the goal of `P1` is not to build a complete radar/IFF/fusion system, but to make the following statements true:

- New sensor fields are no longer just implicit default values inside C++ structs; they become configurable, observable, and testable.
- The `TrackDatabase`'s `status / quality / source` semantics are visible to upper layers, not just existing internally in the backend.
- Environment, IFF, fusion, and track quality realism items begin to produce verifiable effects, while still remaining within a conservative scope.

---

## II. Realistic Input After P0 Acceptance

P1 does not start from a blank slate, but from the current state after this P0 acceptance.

### 2.1 P0 Achievements Already in Place

1. Local detection already has an approximate `SNR -> Pd` link.
2. Local track already has a minimal `2-of-3` confirmation semantics.
3. `TrackManager` already has a minimal `alpha-beta` prediction update skeleton.
4. `DataLink` has severed the truth-style behavior of "directly writing into the receiver's ContactList" and switched to track/report semantics.

### 2.2 Compatibility Risks Exposed During This Acceptance

If these issues are not addressed, the realism skeleton of `P0` will remain "partially valid only in the backend".

| Risk | Current Phenomenon | Direct Requirement for P1 |
|------|--------------------|---------------------------|
| New fields in `Sensor` not fully connected | Structs expanded, but `loader / factory` still need unified default values and config reading | Perform pre-integration wrap-up first |
| Observation not exposing new semantics | `track status / quality / new Detection fields` still not stably exposed to upper layers | Perform pre-integration wrap-up first |
| Python binding surface still uses old interfaces | New fields of `ReportTrack`, `CommPacket`, and `Detection` not fully exposed in Python | Perform pre-integration wrap-up first |
| Old tests may still be bound to old semantics | Old tests may still treat "shared track = local contact" as valid behavior | Perform pre-integration wrap-up first |
| Test/build product paths may cause confusion | If tests load a different build product than the current one, there can be a false impression that "source is changed but runtime remains the same" | P1 needs to tighten test entry points |
| Current `entity_id` is still a strong coupling hook | P0 still uses `entity_ref`/`entity_id` for auxiliary association and debugging | P1 must continue conservative evolution; cannot abruptly sever this |
| `Tentative` is still internal semantics | P0, to maintain compatibility with observation interfaces, has not yet exposed tentative tracks as a primary observation contract | P1 needs to clarify whether and how to expose this |
| Noise failures in unrelated tests | e.g., some `naval_screen` related tests may fail not directly caused by this line | P1 needs to layer regression judgment with owned/unowned risk |

### 2.3 Basic Strategy for P1

P1 adopts two principles:

1. `Wrap up first, then deepen`
   - First complete `loader / factory / observation / binding / test contracts`
   - Then proceed with deeper realism
2. `Deepen realism conservatively, no architectural revolution`
   - Allow continuing to retain `entity_ref` as a debug/truth hook
   - Do not directly introduce `JPDA / MHT / full Link 16 / full NCTR` in P1

---

## III. P1 Pre-Integration Wrap-Up

This layer is not about "making algorithms more realistic", but about "making P0 a true system-level capability".

### 3.1 Objectives

1. Get new fields of `Sensor` from configuration into runtime.
2. Make `Track status / quality / Detection extended fields` visible to observation and Python.
3. Migrate old test contracts to new semantics, instead of silently relying on old behavior.
4. Stabilize test and build entry points to reduce the risk of "running against old build products".

### 3.2 Items Conservatively Included in P1

#### 1. Loader / Factory Default Value Completion

Suggested file scope:

- [src/content/unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [src/models/core/default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
- If needed, supplement [src/content/unit_definition.h](../../../../src/content/unit_definition.h)

Suggested completions:

- `reference_snr_db`
- `reference_range_m`
- `reference_rcs_m2`
- `pfa`
- `confirm_hits_m`
- `confirm_window_n`
- `velocity_noise_std`
- `alpha_beta_alpha`
- `alpha_beta_beta`

Suggested default conventions:

- Radar default `range_power = 4.0`
- `pfa = 1e-6`
- Fighter radar default `confirm = 2-of-3`
- Surveillance radar default `confirm = 2-of-2` or `3-of-4`

P1 does not recommend stuffing `Pt / G / B / F / PRF` into the schema at this layer.

#### 2. Observation / Runtime Contract Completion

Suggested file scope:

- [src/core/engine/simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
- [src/core/engine/simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h)

Observation interfaces that P1 needs to clarify:

- Whether to continue only exposing `confirmed/coasted` tracks by default
- Whether to expose `status` directly to upper-layer agents
- Whether to additionally expose:
  - `track_quality`
  - `track_confidence`
  - `last_local_update_time`
  - `last_datalink_update_time`
  - Whether `closing_speed` should be derived from `vx/vy/vz`

Conservative recommendation:

- Default observation still only exposes `confirmed/coasted`
- Add new fields for `status / quality / confidence`
- If tentative tracks need exposure, go through `debug observation` or an explicit optional exit; do not directly change the main contract

#### 3. Python Binding Exposure and Compatibility Aliases

Suggested file scope:

- [src/interfaces/python/bindings_core.cpp](../../../../src/interfaces/python/bindings_core.cpp)
- [src/interfaces/python/bindings_command.cpp](../../../../src/interfaces/python/bindings_command.cpp)

P1 needs to add:

- `Detection.snr_db`
- `Detection.detection_prob_used`
- `Detection.measured_vr`
- `Detection.sensor_type`
- `Detection.local_sensor_hit`
- `CommPacket.track_ref`
- `CommPacket.velocity_x/y/z`
- `CommPacket.quality`
- `CommMsgType.ReportTrack`

Compatibility suggestion:

- `ReportTrack` and `ReportContact` can both be retained on the Python side
- Old field names are not removed; only new ones are added

#### 4. Migration of Old Test Semantics

Suggested file scope:

- `tests/runtime/test_kernel_observation_sanity.py`
- `tests/runtime/test_execution_step_runtime.py`
- `tests/runtime/test_mission_runtime.py`
- `tests/runtime/test_naval_screen_scenario.py`
- `tests/runtime/test_air_combat_1v1_fire_missile.py`
- `tests/runtime/test_bindings_command_surface.py`
- `tests/runtime/test_sensor_situation_realism_p0.py`

Old semantics that P1 needs to clean up:

- "After sharing a track, the receiver's local `ContactList` automatically has the target appear"
- "`ReportContact` is the only valid message type name"
- "Track does not affect the contract if it lacks `status / quality` fields"

#### 5. Build/Test Entry Point Tightening

Suggested file scope:

- `python/testing/runtime.py`
- `tests/README.md`
- If necessary, add a minimal test documentation note, but do not modify the task master list

P1 requires at minimum:

- When running tests, prioritise loading the current build product
- Clearly define the standard order: `build ef_py -> run runtime tests`
- Avoid ambiguity such as "source code has changed, but tests still load the old installed module"

### 3.3 Items Deferred to P2

The following should not be included in the "pre-integration wrap-up":

1. Rewriting the main observation contract
2. Completely removing `entity_ref`
3. Full refactoring of the Python API naming surface
4. Fixing all unrelated runtime regressions

### 3.4 Minimal Test Checklist

#### 1. Configuration / Default Values

- New `sensor` fields can be read from the database
- When fields are missing, factory/default values are stable
- Radar default `range_power` no longer erroneously falls to `2.0`

#### 2. Observation / Binding

- Python can read the new `Detection` fields
- Python can read `Track status / quality`
- `ReportTrack` and `ReportContact` are both available on the compatibility surface

#### 3. Semantic Migration

- After DataLink sharing, the receiver's `ContactList` is still empty
- The receiver's `TrackDatabase` can see `TrackSource::DataLink`
- Old tests that depended on old semantics have been changed to check new semantics or explicitly deprecated

### 3.5 Acceptance Criteria

After completing the pre-integration wrap-up, at least the following must hold:

1. P0 new fields no longer rely on "implicit struct defaults + manual injection" to function.
2. Runtime observation and Python binding can see the key new semantics of P0.
3. Old tests no longer treat "shared contact" as a valid behavior.
4. The path from build to test is reproducible, explainable, and handover-ready.

---

## IV. P1 Deepening Realism

This layer, after the pre-integration wrap-up, begins to further improve realism while maintaining a conservative scope.

### 4.1 Items to Conservatively Include in P1

#### 1. Track Quality / Confirm Semantics Refinement

Suggested file scope:

- [src/components/systems/track_management.h](../../../../src/components/systems/track_management.h)
- [src/systems/systems/track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [src/core/engine/simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)

P1 recommends doing:

- Tighten the current simplified hit accumulation into a clearer sliding `M-of-N`
- Clarify the lifecycle: `Tentative -> Confirmed -> Coasted -> Dropped`
- Differentiate:
  - Local latest update time
  - Data link latest update time
  - Overall track age
- Make `quality` influenced by `hits / misses / staleness / source`

This belongs in P1 because it directly affects higher-level tactical decisions, but does not require a full Kalman covariance system.

#### 2. Conservative Environment/Clutter Modeling

Suggested file scope:

- [src/core/interfaces/environment_model.h](../../../../src/core/interfaces/environment_model.h)
- [src/models/environment/default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp)
- [src/models/systems/default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

P1 recommends doing:

- Elevate `weather attenuation` from a fixed `0.0` to a minimal nonzero model
- Add a basic clutter penalty for look-down / low radial velocity scenarios
- Retain the current data link horizon formula
- Add a minimal "curvature/low-altitude geometric penalty" or horizon-style penalty on the sensor detection side

P1 does not recommend doing:

- Full terrain ray casting
- Sea-state-driven sea clutter maps
- Ducting/super-refraction/sub-refraction

#### 3. Minimal IFF State Machine Implementation

Suggested file scope:

- [src/components/systems/track_management.h](../../../../src/components/systems/track_management.h)
- [src/components/systems/sensor.h](../../../../src/components/systems/sensor.h)
- [src/systems/systems/track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- Corresponding observation/binding exits

P1 only recommends doing:

- `IFF reply present / no reply / ambiguous / pending`
- Minimal time semantics for periodic interrogation
- Friendly aircraft reply should first promote `identity` from `Unknown` to `Friendly`

P1 does not recommend doing:

- Full Mode 4/5 key management and time synchronization
- Deceptive IFF
- Full NCTR identification chain

Regarding `NCTR`:

- `NCTR` can reserve only fields or source slots in P1
- Specific micro-Doppler/JEM identification logic remains deferred to `P2`

#### 4. Conservative Multi-Source Fusion Implementation

Suggested file scope:

- [src/components/systems/track_management.h](../../../../src/components/systems/track_management.h)
- [src/systems/systems/track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
- [src/systems/systems/data_link_system.h](../../../../src/systems/systems/data_link_system.h)

P1 recommends doing:

- Add `source_mask`
- Allow `TrackSource::Fused` to actually appear
- Implement minimal fusion rules for `Radar + DataLink`:
  - Local updates preferentially refresh geometry
  - Data link updates preferentially supplement stale tracks
  - Quality takes a weighted or upper-bound approach, rather than simple overwriting

P1 does not recommend doing:

- `JPDA / MHT`
- True track-to-track covariance fusion
- Full multi-sensor database

#### 5. Further Radar Parameterization Layer

Suggested file scope:

- [src/components/systems/sensor.h](../../../../src/components/systems/sensor.h)
- [src/models/systems/default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- `examples/config/database/aircraft/modules/sensors/*.json`
- Relevant sensor configuration under `examples/config/database/ships/`

P1 recommends doing:

- Derive/validate default `range_power` by `SensorType`
- Clarify the calibration convention for `reference_range_m / reference_rcs_m2 / reference_snr_db`
- Continue using front/side/rear RCS, but update parameter tables to traceable values
- Advance `doppler notch` from a hard constant toward a tunable threshold/taperable degradation

P1 does not recommend doing:

- Full equation-level parameterization of `Pt / G / lambda / B / F / PRF`
- `Swerling 0-IV`
- Waveform/PRF adaptive switching

### 4.2 Items Explicitly Deferred to P2

The following items should remain in `P2` to prevent P1 from expanding out of control:

1. Full `Kalman / IMM / JPDA / MHT`
2. Truly breaking away from the `entity_id`-based track association system
3. Full Link 16 / J-series / reporting responsibility / time slot capacity
4. Full `Mode 4/5`, time synchronization, encrypted challenge-response
5. `NCTR` micro-Doppler/JEM identification
6. Detailed terrain obscuration, sea clutter maps, ground clutter maps, ducting propagation
7. Full radar parameter equations, waveform switching, Swerling scintillation
8. DRFM / RGPO / VGPO / angle deception
9. Independent high-fidelity modeling of IRST / MAWS / DAS

---

## V. Suggested File Scope

### 5.1 P1 Pre-Integration Wrap-Up

- `src/content/unit_definition_loader.cpp`
- `src/models/core/default_unit_factory.h`
- `src/core/engine/simulation_kernel_observation_api.cpp`
- `src/interfaces/python/bindings_core.cpp`
- `src/interfaces/python/bindings_command.cpp`
- `python/testing/runtime.py`
- `tests/runtime/test_bindings_command_surface.py`
- `tests/runtime/test_sensor_situation_realism_p0.py`
- Other affected runtime/contract tests

### 5.2 P1 Deepening Realism

- `src/components/systems/sensor.h`
- `src/components/systems/track_management.h`
- `src/models/systems/default_sensor_model.cpp`
- `src/models/environment/default_environment_model.cpp`
- `src/systems/systems/track_manager_system.h`
- `src/systems/systems/data_link_system.h`
- `examples/config/database/aircraft/modules/sensors/*.json`
- `examples/config/database/aircraft/units/*.json`
- `examples/config/database/ships/**/*.json`

---

## VI. Minimal Test Checklist

### 6.1 Pre-Integration Wrap-Up

1. New `sensor` fields can be correctly read from configuration, and default values are stable.
2. Python observation can see `track status / quality / confidence`.
3. Python `Detection` can see `snr_db / detection_prob_used / measured_vr`.
4. `ReportTrack` and `ReportContact` co-exist compatibly on the Python side.
5. Running tests no longer treat the receiver's local `ContactList` as the result of data link sharing.

### 6.2 Deepening Realism

1. Minimal weather attenuation (rain/fog, etc.) reduces long-range `Pd`, and the trend is monotonic.
2. Look-down / low radial velocity targets are harder to confirm under clutter penalty.
3. `2-of-3` is no longer just a cumulative hit count; it has explicit behavior regarding misses and window semantics.
4. `Coasted` track quality degrades over time and drops after timeout.
5. Friendly aircraft IFF reply can make `identity` converge from `Unknown`/`AssumedFriendly` toward `Friendly`.
6. For the same target, `Radar + DataLink` no longer generates duplicate tracks, and the `Fused/source_mask` semantics hold.

### 6.3 Regression Gatekeeping

1. At least sample re-run of the situation-related key scenarios in `naval_screen`, `mission_runtime`, `air_combat_1v1`.
2. If unrelated failures still exist, the acceptance record must differentiate:
   - Introduced by this line
   - Pre-existing historically
   - Caused by shared integration

---

## VII. Data Source Implementation Plan

P1 does not aim for classified-level model replication, but must make parameter sources "traceable, replaceable, and tiered".

### 7.1 Data Source Tiers

#### Tier A: Preferred Sources

- MathWorks public Radar/Tracking documentation
- ITU-R public recommendations
  - Rain attenuation
  - Atmospheric absorption
  - Public models related to radio horizon/path loss
- Public target tracking textbooks / alpha-beta filter materials

Applicable to:

- `Pd/SNR`
- `M-of-N`
- `alpha-beta`
- Weather attenuation
- Radio line-of-sight

#### Tier B: Engineering Usable

- Public platform/radar promotional materials
- AWACS, ship mast height, radar magnitude, typical scan periods
- Public RCS magnitude ranges, target classification materials

Applicable to:

- `reference_range_m`
- `reference_rcs_m2`
- Ship/AWACS height
- Fighter radar / AWACS baseline defaults

#### Level C: Preliminary values or sanity checks only

- Community databases
- Enthusiast materials
- Forum collations
- Open‑source simulation configurations

Applicable to:

- Initial parameters when no better sources are available
- Cross‑checking against Level A/B materials

### 7.2 Implementation approach

It is recommended to maintain two layers simultaneously:

1. `Code configuration layer`
   - Write the final default parameters into `examples/config/database/.../sensors/*.json`
2. `Traceability document layer`
   - Add a new reference table document or spreadsheet under `docs/task/flight_dynamics/`
   - At a minimum record:
     - Parameter name
     - Adopted value
     - Applicable object
     - Source level
     - Public source description
     - Whether it is an engineering approximation

P1 advises against stuffing data source traceability into the README or the task master table for now.

---

## VIII. Acceptance criteria

Upon completion of P1, at least the following must be satisfied:

1. `P0` The new fields and new semantics have been fully wired through to configuration, runtime, observation, and Python.
2. The situational awareness master contract no longer confuses "local detection contacts" with "shared tracks".
3. Track `status / quality / source` can be read stably by upper layers.
4. At least one realistic element each from environment, IFF, fusion, and track quality has entered the run results and is covered by gate‑keeping tests.
5. Legacy test semantics have been migrated or explicitly deprecated; the old truth‑style behavior is no longer accepted by default.

---

## IX. Recommended implementation order

### Step 1

First complete `loader / factory / observation / binding` to truly wire through the P0 fields and semantics.

### Step 2

Uniformly migrate legacy test contracts, especially data‑link sharing and observation surfaces.

### Step 3

Refine `track status / quality / sliding M‑of‑N / coast‑drop` to stabilise the track semantics first.

### Step 4

Introduce conservative environment/clutter and a minimal IFF state machine to give the "detect‑confirm‑identify" chain its first complete pass.

### Step 5

Implement minimal fusion of `Radar + DataLink` and `TrackSource::Fused`, then add another layer of radar parameterisation.

---

## X. Summary of P1 vs. P2 boundaries

### Should be conservatively included in P1

1. Finalisation of `loader/factory/observation/binding` for new fields
2. Migration of legacy test semantics
3. Refinement of `track status / quality / M‑of‑N`
4. Minimal weather attenuation and clutter penalty
5. Minimal IFF state machine
6. Minimal `Radar + DataLink` fusion
7. One traceable layer of radar parameterisation and default‑value correction

### Remain for P2

1. Full multi‑target tracking and complex association
2. Complete Link‑16 protocol simulation
3. Full Mode‑4/5 and NCTR
4. Detailed environment propagation and clutter fields
5. Complete radar equation and waveform/PRF
6. Deception jamming and high‑fidelity ECM/ESM

This package is frozen until the next explicit reopening of direction‑two tasks.
