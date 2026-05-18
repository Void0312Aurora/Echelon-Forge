<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/sensor_situation/sensor_situation_realism_analysis_20260516.zh.md. Review before treating this file as authoritative. -->

# Sensor and Situational Awareness Reality Analysis

Status: `2026-05-16` Frozen analysis version.

Related files:

- [Sensor Component Definition](../../../../src/components/systems/sensor.h)
- [EW Component Definition](../../../../src/components/systems/ew.h)
- [DataLink Component Definition](../../../../src/components/systems/data_link.h)
- [TrackManagement Component Definition](../../../../src/components/systems/track_management.h)
- [ISensorModel Interface](../../../../src/core/interfaces/sensor_model.h)
- [DefaultSensorModel (Sensor Scan)](../../../../src/models/systems/default_sensor_model.cpp)
- [SensorSystem (Scan Scheduling and Track Memory)](../../../../src/systems/systems/sensor_system.h)
- [DataLinkSystem (Data Link Fusion and Messages)](../../../../src/systems/systems/data_link_system.h)
- [TrackManagerSystem (Track Database)](../../../../src/systems/systems/track_manager_system.h)
- [EWSystem (Electronic Warfare)](../../../../src/systems/systems/ew_system.h)
- [IEnvironmentModel Interface](../../../../src/core/interfaces/environment_model.h)
- [DefaultEnvironmentModel (Atmosphere/LOS/Weather)](../../../../src/models/environment/default_environment_model.cpp)
- [Sensor and Situational Awareness Roadmap](../../../forward/sensor_situation.md)
- [Flight Dynamics Reality Analysis (Related)](../flight/flight_dynamics_realism_analysis_20260516.zh.md)

Document positioning:

- This document only records the known deficiencies of the current sensor, data link, track management, and electronic warfare pipeline, along with their corresponding real physical/engineering conditions.
- It does not cover acceptable simplifications, does not provide prioritization, and does not provide a work plan.

## Postscript: `2026-05-17` Freeze Mark

Caliber markers:

- `Unresolved`: The original point remains essentially valid.
- `Partially resolved`: There is already a partial implementation or shared contract closure, but the main distortion persists.
- `Minimally closed`: A minimal closed loop already exists; it is no longer appropriate to describe it as "completely missing".
- `Resolved`: The old discussion on this item is no longer suitable as a description of the current state.

This postscript is only used to indicate whether these points today should still be directly considered as current issues.

| Item | Current Marker | Description |
|------|----------------|-------------|
| `2.1` Detection Probability Model | `Partially resolved` | `Tentative/Confirmed` and minimal confirmation semantics exist, but `SNR→Pd`, correlated noise, and more realistic `M-of-N` are not yet complete |
| `2.2` RCS Model | `Unresolved` | Aspect angle, frequency, polarization, and glint still do not form a current mainline closure |
| `2.3` Doppler Processing | `Unresolved` | `PRF / waveform / micro-Doppler` has not yet entered runtime contracts |
| `2.4` Jamming and Electronic Warfare | `Unresolved` | Currently still no `DRFM / cross-eye / more realistic decoy kinematics` closure |
| `2.5` Tracking and Track Management | `Partially resolved` | `track/report` semantics have replaced raw contact replication, but `velocity / quality / full lifecycle` still needs continued closure |
| `2.6` Data Link | `Partially resolved` | Switched to `track/report + QoS budget`, but still not a full `Link 16 / NPG / relay` model |
| `2.7` Track Classification (IFF/Identification) | `Unresolved` | Minimal `IFF` state machine not yet closed; the old "god's-eye-view classification" problem still essentially holds |
| `2.8` Sensor Fusion | `Partially resolved` | `local + datalink -> fused` already has a minimal contract, but multi-source weighted fusion and full deduplication are not yet complete |
| `2.9` Environmental Effects on Sensors | `Partially resolved` | Maritime `LOS / sea-state / ducting` already has minimal access, but weather, clutter, and complete refraction are still missing |
| `2.10` Structural Issues in Sensor Parameters | `Unresolved` | The `flat struct` and type-specific parameter system have not yet been truly separated |

---

## I. Current System Pipeline Overview

The current sensor and situational awareness pipeline is arranged in ECS registration order:

```
SensorSystem         → Scan scheduling (scan_period gating), track memory aging
  └ DefaultSensorModel.scan()  → Actual detection (FOV/range gating, probability determination, noise, RWR update)

DataLinkSystem       → Share contacts among same-network members, transmit tactical messages
  └ Receiver automatically fuses unknown targets into ContactList

TrackManagerSystem   → Build SystemTrack database from ContactList + CommQueue
  └ Track classification (Friend/Hostile/Neutral), source mark (Radar/Data Link), position estimation, aging, and cleanup

EWSystem             → Chaff/flare deployment + lifetime management

ClearCommInbox       → Message TTL cleanup (0.5s retention)
```

The observation side (visible to RL Agent) obtains situational awareness through `InstrumentState` + `ContactList` + `TrackDatabase` + `RWR`.

---

## II. Known Distortion Points

### 2.1 Detection Probability Model

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **No SNR threshold** | `default_sensor_model.cpp:205` directly synthesizes probability without SNR→Pd mapping | Real radar detection probability follows the Marcum Q function or Albersheim approximation: `Pd = f(SNR, Pfa)`. The detection threshold is determined by CFAR (typical Pfa=10⁻⁶), not directly specified by `detection_prob`. At long range and high noise, there is a physical steep drop where "signal is buried in noise"; the current model cannot express this |
| **Signal strength does not participate in detection probability** | `signal_strength` calculation (lines 244-279) is only used for observation output, not fed back to `detection_prob` | The radar equation for RCS/R⁴ is already used to calculate signal strength, but the `range_factor` for detection probability uses an empirical formula `1 - (R/Rmax)^n` rather than a physical detection model based on signal_strength/SNR. There is conceptual duplication between the two paths |
| **Detection probability is a simple product of factors** | All factors multiplied independently | In reality, range attenuation and RCS fluctuations (Swerling models) are correlated—at long range, target scintillation introduces additional uncertainty. The independence assumption overestimates detection consistency for weak targets at long range |
| **No scan-to-scan integration (M-of-N)** | Independent determination per frame | Real radar TWS mode typically requires 2 detections out of 3 scans (2-of-3 logic) to establish a track. In the current model, a single "dice roll success" immediately produces a Detection, causing targets to "flicker" at the detection boundary—present in one frame, absent in the next. Moreover, a single detection could be a false alarm and should not be used to establish a track |
| **No target RCS fluctuations** | RCS takes the fixed value of `RCSProfile.frontal_rcs` | Real RCS varies dramatically with aspect angle (10-20 dB magnitude), with random fluctuations due to maneuvers. Especially on low-observable (LO) platforms, RCS aspect sensitivity is exponential. Real radar detection requires Swerling 0-IV target fluctuation models |
| **`aspect_influence` is a cosine model symmetric for turn direction and head-on** | `aspect_factor = 0.5+0.5*cos(aspect)` | Real airborne radar typically has longer detection range for head-on targets than tail-on targets (head-on Doppler advantage), but side (beam aspect) detection is usually worst (Doppler falls into main lobe clutter). The current model has cos(0)=1 (head-on/tail-on optimal), cos(90)=0.5 (side worst), confusing the Doppler effect with the RCS pattern. In reality, detection probability at beam aspect should be significantly lower than tail-on |
| **No cumulative detection probability (P_cum)** | Each scan independent | On the tens-of-seconds timescale of RL training, the cumulative detection probability `P_cum = 1 - Π(1-P_single)^N` should approach 1 with continuous scanning. The current model lacks this guarantee, potentially resulting in the statistical anomaly of "continuous scanning for 30 seconds without detecting a target within close visual range" |

### 2.2 RCS Model

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **RCS only takes frontal_rcs** | `default_sensor_model.cpp:240` `rcs = rcs_prof->frontal_rcs` | `RCSProfile` defines three values (frontal/side/rear), but only frontal is used in practice. A `TODO` comment confirms this simplification. Real target RCS can differ by 10-20 dB across aspect angles—side detection range may be only half of head-on |
| **No polarization effects** | Radar equation does not consider polarization | Real RCS for horizontal and vertical polarization on the same target can differ by 3-6 dB |
| **No frequency dependence** | RCS is a single value | RCS is a function of frequency—the RCS of the same target at X-band (10 GHz) vs. S-band (3 GHz) can differ by an order of magnitude (resonance region vs. optical region) |
| **No multiple scattering centers/scintillation** | Single RCS value | Real complex targets (e.g., fighter aircraft) have dozens of scattering centers. Their interference during relative motion produces speckle, causing rapid RCS fluctuations in the ±5-10 dB range. This is crucial for angular tracking errors (glint) in guidance radars |

### 2.3 Doppler Processing

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Doppler notch as hard threshold** | `default_sensor_model.cpp:200` `abs(v_closing) < notch → 0.1` | Real pulsed Doppler radars have more complex blind zone structures. The zero-Doppler notch (main lobe clutter suppression) is the widest, but side lobe clutter and folded clutter from high PRF lines also produce additional blind zones. Moreover, real radars do not give a "probability × 0.1" for targets in the notch—they are completely undetectable |
| **No target Doppler spectrum spreading** | Only rigid body closure velocity used | Real aircraft engine fan/compressor blades (JEM, Jet Engine Modulation), rotors (helicopters), and propellers produce characteristic micro-Doppler spreading, a key feature for Non-Cooperative Target Recognition (NCTR) |
| **No PRF/waveform switching** | No concept | Real radars switch between low/medium/high PRF depending on target range/velocity ambiguities. Medium PRF has best performance for head-on targets but suffers range ambiguity for tail-on targets. Without PRF switching, both range and velocity ambiguities cannot be resolved simultaneously |

### 2.4 Jamming and Electronic Warfare

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Only noise barrage jamming** | `default_sensor_model.cpp:254` `NoiseBarrage` or `NoiseSpot` | Deception jamming (DRFM) is missing—Range Gate Pull-Off (RGPO), Velocity Gate Pull-Off (VGPO), and angle deception (inverse monopulse, cross-polarization) are the most common jamming techniques in air combat. The `DeceptionDRFM` enumeration is defined but not implemented |
| **Jamming determination is binary** | Beyond burn-through distance → completely invisible, otherwise → completely normal | Real burn-through is a non-binary transition—as distance decreases, the signal-to-jamming ratio (S/J) gradually improves until detection is possible, not instantaneously from 0 to 1 |
| **No angle deception/pull-off** | Not present | DRFM jamming can generate false angular tracking errors—directly affecting miss distance in proportional navigation. This is one of the most core techniques in air combat electronic countermeasures |
| **No cross-eye jamming** | Not present | The most efficient angle deception technique against angle-tracking radars (monopulse radars), capable of inducing systematic bias in missile angle tracking |
| **No chaff cloud evolution** | `EWSystem` deploys static chaff entities (RCS=50, duration 20 seconds) | Real chaff clouds have a blooming time (0.5-2s to achieve full RCS), drift with the wind, and RCS decreases over time. Moreover, the interference mechanism of chaff against radar is "generating a large number of false echoes" rather than "a single decoupled entity with RCS=50"—the chaff dipole cloud appears as an extended clutter region on radar displays |
| **Flare model extremely simple** | `EWSystem` deploys entities (no RCS, but with `Lifetime`, IR sensor signal=500/R²) | Real flares have a ramp-up time (0.1-0.5s to peak IR output), a cooling curve (significant decay after 2-5s), and must separate from the aircraft's line of sight to effectively decoy. The current model lacks decoy kinematics and the aircraft-decoy-seeker triangular geometry judgment—precisely the core logic of IRCCM (Infrared Countermeasure Rejection) |

### 2.5 Tracking and Track Management

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **No tracking filter** | `TrackManager` directly overwrites track position with current contact data | Real track management uses α-β or Kalman filters to smooth and predict measurements from consecutive scans. Lacking a filter means: (a) track position equals the most recent detection measurement (including noise), (b) track position cannot be predicted between scans, (c) no track uncertainty (covariance matrix) information. This renders track data unusable for missile mid-course guidance and fire control solutions |
| **Track ID = entity_id** | `track_manager_system.h:135` `track.entity_id == contact.target_id` | Real systems must assign track numbers themselves. entity_id creates a one-to-one mapping between track and entity, bypassing all track correlation problems—sensor errors may cause multiple tracks for the same target, or two targets merged into one track. This is the most difficult engineering problem in multi-target tracking |
| **Track confidence is fixed** | Radar track confidence=0.5, data link track confidence=0.8 | Real track confidence should reflect: number/quality of detections (track quality), most recent update time (staleness), sensor type fusion, and data link source reliability. The current fixed values do not evolve over time |
| **No track correlation and deduplication** | `TrackManager` matches by entity_id rather than position/velocity gates | Bypasses the most difficult association problems such as Multiple Hypothesis Tracking (MHT) or Joint Probabilistic Data Association (JPDA) |
| **Velocity estimation missing** | `SystemTrack` has `vx, vy, vz` fields but never assigned | Track velocity components are always zero. Any downstream decision dependent on target velocity vector (e.g., collision course determination, intercept vector calculation) is unusable |
| **No track initiation/confirmation logic** | Track established on first detection | Real radar requires 2-3 consecutive detections of continuous scan (M-of-N logic) to establish a "confirmed track". A single detection may be a false alarm and should be marked as a "tentative track" |

### 2.6 Data Link

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Raw contacts are shared instead of tracks** | `DataLinkSystem` directly copies the sender's `ContactList` to the receiver | Real data links (Link 16) share "tracks" containing track number, filtered position/velocity, confidence, and identification information. Raw radar plots are not transmitted over data links—the plot data volume is too large and contains noise, making it impossible to transmit in limited time slots |
| **No message format/protocol** | `Detection` struct exchanged directly | Real Link 16 has strict J-series message formats (J3.x surveillance tracks, J12.x mission management, etc.), slot size limits, and data compression (position quantization precision depends on data link precision level) |
| **No reporting responsibility** | All nodes share all contacts with all same-network nodes | In real networks, reporting responsibility for the same target is assigned to the "highest quality" node (to avoid redundant transmission). Multiple nodes should not report the same target repeatedly—this is a core function of Link 16 network management |
| **No network capacity/slot limitation** | No bandwidth constraints | A single time slot in real Link 16 can only carry a limited number of track reports. In dense target environments (e.g., large-scale air combat), there is priority queuing for track reports |
| **Network assignment is a side-level approximation** | `network_id = side` | In reality, a carrier battle group may have multiple independent networks (different NPGs), and cross-service/international coordination requires gateway forwarding |
| **Radio horizon uses simplified formula** | `3.57*(√h1+√h2)` valid for standard atmosphere k=4/3 | Under real atmospheric refraction conditions (non-standard refraction—super-refraction, sub-refraction), the horizon distance can vary by ±15% |

### 2.7 Track Classification (IFF/Identification)

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Classification directly queries entity's Alliance** | `track_manager_system.h:13-24` `classify_track_from_alliance()` directly reads the target's `Alliance.side` | This is "god's-eye-view" classification—real systems must infer target identity through IFF interrogation/response (Mode 4/5), Non-Cooperative Target Recognition (NCTR—based on JEM/RCS features/kinematics), and Rules of Engagement. IFF responses may be missing (fault/jamming/NATO Mode 5 encryption mismatch), unreliable (Mode 4 can be spoofed), and NCTR requires time and sensor accumulation |
| **No ambiguous identification states** | Only Friend/Hostile/Neutral/Unknown | Real ID matrix includes more states: Assumed Friend (associated based on flight plan but not confirmed), Suspect (abnormal behavior but not confirmed hostile), Pending (IFF interrogation sent but no response received). These ambiguous states directly affect Rules of Engagement and weapon release authorization |
| **No Mode 4/5 encryption and time synchronization** | Not present | Modern IFF Mode 5 requires precise GPS time-synchronized encrypted interrogation/response. If the transponder's time drift exceeds tolerance, even legitimate friendly units may be classified as Unknown—a key source of blue-on-blue risk in real operations |

### 2.8 Sensor Fusion

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **No multi-sensor fusion** | Each entity's `Sensor` is a single sensor | A real fighter typically carries: radar (forward-looking) + IRST (forward-looking passive IR) + RWR (omnidirectional passive) + MAWS (Missile Approach Warning) + DAS (Distributed Aperture System, e.g., F-35's EODAS). These sensor sources should be fused based on their respective strengths and weaknesses, not solely reliant on a single sensor |
| **TrackDatabase overwrites by entity_id rather than fusing** | Radar source directly overwrites data link source (or vice versa, depending on arrival order) | Proper approach: When two sensor sources provide information on the same target, they should be weighted-fused according to their respective covariances (track-to-track fusion), rather than one overwriting the other |
| **TrackSource only marks the primary source** | Simple enumeration Radar/DataLink/RWR/Fused | The `Fused` enumeration is defined but never used—there is no code path that marks multi-source tracks as Fused |
| **Contacts in ContactList enter/exit TrackDatabase without association** | Sensor scan → ContactList → TrackManager matches by entity_id | Missing the plot-to-track association stage—the classic problem in multi-target tracking. The current approach completely bypasses this by relying on entity_id's "god's-eye view" |

### 2.9 Environmental Effects on Sensors

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Weather attenuation MVP is 0** | `default_environment_model.cpp:153` `get_weather_attenuation() → return 0.0` | Attenuation from precipitation (rain/snow/hail), fog, and clouds on radar/infrared/visual is completely absent. Real Ka-band radar in moderate rain (4mm/hr) can have two-way attenuation up to 0.4dB/km—20dB loss over 50km, equivalent to halving detection range |
| **LOS check only checks if endpoints are underground** | `check_line_of_sight()` does not check intermediate points | Earth curvature occlusion is not modeled (the radar horizon uses a simplified formula rather than real ray tracing). Obstructions from mountains/buildings and other tall obstacles are not considered |
| **No atmospheric ducting effects** | Not modeled | Under specific temperature/humidity gradients, radar waves can be trapped by atmospheric ducts for over-the-horizon propagation (hundreds of kilometers), producing anomalous detections. Particularly important for surface radars—evaporation ducts can create over-the-horizon detection close to the sea surface |
| **No sea clutter/ground clutter** | Not modeled | Downward-looking/low-altitude target detection is limited by strong ground/sea clutter. For shipborne radars against sea-skimming anti-ship missiles, sea clutter is the dominant limiting factor. Pulsed Doppler radars separate clutter from moving targets using Doppler filtering, but low radial velocity targets (side-aspect flight) fall into the clutter region and are undetectable |
| **No solar flare effects on IR** | Only simple sun direction detection for visual/IR | Real IR seekers may lose lock entirely when the sun enters the FOV (the sun is an extremely strong background radiation source in the IR band). The current `sun_factor=0.1` only reduces probability rather than completely blocking the seeker, severely underestimating the destructive effect of solar interference |

### 2.10 Structural Issues in Sensor Parameters

| Distortion | Code Location | Reality |
|------------|---------------|---------|
| **Sensor parameters are flat struct** | `sensor.h:13-26` All sensor types use the same parameter set | Different sensor types require different parameterizations. IRST does not have "Doppler notch" but has "NEdT (Noise Equivalent Temperature Difference)" and "IFOV (Instantaneous Field of View)". Radar has "peak power", "antenna gain", "pulse width", "PRF" rather than a simple "detection_prob". The current flat struct loses the physical parameters specific to sensor types |
| **range_power can be set but requires manual configuration** | `range_power` field exists but is manually filled in the scene JSON | Radar should be 4.0 (R⁴ law), IR and visual should be 2.0 (R² law). This value is not automatically derived from SensorType, posing a risk of misconfiguration—setting radar's range_power to 2.0 would severely overestimate long-range detection capability |
| **No antenna gain and peak power in radar range equation** | Detection probability not based on SNR | Real radar maximum detection range is determined by: `R_max⁴ = (Pt·G²·λ²·σ) / ((4π)³·kT·B·F·(S/N)min)`. Each parameter (peak power Pt, antenna gain G, wavelength λ, noise bandwidth B, noise figure F, minimum detectable SNR) should be configurable to differentiate the performance of different radar models |

---

## III. Statements That Should Not Be Used Currently

To avoid future semantic drift, the following statements should be explicitly avoided:

1. The current detection model should not be called "radar simulation"—it is
   **"geometric gating + independent probability detection + Gaussian noise"**, without SNR threshold, waveform, or PRF.
2. The current tracking system should not be called "multi-target tracker"—it is
   **"entity_id direct association contact recorder"**, without tracking filter, track correlation, or M-of-N initiation.
3. The current data link should not be called "Link 16 simulation"—it is
   **"same-side same-network peer-to-peer ContactList replication"**, without message format, R2, or time slots.
4. The current IFF/classification should not be called "target identification"—it is
   **"direct query of entity Alliance.side"**, without IFF question/answer, NCTR, or ambiguous states.
5. The current electronic warfare should not be called "ECM simulation"—it is
   **"burn-through distance binary determination + static chaff/flare deployment"**, without DRFM, angle deception, or decoy kinematics.

A more accurate description is:

- **RL training-level sensor abstraction**
- **Geometric gating + probability detection + Gaussian noise baseline**
- **Suitable for "detect-track-share situational awareness" training, not suitable for electronic warfare or sensor countermeasures**

This conclusion is frozen until the next explicit reopening of sensor advancement.
