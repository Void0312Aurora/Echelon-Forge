<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_p0_implementation_package_20260516.zh.md. Review before treating this file as authoritative. -->

# Sensor/Situational Realism P0 Implementation Package

Status: `2026-05-16` – Workable Frozen Version.

Related documents:

- [Sensor and Situational Awareness Realism Analysis](sensor_situation_realism_analysis_20260516.zh.md)
- [Sensor/Situational Awareness Realism Verification and Implementation Plan](sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md)
- [Weapon System and Guidance Loop Realism Verification and Implementation Plan](../weapon_guidance/weapon_guidance_realism_verification_and_plan_20260516.zh.md)

Core code locations:

- [Sensor component](../../../../src/components/systems/sensor.h)
- [TrackManagement component](../../../../src/components/systems/track_management.h)
- [Comm component](../../../../src/components/systems/comm.h)
- [CommMsgType](../../../../src/components/command/common/comm_message.h)
- [UnitDefinition Loader](../../../../src/content/unit_definition_loader.cpp)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)

Purpose of this document:

- Consolidate Direction 2 into a `P0` work package that is sufficiently small but actually actionable.
- Clearly define what `P0` includes and excludes.
- Freeze fields, files, tests, and external data adoption criteria to prevent divergence during implementation.

---

## 1. P0 Objective

P0 only addresses four things:

1. Upgrade radar detection from `range_factor * detection_prob` to `SNR/Pd approximation`.
2. Introduce `M-of-N` confirmation for local detections, preventing a single plot from immediately becoming a tactically usable track.
3. Add minimal `alpha-beta` position/velocity filtering to `TrackManager`.
4. Make `DataLink` no longer directly write to the receiver’s `ContactList`, but only report track-level information.

The delivery goal of P0 is not a "complete sensor simulation", but to make the following statements true for the first time:

- The local `ContactList` represents single-sensor measurement contacts, no longer mixed with shared situational awareness.
- `TrackDatabase` is the cross-scan, sharable, filterable, confirmable tactical picture.
- Distant weak targets will first experience `low Pd -> tentative -> confirmed`, rather than "a single dice roll success leads to firing".
- DataLink shares `track report`, not "a copied contact disguised as a local radar hit".

---

## 2. P0 Non-Objectives

This package explicitly does **not** include:

1. Full Kalman, JPDA, MHT, or multi-hypothesis association.
2. Full IFF/Mode 4/5, NCTR, behavior recognition.
3. DRFM deception, angle deception, complex ECM/ESM countermeasures.
4. High-fidelity environment modeling of sea/ground clutter, ducting, non-standard refraction.
5. True multi-sensor fusion and formal activation of `TrackSource::Fused`.
6. Major restructuring of Python/RL observation structures.
7. Classified or type-exact parameter reproduction.

These items either belong to `P1/P2`, or would significantly expand the scope of changes and are not suitable for inclusion in the current work package.

---

## 3. P0 Success Criteria

After P0 is completed, at least the following must hold:

1. Radar detection probability is determined by `snr_db -> pd`, and is monotonically reasonable with respect to range and RCS.
2. A single detection does not immediately generate a `confirmed` track.
3. `x/y/z/vx/vy/vz` in `TrackDatabase` no longer remain "position updated, velocity all zeros" for extended periods.
4. After DataLink sharing, the receiver obtains tracks with `TrackSource::DataLink`, but the local `ContactList` does not suddenly contain shared targets.
5. Existing tests for `mission_runtime`, `naval_screen`, `air_combat_1v1` either continue to pass, or are explicitly and minimally updated to the new semantics.

---

## 4. Specific Files to Add/Modify

### 4.1 Mandatory Modifications

#### 1. Components and Configuration

- [src/components/systems/sensor.h](../../../../src/components/systems/sensor.h)
  - Add fields required for SNR/Pd and M-of-N
  - Extend `Detection`

- [src/components/systems/track_management.h](../../../../src/components/systems/track_management.h)
  - Add `TrackStatus` and minimal filtering/quality fields

- [src/components/systems/comm.h](../../../../src/components/systems/comm.h)
  - Add minimal track report fields to `CommPacket`

- [src/components/command/common/comm_message.h](../../../../src/components/command/common/comm_message.h)
  - Add `ReportTrack`

- [src/content/unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
  - Read new `sensor` fields

#### 2. System Logic

- [src/models/systems/default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
  - Introduce `snr_db` calculation
  - Introduce `pd_from_snr()` approximation
  - Produce extended `Detection`

- [src/systems/systems/track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)
  - Implement tentative/confirmed/coast lifecycle
  - Implement minimal `alpha-beta` filtering
  - Implement `ReportTrack` reception logic

- [src/systems/systems/data_link_system.h](../../../../src/systems/systems/data_link_system.h)
  - Remove logic that directly writes to the receiver's `ContactList`
  - Only send `ReportTrack`

### 4.2 Files Recommended for Simultaneous Adjustment

- [src/models/core/default_unit_factory.h](../../../../src/models/core/default_unit_factory.h)
  - Behavior not changed for now, but ensure `TrackDatabase` initialization is safe for new fields

- [src/core/engine/simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp)
  - P0 default: do not change observation schema
  - Only supplement `closing_speed` or filter unconfirmed tracks if necessary

### 4.3 New Test Files

- `tests/runtime/air_combat/test_sensor_track_runtime_contracts.py`

If finer granularity is desired, it can be split into:

- `tests/runtime/air_combat/test_sensor_pd_snr.py`
- `tests/runtime/air_combat/test_track_manager_p0.py`
- `tests/runtime/link/test_datalink_track_reporting.py`

However, for P0 it is recommended to start with a single test file to reduce organizational overhead.

---

## 5. Field Design

P0 adds only the minimum fields, prioritizing not introducing large, comprehensive structures.

### 5.1 `Sensor` Fields

File:

- [sensor.h](../../../../src/components/systems/sensor.h)

Proposed additions:

```cpp
double reference_snr_db;      // Reference single-dwell SNR at reference_range_m / reference_rcs_m2
double reference_range_m;     // Calibration reference range
double reference_rcs_m2;      // Calibration reference RCS
double pfa;                   // False alarm probability, default 1e-6 for P0
int confirm_hits_m;           // M of M-of-N
int confirm_window_n;         // N of M-of-N
double velocity_noise_std;    // Radial velocity measurement noise
double alpha_beta_alpha;      // Recommended to allow default filter parameters per sensor type
double alpha_beta_beta;
```

P0 recommends **not** adding the following yet:

- `Pt/G/B/F`
- `n_pulses`
- `supports_iff_interrogation`
- Full environment/clutter parameters

These would expand the scope of this round.

### 5.2 `Detection` Fields

File:

- [sensor.h](../../../../src/components/systems/sensor.h)

Proposed additions:

```cpp
double snr_db;
double detection_prob_used;
double measured_vr;
int sensor_type;
bool local_sensor_hit;
```

Usage:

- `snr_db` and `detection_prob_used` directly serve realism testing and debugging
- `measured_vr` provides an entry point for P0's velocity estimation

### 5.3 `SystemTrack` Fields

File:

- [track_management.h](../../../../src/components/systems/track_management.h)

Proposed additions:

```cpp
enum class TrackStatus {
    Tentative = 0,
    Confirmed,
    Coasted
};

TrackStatus status;
double quality;
int confirm_hit_count;
int confirm_miss_count;
double last_update_time;
double last_local_update_time;
double last_datalink_update_time;
double alpha_beta_alpha;
double alpha_beta_beta;
```

P0 recommends **not** introducing matrix covariance now; use `quality + time_since_update + status` as the minimal quality representation.

### 5.4 `CommMsgType` and `CommPacket`

Files:

- [comm_message.h](../../../../src/components/command/common/comm_message.h)
- [comm.h](../../../../src/components/systems/comm.h)

Proposal:

- Add `CommMsgType::ReportTrack`
- Add minimal fields to `CommPacket`:

```cpp
uint64_t track_ref;
double velocity_x;
double velocity_y;
double velocity_z;
double quality;
int source_code;
```

P0 still retains `entity_ref` for truth comparison and compatibility with existing logic, but it should be explicitly a transitional debugging hook.

---

## 6. Core Implementation Constraints

### 6.1 `SNR/Pd` Approximation Constraints

P0 recommends:

1. First compute `snr_db` based on reference quantities
2. Then map to `Pd` using a logistic or Albersheim-style approximation

Recommended function form:

```text
snr_linear = snr_ref_linear
           * (sigma / sigma_ref)
           * (range_ref / range)^4
           * env_factor
           * doppler_factor
           * jam_factor

pd = 1 / (1 + exp(-k * (snr_db - snr_50_db)))
```

Engineering simplifications allowed in P0:

- `sigma` can still use three-point interpolation (frontal/side/rear)
- `doppler_factor` can still retain empirical degradation, but applied to `snr_db`
- `jam_factor` can still retain a burn-through threshold, but output to the SNR chain

P0 **does not** allow retaining:

- `range_factor = 1 - (R/Rmax)^n` as the primary source of detection probability

### 6.2 `M-of-N` Confirmation Constraints

P0 only implements window-based confirmation for a single target/single track, not complex association.

Recommended defaults:

- Fighter radar: `2-of-3`
- AWACS/long-range surveillance: `2-of-2` or `3-of-4`

Minimum semantic requirements:

- First hit -> `Tentative`
- Accumulated hits within the window reach threshold -> `Confirmed`
- On miss, first `Coasted`
- Delete on timeout

### 6.3 `alpha-beta` Filter Constraints

P0 only implements minimal filtering in Cartesian coordinates:

- Predict: `x += vx * dt`
- Update: `x += alpha * residual`
- Velocity: `vx += beta / dt * residual`

Recommended default parameter ranges:

- Fighter radar: `alpha = 0.65`, `beta = 0.12`
- AWACS: `alpha = 0.45`, `beta = 0.06`

P0 does not do:

- IMM
- EKF/UKF
- Covariance matrix output

### 6.4 `DataLink` Constraints

P0 must satisfy:

- `DataLinkSystem` no longer writes the sender's contact directly to the receiver's `ContactList`
- Only sends `ReportTrack`
- The receiver's `TrackManager` decides whether to create a `TrackSource::DataLink` track

P0 allows during the transition:

- Still use `entity_ref` in the message for target correlation
- But no longer generate "shared contacts that look like local plots"

---

## 7. Test Checklist

### 7.1 New Tests

#### 1. `test_radar_pd_decreases_with_range_and_increases_with_rcs`

Verify:

- Under the same reference configuration, increasing range does not increase `snr_db` and `Pd`
- Larger RCS yields higher `snr_db` and `Pd`

#### 2. `test_single_hit_creates_tentative_not_confirmed_track`

Verify:

- The first detection only creates a `Tentative` track
- It does not immediately become an observable/tactically usable confirmed track

#### 3. `test_two_of_three_promotes_track_to_confirmed`

Verify:

- The `2-of-3` hit window works correctly
- The hit sequence is deterministic

#### 4. `test_alpha_beta_filter_estimates_velocity_for_constant_velocity_target`

Verify:

- For a constant velocity target, `vx/vy/vz` converge gradually
- Filtered trajectory jitter is less than raw measurements

#### 5. `test_datalink_shared_track_does_not_create_local_contact`

Verify:

- When the receiver has no local sensor detection, `ContactList` does not contain the shared target
- But `TrackDatabase` has a `TrackSource::DataLink` track

#### 6. `test_datalink_report_track_reaches_hvu_picture`

To replace the current `ReportContact` semantic test:

- Corresponds to [test_naval_screen_scenario.py](../../../../tests/runtime/naval/test_naval_screen_scenario.py)

### 7.2 Existing Tests Requiring Updates

The following tests will likely need synchronized updates after P0:

- [tests/runtime/naval/test_naval_screen_scenario.py](../../../../tests/runtime/naval/test_naval_screen_scenario.py)
  - Reason: Current assertions still explicitly depend on `ReportContact`

- [tests/runtime/mission/test_mission_runtime.py](../../../../tests/runtime/mission/test_mission_runtime.py)
  - Reason: The shared situational awareness path must still exist, but the semantics of "shared contact" vs "local contact" need recalibration

- [tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py](../../../../tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py)
  - Reason: If the launch precondition changes to `confirmed track`, more steps or clearer detection confirmation conditions are needed

P0 does not recommend major restructuring of these tests, only adjusting their semantics and waiting conditions.

---

## 8. External Data Adoption

P0 does not require that all reference values be written into a database in this round, but the "how" of adoption must be unified.

### 8.1 Data Source Hierarchy

From highest to lowest credibility:

1. `Official/Standard`
   - MathWorks radar/tracking documentation
   - ITU-R P.838 / P.840
   - FAA / NOAA / UCAR public materials on radar horizon / propagation

2. `Public Engineering Materials`
   - Vendor brochures
   - Congressional/audit public documents
   - Academic course public slides

3. `Unofficial but Systematic Databases`
   - [Cmano-DB](https://cmano-db.com/)

### 8.2 Recommended Parameter Adoption Method for P0

For each radar type, adopt only three parameters initially:

1. `reference_range_m`
2. `reference_rcs_m2`
3. `reference_snr_db`

Do not hardcode a "theoretical maximum detection range" directly in the database; instead, use these three to back-calculate `snr_db`.

Recommended approach:

- If public materials state "detection range about 80 km for a 5m² target"
- Then set `reference_range_m = 80000`
- `reference_rcs_m2 = 5`
- `reference_snr_db` to a value that makes the detection probability at that range point approach the selected `Pd` threshold

In other words, P0 first translates the public "detection range" into a unified reference point, rather than directly using magic constants.

### 8.3 Recommended Documentation

Before P0 is complete, external data is recommended to be recorded in documentation first, without rushing to create a separate directory.

It is recommended to later add:

- `docs/standards/sensors/sensor_reference_notes_20260516.md`

Suggested recording format:

- Sensor name
- Source link
- Original magnitude
- Converted value used
- Reason for adoption
- Uncertainty notes

During the P0 code implementation phase, only the final converted values will be written into JSON / loader.

---

## 9. Recommended Implementation Order

P0 recommends splitting into `6` steps, executed in order:

### Step 1. Freeze component fields and loading paths

Modify:

- `sensor.h`
- `track_management.h`
- `comm.h`
- `comm_message.h`
- `unit_definition_loader.cpp`

Objective:

- Get the new fields compiled
- Do not change runtime semantics

Completion criteria:

- Full compilation passes
- Existing sensor tests remain unchanged

### Step 2. Introduce `snr_db` and `pd_from_snr()` in `DefaultSensorModel`

Modify:

- `default_sensor_model.cpp`

Objective:

- Keep the existing scanning flow unchanged
- Only replace the source of "single dwell probability"

Completion criteria:

- `Detection` now includes `snr_db`
- Range/RCS monotonicity tests pass

### Step 3. Introduce `Tentative/Confirmed/Coasted` in `TrackManagerSystem`

Modify:

- `track_manager_system.h`

Objective:

- First implement the M-of-N lifecycle
- Do not yet connect alpha-beta

Completion criteria:

- `single hit != confirmed`
- `2-of-3 => confirmed`

### Step 4. Integrate minimal `alpha-beta` filter in `TrackManagerSystem`

Modify:

- `track_manager_system.h`

Objective:

- Add position/velocity prediction and update for both confirmed and tentative tracks

Completion criteria:

- A constant velocity target converges to non-zero `vx/vy/vz`

### Step 5. Change `DataLinkSystem` to `ReportTrack` only

Modify:

- `data_link_system.h`
- `track_manager_system.h`

Objective:

- Remove injection into receiver's `ContactList`
- Only retain track sharing

Completion criteria:

- Receiver still gets `TrackSource::DataLink`
- Receiver's `ContactList` does not grow due to sharing

### Step 6. Adjust existing runtime tests and add P0 gate tests

Modify:

- Add `tests/runtime/air_combat/test_sensor_track_runtime_contracts.py`
- Update `test_naval_screen_scenario.py`
- Update `test_mission_runtime.py` and `test_air_combat_1v1_fire_missile.py` if necessary

Completion criteria:

- New P0 tests pass
- Affected old tests return to green

---

## 10. Recommended Minimum Kickoff Strategy

If only a very small branching is allowed, it is recommended to split into the following "minimum committable units":

1. `fields-only`:
   - Only change component fields and loader
2. `sensor-pd`:
   - Only replace the `Pd` logic in `DefaultSensorModel` with `SNR/Pd`
3. `track-confirmation`:
   - Only add `Tentative/Confirmed`
4. `track-filter`:
   - Only add `alpha-beta`
5. `datalink-track-report`:
   - Only cut off `ContactList` injection

This way each PR has clear semantics and is easier to locate regressions.

---

## 11. Current Freeze Conclusions

The `P0` for Direction 2 should stop discussing "whether to make it more realistic" and instead directly enter the following concrete package:

1. `Sensor`: Add reference SNR / Pfa / M-of-N / alpha-beta parameters
2. `DefaultSensorModel`: Replace empirical probability with `SNR/Pd`
3. `TrackManager`: Add `Tentative/Confirmed/Coasted + alpha-beta`
4. `DataLink`: Change to `ReportTrack`, stop writing to `ContactList`
5. `Tests`: Add P0 gate tests, minimally update existing shared situational awareness tests

Once this package lands, the current sensor/situational awareness system will transition from a "training-level contact replicator" to a "minimally usable tactical situation chain" level. This is also the most worthwhile step to take before advancing further toward air combat realism.
