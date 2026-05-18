<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_verification_and_implementation_plan_20260516.zh.md. Review before treating this file as authoritative. -->

# Sensor/Situational Awareness Realization Verification and Implementation Plan

Status: `2026-05-16` Direction Two Execution Draft.

Related Inputs:

- [传感器与态势感知现实性分析](sensor_situation_realism_analysis_20260516.zh.md)
- [DefaultSensorModel](../../../../src/models/systems/default_sensor_model.cpp)
- [SensorSystem](../../../../src/systems/systems/sensor_system.h)
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h)
- [DataLinkSystem](../../../../src/systems/systems/data_link_system.h)
- [EWSystem](../../../../src/systems/systems/ew_system.h)
- [DefaultEnvironmentModel](../../../../src/models/environment/default_environment_model.cpp)
- [Sensor 组件](../../../../src/components/systems/sensor.h)
- [TrackManagement 组件](../../../../src/components/systems/track_management.h)
- [DataLink 组件](../../../../src/components/systems/data_link.h)
- [Comm 组件](../../../../src/components/systems/comm.h)
- [UnitDefinition Loader](../../../../src/content/unit_definition_loader.cpp)

Document Purpose:

- Verify which judgments from the current research have been confirmed by code, which need correction or supplementation.
- Provide a landing plan that fits the current ECS/component structure, not engaging in abstract "ideal systems."
- Gather a set of sufficiently reliable data sources that can directly serve parameterization and approximate calibration.
- Provide a clear entry sequence for subsequent code modifications and realism testing.

---

## A. Verification Conclusions

### A.1 Overall Judgment

The general direction of the current research is **accurate**: the current system is closer to an "RL training-level sensor abstraction" rather than a "fire-control-grade radar/track/data link simulation."

However, after examining the code, the conclusions need to be categorized into three types:

1. **Fully Accurate**
2. **Basically Accurate, but the description needs greater precision**
3. **Missing points that need supplementation**

### A.2 Fully Accurate Conclusions

#### 1. Current Detection Probability is Not an SNR/Pd Model

Accurate.

- The main detection chain from [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp:127) to [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp:212) is still:
  `FOV/range gating -> range_factor -> aspect_factor -> doppler_factor -> weather/sun factor -> detection_prob`
- `signal_strength` is calculated only after [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp:235) and is used only for outputting `Detection.signal_strength`, without feeding back into detection success probability.

Therefore, the judgment of "no SNR threshold, no Pd(Pfa,SNR) mapping" is accurate.

#### 2. No M-of-N Detection Confirmation

Accurate.

- [SensorSystem](../../../../src/systems/systems/sensor_system.h:47) directly generates `fresh_contacts` per scan.
- [TrackManagerSystem](../../../../src/systems/systems/track_manager_system.h:131) creates a track immediately upon first seeing a contact.
- There are no tentative/confirmed states, nor `m_hits / n_scans`.

This directly leads to "flickering targets" under marginal detection conditions being immediately treated as usable tracks.

#### 3. Track Management Has No Filter

Accurate.

- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h:135) and [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h:183) both "directly overwrite with latest measurement."
- [SystemTrack](../../../../src/components/systems/track_management.h:24) has `vx/vy/vz`, but the current system has no path to assign values.

Thus the judgment of "no prediction, no smoothing, no velocity estimation, no uncertainty" stands.

#### 4. Data Link Shares Not Filtered Tracks but Contact/Truth Coordinates

Accurate, and actually more severe than described in the original text.

- [data_link_system.h](../../../../src/systems/systems/data_link_system.h:103) directly merges the sender's `ContactList` into the receiver's `ContactList`.
- [data_link_system.h](../../../../src/systems/systems/data_link_system.h:143) also sends `ReportContact` via `CommQueue`.
- The message uses the target entity's true coordinates [data_link_system.h](../../../../src/systems/systems/data_link_system.h:147), not the sender's measurement or filtered estimate.

So currently it's not just "sharing raw contacts," but **sharing contacts plus truth position copy**.

#### 5. IFF/Classification is God's Perspective

Accurate.

- `classify_track_from_alliance()` [/home/void0312/Workshop/CMO/src/systems/systems/track_manager_system.h:13] directly reads `Alliance.side`.
- Both local detections and data link tracks use this path [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h:141), [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h:190).

This is not "simplified IFF," but "bypassing the IFF/identification problem."

#### 6. Environmental Effects on Sensors Are Almost Completely Unused

Accurate.

- `check_line_of_sight()` only checks if endpoints are underground [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp:147).
- `get_weather_attenuation()` always returns `0.0` [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp:153).
- Sun interference is just a multiplication by `0.1` for visual/infrared detection probability [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp:106).

Therefore, weather, terrain masking, clutter, and realistic sun background currently do not form usable physical constraints.

### A.3 Basically Accurate, but Need Correction or Supplement

#### 1. "No Multi-Sensor Fusion" Should Be Corrected to "Framework Allows Multiple Sources, But No Real Fusion"

The original text says "no multi-sensor fusion," which is generally correct, but needs greater precision:

- `TrackSource::Fused` already exists in [track_management.h](../../../../src/components/systems/track_management.h:7).
- The observation interface has already exposed `source` and `classification` to the agent observation [simulation_kernel_observation_api.cpp](../../../../src/core/engine/simulation_kernel_observation_api.cpp:214).

What is truly missing is:

- Multi-source association
- Weighted updates
- Source quality management
- Implementation of the `Fused` state

Therefore, it should be corrected to:

> The current system has "multi-source fields and observation outputs," but has not yet implemented real track-to-track fusion.

#### 2. "No Radio Horizon" is Inaccurate; Should Be "Data Link Horizon Has a First-Order Approximation, But Sensor LOS Has Not"

- The data link already has a standard approximate formula `3.57 * (sqrt(h1) + sqrt(h2))` [data_link_system.h](../../../../src/systems/systems/data_link_system.h:91).
- But sensor LOS still only has endpoint underground determination [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp:147).

Thus a more accurate statement is:

> The data link communication range already uses a 4/3 Earth approximate radio horizon formula; what is truly missing is terrain/curvature masking on the sensor side, and variations under non-standard refraction conditions.

#### 3. "Track ID = entity_id" Needs a Consequence Supplement

The original judgment is accurate, but it should also add:

- Many higher-level logics already depend on `track.id == entity_id`.
- For example, the prerequisite for weapon release is whether `target_id` exists in `ContactList`.

This means decoupling from `entity_id` cannot be done in one step. It must adopt:

- Internally assigned `track_id`
- `entity_ref` only as a debug/truth hook
- Upper interfaces gradually changed to read `track_id + classification + quality`

Otherwise, changing one thing will affect everything.

#### 4. "Jamming Judgment is Binary" Should Be Corrected to "Two-Stage: Pre-Detection Burn-Through Binary Cut, No Continuous Degradation After Detection"

- In [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp:252) onward, if a target has noise suppression jamming and distance is greater than burn-through distance, it directly `return`s.
- This means it's not "first reduce probability, then mask," but a "pre-detection hard cutoff."

Thus a more accurate statement is:

> Current noise jamming is a pre-detection hard kill type, not a continuous degradation based on J/S or S/J.

### A.4 Missing Points That Need Supplementation

#### 1. Current Default `range_power` Configuration for Radar is Clearly Unreasonable

This was not pointed out in the existing analysis documents, but is very important.

- The `Sensor` comment says radar should be close to `R^4` [sensor.h](../../../../src/components/systems/sensor.h:19).
- But in the public configuration, many radars are set to `2.0`:
  - [an_apg_68.json](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json:1)
  - [irbis_e.json](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json:1)
  - [e3_sentry.json](../../../../examples/config/database/aircraft/units/e3_sentry.json:1)

This systematically overestimates long-range radar performance. Even if SNR is not yet introduced, this needs to be corrected as soon as possible.

#### 2. DataLink Configuration Does Not Actually Use the `network_id` from the Database

- The loader reads `has_data_link` and `data_link_network_id` [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp:250).
- But the default factory actually forces assignment by side: `Blue=1, Red=2` [default_unit_factory.h](../../../../src/models/core/default_unit_factory.h:475).

This means the document's "network_id = side" is not just an approximation, but a **hardcoded override**.

#### 3. The Responsibilities of ContactList and TrackDatabase Have Begun to Overlap

In the current code:

- `ContactList` both carries local detections and is directly written by the data link.
- `TrackDatabase` then generates observed tracks from `ContactList + CommQueue`.

This causes increasing semantic confusion as to whether a "contact" is a plot or a shared track. Subsequent realization must separate the two layers early.

#### 4. The Observation Interface Does Not Yet Output Track Quality/Confirmation Status

- The observation currently only outputs `range/azimuth/elevation/closing_speed/time_since_update/source/classification`.
- There is no `confidence`, `track_quality`, `tentative/confirmed`.

Even if M-of-N and filtering are implemented in the backend, if quality is not exposed to the upper agent, the training will treat "low-confidence temporary plots" and "mature tracks" equally.

---

## B. Implementation Plan

The goal is not to build a complete fire control system in one step, but to prioritize supplementing the five most valuable aspects on the current structure:

1. `SNR/Pd` approximation
2. `M-of-N` detection confirmation
3. Basic track filtering
4. Data link upgrade from contact to track
5. Simplified IFF/classification and basic environmental effects

### B.1 Design Principles

#### 1. Keep the Current ECS Main Flow, Do Not Overhaul the System Sequence

Current sequence:

`SensorSystem -> DataLinkFusionSystem -> TrackManagerSystem -> EWSystem`

It is recommended to keep this order, but redefine the responsibilities of each layer:

- `SensorSystem`: Only produces local measurement contacts, not responsible for "track-level sharing."
- `DataLinkSystem`: Shares track reports, no longer directly writes to receiver `ContactList`.
- `TrackManagerSystem`: Solely responsible for tentative/confirmed track lifecycle, local filtering, multi-source fusion, and classification status.

#### 2. Allow Transition Period to Retain `entity_id` Truth Hook, But Downgrade from Business Logic

Short-term retention allowed:

- `Detection.target_id`
- `SystemTrack.entity_id`

But must make clear:

- Use only for testing/debugging/truth comparison.
- No longer used as the sole associative key.

#### 3. First Do "Approximate Reality," Then "Fine Reality"

Priority for this round:

- Single-pulse/single-channel approximation
- Constant false alarm rate using fixed `Pfa`
- `alpha-beta` before Kalman
- IFF state machine before full Mode 5
- Rain/fog/horizon/sun angle before complex clutter maps

### B.2 Data Structure Modification Proposals

#### 1. Extend `Sensor`

Files:

- [sensor.h](../../../../src/components/systems/sensor.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)

Suggested new fields:

```cpp
double reference_snr_db;          // Single detection SNR at reference_range_m, reference_rcs_m2
double reference_range_m;         // Calibration reference range
double reference_rcs_m2;          // Calibration reference RCS
double pfa;                       // False alarm probability, default 1e-6
int confirm_hits_m;               // M-of-N: M
int confirm_window_n;             // M-of-N: N
double revisit_merge_ttl_s;       // Tentative retention time when no updates
double velocity_noise_std;        // Closing speed/radial velocity measurement noise
double iff_interrogation_period_s;
bool supports_iff_interrogation;
```

Rationale:

- This set of fields can get `SNR -> Pd` running without introducing complete radar equation parameters.
- `reference_snr_db` is more suitable for the current database situation than directly plugging in `Pt/G/B/F`.

#### 2. Extend `Detection`

File:

- [sensor.h](../../../../src/components/systems/sensor.h)

Suggested additions:

```cpp
double snr_db;
double detection_prob_used;
double measurement_sigma_range_m;
double measurement_sigma_bearing_deg;
double measurement_sigma_elevation_deg;
int sensor_type;
bool local_sensor_hit;
bool iff_reply_present;
```

Reason:

- These fields can later be fed to the track filter and also directly written to diagnostic/test logs.

#### 3. Extend `SystemTrack`

File:

- [track_management.h](../../../../src/components/systems/track_management.h)

Suggested additions:

```cpp
enum class TrackStatus { Tentative = 0, Confirmed, Coasted, Dropped };
enum class IffState { None = 0, FriendlyReply, NoReply, Ambiguous };
enum class TrackIdentity { Unknown = 0, AssumedFriendly, Friendly, Suspect, Hostile, Neutral };

TrackStatus status;
IffState iff_state;
TrackIdentity identity;

double quality;                  // 0..1
double covariance_pos_m2;
double covariance_vel_m2ps2;
int hit_count_window;
int miss_count_window;
double last_local_update_time;
double last_datalink_update_time;
double last_iff_time;
uint32_t source_mask;            // radar / ir / datalink / rwr
```

Short term, a full matrix covariance is not needed; scalar position/velocity variance suffices.

#### 4. Extend `CommPacket`, Add "Track Report" Payloads

Files:

- [comm.h](../../../../src/components/systems/comm.h)
- [comm_message.h](../../../../src/components/command/common/comm_message.h)

Suggested additions:

```cpp
ReportTrack,
ReportTrackQuality,
ReportIFF
```

And add to `CommPacket`:

```cpp
uint64_t track_ref;
double vx;
double vy;
double vz;
double quality;
int classification_code;
int source_code;
```

This allows upgrading the data link from `ReportContact` to `ReportTrack` without overthrowing the existing message framework.

### B.3 Detection Model: SNR/Pd Approximation

#### 1. Recommended First Version Approximation

File:

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

Suggested replacement of current `detection_prob` generation logic:

1. Compute geometric gating:
   - Range
   - FOV
   - LOS
2. Compute equivalent `sigma_rcs`:
   - Based on `RCSProfile` frontal/side/rear interpolation
3. Compute reference SNR scaling:
   - Radar: `snr_linear = snr_ref_linear * (sigma / sigma_ref) * (R_ref / R)^4 * env_factor * jam_factor * aspect_doppler_factor`
   - IR/Visual: Keep `R^-2` family for now, but also convert to "equivalent SNR"
4. Map `snr_db` to `Pd`:
   - First use Albersheim approximation or logistic fit
5. Output single `Detection`

#### 2. Recommended Engineering Approximation Formula

First phase, do not require full Marcum-Q; use:

```text
Pd = 1 / (1 + exp(-k * (snr_db - snr_50_db)))
```

Where:

- `snr_50_db` is approximated from `Pfa` and number of integrated pulses
- `k` controls threshold steepness

For a step further, can be done as:

```text
Pd = logistic(albersheim_margin_db)
albersheim_margin_db = snr_db - snr_required_db(pd_ref, pfa, n_pulses)
```

In the current project, this is already much more reliable than `1 - (R/Rmax)^n`.

#### 3. Minimum Landing Plan for RCS Pattern

Files:

- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)
- [ew.h](../../../../src/components/systems/ew.h)

Suggestion:

- Interpolate using target aspect angle over three points: frontal/side/rear.
- Do not do full Swerling I-IV family for now.
- But allow adding an `rcs_fluctuation_std_db`.

For example:

- Near head-on: use `frontal_rcs`
- Near 90 degrees: use `side_rcs`
- Near tail chase: use `rear_rcs`
- Linear or cosine interpolation
- Each scan, add a small random fluctuation, e.g., `N(0, 2~4 dB)`

This is significantly better than "always frontal_rcs".

#### 4. First Version Correction for Doppler and Beam Aspect

The current `0.1` multiplier is too coarse. Suggested change:

- For radar, add `clutter_notch_speed_mps`.
- Add `beam_aspect_penalty`.
- When `|v_closing| < notch` and target in look-down/low-altitude background, directly reduce `snr_db` by a fixed amount, e.g., `-12 dB`.
- When pure air-to-air, sky background, reduce only `-4 ~ -6 dB`.

This separates "completely blind / partially degraded / normal."

### B.4 M-of-N Detection Confirmation

#### 1. Suggested Placement in `TrackManagerSystem` Instead of `SensorSystem`

Reason:

- `SensorSystem` is more suitable for measurement generation only
- `TrackManagerSystem` naturally handles the contact → track lifecycle

#### 2. Specific Implementation

Files:

- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

It is recommended to introduce a two‑layer object:

- `MeasurementContact`: a single‑scan contact (point)
- `SystemTrack`: a track maintained across scans

For now, you do not need to create a new component name. You can first add states in `SystemTrack`:

- When creating a contact, initially set it as `Tentative`
- If the number of hits in the last `N` scans is `>= M`, upgrade to `Confirmed`
- If consecutive misses occur, transition to `Coasted`
- Delete when `coast_timeout_s` is exceeded

Recommended default values:

- Airborne fire control radar: `2‑of‑3`
- Large AWACS / maritime search: `2‑of‑2` or `3‑of‑4`
- IRST: `2‑of‑4`

#### 3. Compatibility with Existing Upper‑Level Logic

Short‑term suggestion:

- `ContactList` can remain as‑is for compatibility
- But weapon launch, shared situational awareness, and agent trusted tracks should only read `Confirmed track`

That is, separate "tactically usable" from "sensor has seen".

### B.5 Basic Track Filtering

#### 1. Phase One: `alpha‑beta` is sufficient

File:

- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

For each `SystemTrack`, it is recommended to maintain:

- `x/y/z`
- `vx/vy/vz`
- `covariance_pos_m2`
- `covariance_vel_m2ps2`

Update procedure:

1. Predict
   - `x += vx * dt`
   - `y += vy * dt`
   - `z += vz * dt`
2. Update with measurement residual
   - `x += alpha * rx`
   - `vx += beta/dt * rx`
   - Same for other axes

Recommended starting values:

- High‑refresh airborne radar: `alpha=0.55~0.75`, `beta=0.05~0.18`
- Low‑refresh AWACS: `alpha=0.35~0.55`, `beta=0.02~0.10`

#### 2. Fusion of Data‑Link Track with Local Track

If a local track already exists:

- When a local measurement hits, update primarily with local data
- Data‑link messages only provide auxiliary correction or update `source_mask`

If only data‑link data is available:

- You can directly create a `Tentative` track or a `Confirmed remote track`
- But the quality and timeliness should be lower than local fire‑control tracks

### B.6 Data‑Link: Upgrade from Contact to Track

#### 1. Stop Directly Writing to the Receiver’s `ContactList`

This is one of the most important structural changes.

Currently [data_link_system.h](../../../../src/systems/systems/data_link_system.h:103) directly places the sender’s contacts into the receiver’s contact list, which confuses “local detection” with “shared track”.

Suggestion:

- `DataLinkSystem` should only send `ReportTrack`
- The receiver should no longer write it into `ContactList`
- `TrackManagerSystem` consumes `ReportTrack` from `CommQueue` and generates tracks with `TrackSource::DataLink`

#### 2. Report Content

What should be transmitted is not raw contacts, but:

- `track_id` or `remote_track_ref`
- `x/y/z`
- `vx/vy/vz`
- `quality`
- `classification_code`
- `timestamp`
- `age`
- `source_code`

#### 3. Minimal Duty Control

This round does not require a full Link‑16 network management, but it is recommended to add two things first:

- `report_min_quality`
- “Only the highest‑quality node reports the same target”

Implementation can be simple:

- Sender iterates through its own `TrackDatabase`
- Only reports `Confirmed` tracks
- For each target, only the highest‑quality track is sent by this node

### B.7 Simplified IFF / Classification

#### 1. Do Not Aim for Full Mode 5, but Remove the “God‑Eye” Direct Read

It is recommended to add a minimal IFF state machine:

- Platform can optionally have `supports_iff_interrogation`
- Target can optionally have `has_iff_transponder`
- Friendly with normal reply: `FriendlyReply`
- No reply: `NoReply`
- Declared friendly via data link but no local reply: `AssumedFriendly`
- Judged hostile by behavior/alliance rules: `Suspect → Hostile`

#### 2. Placement in Current Code Structure

It is recommended to add:

- `src/components/systems/iff.h`
- `src/systems/systems/iff_system.h`

If you prefer not to add a new system for now, you can also implement it in [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h):

- After a local radar hit, if both the owner and target have IFF components and the interrogation cycle is reached, update `iff_state`
- `classification` should no longer directly equal `Alliance.side`

#### 3. Recommended Simplified Classification Mapping

- `Friendly`: received a trustworthy IFF reply
- `AssumedFriendly`: only a data‑link friendly declaration or known mission formation
- `Unknown`: no reply and no other evidence
- `Suspect`: no reply and abnormal behavior/area
- `Hostile`: clearly an enemy belligerent, red‑network, weapon launch, or rule‑based forced enemy status

For short‑term compatibility with the existing `TrackClass`, you can map back to:

- `Friendly`
- `Hostile`
- `Neutral`
- `Unknown`

And store the finer identity in a new field.

### B.8 Basic Environmental Effects

#### 1. Start with 4 “Measurable and Stable” Items

Files:

- [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

Priority additions:

1. `Terrain/Curvature LOS`
2. `Weather attenuation`
3. `Sun angle / background strong degradation`
4. `Low‑altitude clutter penalty`

#### 2. Suggested Modification for LOS

`check_line_of_sight()` should be changed from endpoint‑only check to:

- Sample `8‑32` intermediate points along the path
- If any point’s terrain is higher than the line‑of‑sight height, the path is obstructed
- Optionally add Earth curvature drop term

This is enough to support first‑order effects such as “mountain blocking” and “low‑altitude sea‑skimming difficulty”.

#### 3. Suggested Modification for Weather

The current class already has `weather_zones_`, but it is not actually used [default_environment_model.cpp](../../../../src/models/environment/default_environment_model.cpp:70).

Suggestion:

- First connect `WeatherZoneImpl` to `get_weather_attenuation()`
- Return different attenuations for different sensor types
  - Visual: heavy attenuation from fog/clouds
  - IR: moderate attenuation from clouds/humidity/rain
  - Radar: rain attenuation, light attenuation from clouds/fog

Phase one can use range‑based attenuation:

- clear: `0 dB/km`
- light rain: `0.02~0.08 dB/km`
- moderate rain: `0.1~0.3 dB/km`
- heavy rain/X‑band: `0.4 dB/km` and above

Finally, convert the path length into an `snr_db` reduction instead of directly multiplying a probability.

#### 4. Suggested Modification for Sun/Background

Currently `sun_factor = 0.1` is too weak.

Suggestion:

- For Visual/IR, when the angle between the target and the sun is less than a threshold, directly reduce `snr_db`
- The threshold should be different per sensor type
  - Visual: `5‑8 deg`
  - IR: `3‑6 deg`

It is not always completely blocked, but there should be windows where the sensor is nearly unusable.

### B.9 Testing Suggestions

It is recommended to add a new set of “direction‑two realism gate tests” at least including:

#### 1. `test_sensor_pd_snr_monotonicity`

Verify:

- For the same target and environment, `snr_db` does not increase as distance increases
- `Pd` is monotonic with respect to `snr_db`
- Side‑aspect low RCS is lower than nose‑aspect high RCS

#### 2. `test_track_confirmation_m_of_n`

Verify:

- A single hit does not immediately become confirmed
- Upgrade after `2‑of‑3`
- Coast / drop after consecutive misses

#### 3. `test_alpha_beta_track_velocity_estimation`

Verify:

- For a target moving with constant velocity, `vx/vy/vz` converge to the true values
- With measurement noise, the track position jitters less than the raw contacts

#### 4. `test_datalink_reports_tracks_not_contacts`

Verify:

- When the receiver has no local detection, `ContactList` is empty but `TrackDatabase` contains `DataLink` tracks
- Data‑link tracks should not masquerade as local radar hits

#### 5. `test_iff_reply_and_unknown_behavior`

Verify:

- Friendly with reply → Friendly
- No reply → Unknown / AssumedFriendly
- No longer directly equals `Alliance.side`

#### 6. `test_environment_weather_and_los_penalties`

Verify:

- Path through rain zone has lower `snr_db` than clear path
- Detection is blocked by mountain obstruction
- Low‑altitude beam/notch conditions are significantly harder to detect

---

## C. Data Source Suggestions

Principles:

- Official/standards preferred
- Public engineering materials and high‑quality civilian databases can serve as approximate calibrations
- For specific aircraft parameters, prefer “multi‑source cross‑checked reasonable range” over a single exaggerated promotional value

### C.1 SNR / Pd / Detection Threshold

#### Tier‑1 Recommendations

- [MathWorks Radar Toolbox: Detection and Tracking Statistics](https://www.mathworks.com/help/radar/detection-and-tracking-statistics.html)
  Purpose:
  - Engineering entry point for Pd / Pfa / threshold / Albersheim / detection statistics
  - Suitable for transforming the current `detection_prob` into an `SNR → Pd` approximation

- [MIT Lincoln Laboratory / Radar series public course materials](https://www.ll.mit.edu/)
  Purpose:
  - Radar detection theory, CFAR, tracking gates
  Note:
  - Specific documents are scattered, suitable as secondary evidence

#### Default Usable Engineering Values

- `Pfa = 1e‑6` can be default for airborne search radar
- For a single scan, the threshold SNR corresponding to `Pd50` can be initially set in the `10‑13 dB` range and tuned
- After pulse integration or multiple sweeps, the required threshold can be reduced by a few dB

These values are not exact for any specific model, but they are reasonable as a first‑version realism threshold for the current project.

### C.2 M‑of‑N Track Confirmation and Filtering

#### Tier‑1 Recommendations

- [MathWorks Multi‑Object Tracking and Tracker Documentation](https://www.mathworks.com/help/fusion/)
  Purpose:
  - Confirmation / deletion thresholds
  - Engineering use of alpha‑beta / Kalman

#### Directly Adoptable Default Values

- Airborne fire control radar: `2‑of‑3`
- AWACS / slow‑refresh long‑range surveillance: `3‑of‑4`
- Coast time: `4‑8 s`
- Track delete: `8‑15 s`

These values are common engineering approximations in the industry, more realistic than “confirm on first sight, delete all after 10 seconds”.

### C.3 IFF / Classification

#### Tier‑1 Recommendations

- [NATO / NAPMO Mode 5 IFF Overview](https://www.napma.nato.int/)
  Purpose:
  - Understand the essence of Mode 5: “encrypted challenge‑response + time sync + friendly confirmation”

- [MITRE public materials on IFF / cooperative identification](https://www.mitre.org/)
  Purpose:
  - Engineering explanation of why you cannot directly read the alliance side

#### Simplified Reference for Current Project

No need to chase Mode 5 protocol details. First abstract to:

- Whether the platform has challenge‑response capability
- Interrogation cycle
- Probability of friendly reply
- Probability of missed reply due to interference/out‑of‑sync

Starting parameters can be:

- Normal friendly reply probability: `0.95~0.995`
- Reply probability under interference/time sync loss: `0.6~0.9`
- Non‑friendly / no transponder: `0`

### C.4 Environmental Effects

#### Tier‑1 Recommendations

- [ITU‑R P.838](https://www.itu.int/rec/R-REC-P.838)
  Purpose:
  - Rain attenuation specific attenuation `gamma_R = k R^alpha`
  - Provides a standard source for radar weather attenuation

- [ITU‑R P.840](https://www.itu.int/rec/R-REC-P.840)
  Purpose:
  - Cloud/fog attenuation
  - Suitable for path loss approximations for Visual / IR / microwave

- [FAA / NOAA / UCAR public materials on radar horizon and beam propagation](https://www.faa.gov/), [UCAR MetEd](https://www.meted.ucar.edu/)
  Purpose:
  - Support standard approximations like `3.57 * (sqrt(h1)+sqrt(h2))`
  - Support the reasonableness of the 4/3 Earth radius approximation

#### Approximate Ranges Directly Usable in This Project

- Airborne/shipboard X‑band moderate rain attenuation:
  - Light rain: `0.02~0.08 dB/km`
  - Moderate rain: `0.1~0.3 dB/km`
  - Heavy rain: `0.4~1.0 dB/km`

- Cloud/fog for radar:
  - Usually weaker than rain; can be ignored or set to a very small term initially

- Cloud/fog for IR/Visual:
  - Should be significantly stronger than for radar; can reduce `snr_db` proportionally along the path

### C.5 Aircraft / Sensor Parameter Sources

#### Tier‑1 Recommendations

- Public manufacturer data, military trade brochures, congressional/audit reports, encyclopedic military‑industry sources

#### Tier‑2 Recommendations

- [Cmano‑DB](https://cmano-db.com/)
  Purpose:
  - Can serve as an unofficial but relatively systematic reference database
  - Suitable for initial magnitude calibration of APG‑68, Irbis‑E, AWACS radar, IRST

Usage suggestion:

- Do not copy a single point value directly
- Cross‑check with at least one other public source or common‑sense range
- Use it to decide order‑of‑magnitude (e.g., “80 km class / 120 km class / 400 km class”), not to claim absolute truth

#### Items Most Needing Calibration in the Current Project

- [an_apg_68.json](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json)
- [irbis_e.json](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json)
- [e3_sentry.json](../../../../examples/config/database/aircraft/units/e3_sentry.json)

The highest priority for these files is not the “absolute maximum detection range”, but:

- Change radar `range_power=2.0`
- Set `type` explicitly to `Radar`
- Add reference `reference_snr_db / reference_range_m / reference_rcs_m2`
- Add `confirm_hits_m / confirm_window_n`

---

## D. Recommended Priorities

### D.1 P0: Immediate Action, Otherwise Subsequent Air‑Combat Conclusions Will Remain Distorted

#### 1. Stop Data‑Link Directly Writing to Receiver’s `ContactList`

Location:

- [data_link_system.h](../../../../src/systems/systems/data_link_system.h)

Reason:

- Currently treats shared situational awareness as local detection
- Directly pollutes launch conditions, tactical picture, agent observations

#### 2. Introduce `Tentative/Confirmed` Track Status and `2‑of‑3` Confirmation

Location:

- [track_management.h](../../../../src/components/systems/track_management.h)
- [track_manager_system.h](../../../../src/systems/systems/track_manager_system.h)

Reason:

- This is the minimum threshold to go from “flickering contacts” to “usable tactical situation”

#### 3. Change Radar Detection Probability from Empirical Multiplier to `SNR → Pd` Approximation

Location:

- [sensor.h](../../../../src/components/systems/sensor.h)
- [unit_definition_loader.cpp](../../../../src/content/unit_definition_loader.cpp)
- [default_sensor_model.cpp](../../../../src/models/systems/default_sensor_model.cpp)

Reason:

- Without solving this, all subsequent effects of range, aspect, weather, and jamming will remain unreal

#### 4. Fix `range_power` in Radar Database

Location:

- [examples/config/database/aircraft/modules/sensors/an_apg_68.json](../../../../examples/config/database/aircraft/modules/sensors/an_apg_68.json)
- [examples/config/database/aircraft/modules/sensors/irbis_e.json](../../../../examples/config/database/aircraft/modules/sensors/irbis_e.json)
- [examples/config/database/aircraft/units/e3_sentry.json](../../../../examples/config/database/aircraft/units/e3_sentry.json)

Reason:

- This is one of the most obvious structural parameter errors currently

### D.2 P1: Should Follow Immediately, Significantly Improves Air‑Combat Credibility

#### 1. Add `alpha‑beta` Position/Velocity Filter for `SystemTrack`

Reason:

- Without velocity estimation, mid‑course guidance, interception, and situational judgment are all unreliable

#### 2. Introduce Simplified IFF / Identity State

Reason:

- Continuing to directly read `Alliance.side` means problems like blue‑on‑blue, no‑reply, and shared identification will never appear

#### 3. Connect Environmental Attenuation and LOS Sampling Obstruction

Reason:

- This is the lowest‑cost entry point to make “low‑altitude sea‑skimming / valley obstruction / bad weather” genuinely produce tactical differences

### D.3 P2: Push After P0/P1 Are Stable

#### 1. RCS Three‑Aspect Interpolation + Small Fluctuations

#### 2. Data‑Link Reporting Responsibility / Reporting Quality Threshold

#### 3. Simplified Clutter / Look‑Down Penalty

#### 4. Refinement of RWR and Radar Mode Relationship

### D.4 P3: Defer Unless Explicitly Entering Electronic‑Warfare / High‑Fidelity Identification Phase

#### 1. DRFM Deception Jamming

#### 2. Micro‑Doppler / NCTR

#### 3. Full Kalman / JPDA / MHT

#### 4. Full Link‑16 Time‑Slot and J‑Series Message Simulation

---

## Conclusion

The most critical realism task for Direction 2 at present is not “adding more sensor types” but removing the five pseudo‑truth points in the existing chain:

1. `detection_prob` multiplied directly
2. First hit immediately confirmed
3. Tracks have no filter and no velocity
4. Data‑link disguises shared situation as local detection
5. Classification directly reads `Alliance.side`

If these five points are not addressed first, even if air‑combat training can run, it is more likely that operators will adapt to current abstract loopholes rather than learn more realistic sensor and situational‑awareness constraints.

The most recommended order of advancement is:

1. `SNR/Pd + M‑of‑N + DataLink no longer writes ContactList`
2. `alpha‑beta filter + track quality + confirmed‑only tactical use`
3. `simplified IFF + environment penalties`
4. `RCS/interference/clutter` further refinement
