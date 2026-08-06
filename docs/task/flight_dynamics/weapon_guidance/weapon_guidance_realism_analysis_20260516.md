<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/weapon_guidance/weapon_guidance_realism_analysis_20260516.zh.md. Review before treating this file as authoritative. -->

# Weapon System and Guidance Loop Realism Analysis

Status: `2026-05-16` Frozen Analysis Version.

Related Files:

- [Missile Component Definition](../../../../src/components/combat/weapon.h)
- [Ammo / WeaponCooldown / Munition Components](../../../../src/components/combat/weapon.h)
- [HitboxConfig / SystemHealth Components](../../../../src/components/combat/damage.h)
- [Health / Score Components](../../../../src/components/combat/health.h)
- [IGuidanceModel Interface](../../../../src/core/interfaces/guidance_model.h)
- [IEffectsModel Interface](../../../../src/core/interfaces/effects_model.h)
- [DefaultGuidanceModel (PN Guidance)](../../../../src/models/weapons/default_guidance_model.cpp)
- [DefaultEffectsModel (Hit Effects)](../../../../src/models/weapons/default_effects_model.cpp)
- [DamageSystem (Proximity Fuze)](../../../../src/systems/combat/damage_system.h)
- [SimulationKernel Weapon API (Firing Logic)](../../../../src/core/engine/simulation_kernel_weapon_api.cpp)
- [Weapons and Engagement Rules Roadmap](../../../systems/weapons/work/issues/weapons_engagement.md)
- [Sensor and Situational Awareness Realism Analysis (Related)](../sensor_situation/sensor_situation_realism_analysis_20260516.zh.md)
- [Flight Dynamics Realism Analysis (Related)](../flight/flight_dynamics_realism_analysis_20260516.zh.md)

Document Positioning:

- This document only records known deficiencies and their corresponding real physical/engineering situations.
- Does not cover acceptable simplifications, does not provide prioritization, does not give a work plan.

## Postscript: `2026-05-18` Closure Markers

Marker Caliber:

- `Unresolved`: The original argument is still basically valid.
- `Partially Resolved`: Partial implementation or runtime gating exists, but the core realism gap remains.
- `Minimal Closure Achieved`: It is no longer appropriate to describe as "completely missing"; a minimal runnable closed loop exists.
- `Resolved`: That old argument is no longer suitable as a description of the current state.

This postscript is solely for answering whether these arguments can still be directly treated as current issues today.

| Item | Current Marker | Description |
|------|----------|------|
| Section 1: Current Weapon Pipeline | `Partially Resolved` | Should be re-read as `seeker-only guidance + minimal 3DoF/PN-autopilot surrogate + shared missile tuning`, no longer the old single-layer chain |
| `2.1` Velocity vector rotation replaces acceleration command | `Minimal Closure Achieved` | Minimal surrogate with bounded lateral acceleration and response lag exists, but still not full body dynamics |
| `2.2` No missile autopilot stage | `Minimal Closure Achieved` | Minimal inner loop semantics like `autopilot_tau` are wired in, but still not a complete autopilot/body dynamics |
| `2.3` LOS rate calculation uses real target position | `Resolved` | Guidance now consumes detection/track state and filtered track memory rather than directly depending on raw target truth position/velocity |
| `2.4` Decoy logic is a rough seduction approximation | `Unresolved` | Still lacks centroid, kinematic discrimination, and more realistic decoy timing |
| `2.5` Navigation gain is a fixed constant | `Partially Resolved` | `nav_gain` is now in shared tuning, but still not real variable gain guidance |
| `2.6` Sign inconsistencies in coordinate systems | `Partially Resolved` | Current sign caliber has a gating line, but this is more of a structural/validation debt rather than a main behavior red flag |
| `3.1` Constant speed — no thrust/drag/mass change | `Minimal Closure Achieved` | `boost/sustain/drag/mass depletion` are now in runtime |
| `3.2` Meaning of max speed is distorted | `Partially Resolved` | Speed is no longer constant, but still lacks a more credible envelope-level interpretation |
| `3.3` Aerodynamic drag completely missing | `Minimal Closure Achieved` | Multiple drag terms are now in runtime and gating tests |
| `4.1` Seeker sensor is a full copy of radar/IR | `Partially Resolved` | Closer to a minimal `seeker-only` implementation, but seeker typing is not deepened |
| `4.2` Lock range and FOV do not reflect real constraints | `Minimal Closure Achieved` | `sensor_max_range / seeker fields / activation range` are wired in, but still not a real seeker constraint model |
| `4.3` Lack of Lock-On Before Launch (LOBL) requirement | `Resolved` | `lobl_required` is now in the formal fire denial gating |
| `4.4` No target discrimination/rejection capability | `Unresolved` | Still lacks seeker discrimination / reject contract |
| `5.1` Fuze logic cannot distinguish miss direction | `Unresolved` | Terminal geometry and directional fuze still not closed |
| `5.2` Hit probability model quality-evasion coupling is unreasonable | `Unresolved` | Hit probability contract still not refactored |
| `5.3` Fuze delay and fragment propagation time missing | `Unresolved` | Fuze timing still not in current mainline |
| `6.1` HP deduction and geometric damage dual track inconsistency | `Unresolved` | `HP` path and subsystem path still not unified |
| `6.2` Part damage is binary instant kill | `Minimal Closure Achieved` | `PlatformDamageState` and post-hit degradation now provide a minimal continuous damage path, even though richer subsystem fidelity is still missing |
| `6.3` Coordinate transformation has uncertainty | `Partially Resolved` | More like validation debt, no evidence it is a main behavior red flag |
| `6.4` No warhead type differentiation | `Unresolved` | Warhead family still not in runtime |
| `7.1` No launch envelope check | `Minimal Closure Achieved` | `min range / off-boresight / LOBL` form a minimal fire denial contract |
| `7.2` No rapid fire/multi-target launch limits | `Partially Resolved` | `ammo/cooldown` is in place, but more realistic salvo/multi-target constraints are missing |
| `8.1` No midcourse datalink | `Minimal Closure Achieved` | `midcourse_datalink_supported / seeker_activation_range_m` are wired |
| `8.2` Launch altitude/speed has zero effect on `Pk` | `Resolved` | Launch altitude/speed no longer have zero effect on missile behavior because atmosphere, drag, thrust, and mass depletion now change the flight profile, even though broader envelope/`Pk` realism remains incomplete |

---

## I. Processing Chain of the Current Weapon Pipeline

```
fire_weapon_from_pilot_action / fire_missile()
  → Launch condition check (ammo, cooldown, existing contact track)
  → Missile entity generation (inherits carrier velocity, fixed missile parameters)
  → Seeker Sensor registration (scan period 0.05s)

GuidanceSystem
  → DefaultGuidanceModel.update()
    → Delay / update period gating
    → Select strongest signal target from ContactList (decoy logic)
    → PN guidance calculation (LOS rate → velocity vector rotation)
    → Velocity normalized to max_speed (no energy change)

DamageSystem (ProximityFuze)
  → Closest distance tracking
  → Trigger fuze when distance starts increasing
  → fuse_distance gating
  → Hit probability (distance quality × maneuvering evasion)
  → on_proximity_hit()

DefaultEffectsModel
  → Generic HP deduction
  → Geometry hitbox determination → system-level damage (radar/engine/fuel)
  → Randomized degradation damage (fallback path)
```

---

## II. Deficiencies of Proportional Navigation (PN) Guidance Law

### 2.1 Velocity Vector Rotation Replaces Acceleration Command

```cpp
// default_guidance_model.cpp:242-271
// Perform Rodrigues rotation on velocity vector, then normalize to max_speed
double v_new_x = vm_x*cos_t + cross_x*sin_t + axis_x*dot*(1.0-cos_t);
velocity.vx = (v_new_x / vn_norm) * missile.max_speed;
velocity.vy = (v_new_y / vn_norm) * missile.max_speed;
velocity.vz = (v_new_z / vn_norm) * missile.max_speed;
```

Real PN guidance law outputs an **acceleration command** (perpendicular to the missile velocity vector), not a geometric rotation of the velocity vector. The missile achieves turns using aerodynamic control surfaces (or thrust vectoring) to produce normal acceleration. The consequences of the current implementation directly rotating the velocity vector are:

- The missile's turn is an **instantaneous geometric operation**, with no aerodynamic response delay, no load factor build-up time.
  A real missile takes 0.05-0.2 seconds from receiving an acceleration command to establishing steady-state load factor on the airframe (depending on airspeed and dynamic pressure).
- Rotating the velocity vector essentially changes the missile's flight path direction, but **does not come with a normal acceleration constraint**. The real missile's available load factor (in G) is determined by `n_max = q_bar × CL_max × S / (m × g)`, which decreases significantly at low dynamic pressure (high altitude/low speed).
  The current model's `turn_rate` limit is a constraint on angular rate, not load factor — these two quantities have a physical divergence at high altitude (same angular rate → needs high G at low altitude, low G at high altitude).
- The hard limit on `turn_rate` may allow physically impossible sharp turns at low speed, and may be overly restrictive at high speed (missile normally has higher available turn angular rate at high speed).

### 2.2 No Missile Autopilot Stage

The real guidance loop is:

```
Seeker measurement → Tracking filter (state estimation) → Guidance law (acceleration command)
  → Autopilot (fin/thrust vector command) → Body dynamics (load factor response)
  → IMU/accelerometer (feedback) → Back to guidance law
```

The current implementation lacks the entire autopilot and body dynamics stage. The output of the guidance law (LOS rate → velocity rotation) directly drives kinematics, without going through:

- **Fin loop**: Deflection rate limits of actuating mechanism (fin servo) (typical 200-300°/s) and deflection angle limits (typical ±25°)
- **Body transfer function**: Aerodynamic delay from fin deflection to body angular rate to normal acceleration.
  Typical tactical missile short period time constant is about 0.05-0.15 seconds
- **Acceleration/angular rate feedback**: The autopilot needs to use IMU angular rate and acceleration measurements to close the inner loop; otherwise, it cannot track the acceleration command of the guidance law.

### 2.3 LOS Rate Calculation Uses Real Target Position

```cpp
// default_guidance_model.cpp:118-139
const Transform* t_pos = world.entity(missile.target_id).get<Transform>();
const Velocity* t_vel = world.entity(missile.target_id).get<Velocity>();
// ...
double rx = t_pos ? (t_pos->x - transform.x) : /* fallback */;
double vt_x = t_vel ? t_vel->vx : 0.0;
```

Relative position and relative velocity are taken directly from the target's real `Transform` and `Velocity`, not estimated from seeker measurements. Code comments frankly admit this issue:

> "In a strict sense, we should use 'det->bearing' history to estimate rate.
>  For MVP High-Fidelity, using Truth for Guidance Law is acceptable."

In reality:

- The seeker only provides **noisy** azimuth, elevation, and range (active radar) or angle information (passive IR/semi-active radar)
- LOS angular rate must be estimated from a sequence of noisy angle measurements, typically using an α-β or Kalman filter
- Measurement noise propagates directly into LOS rate estimation noise, causing terminal miss distance to increase as range decreases (this is one of the most significant sources of terminal miss)
- Target maneuvering (weaving, sharp turns) introduces additional lag in LOS rate estimation; the current model completely bypasses this issue by using real positions

### 2.4 Decoy Logic (Strongest Signal Selection) Is a Rough Seduction Approximation

```cpp
// default_guidance_model.cpp:93-97
// Seduction Logic: Pick strongest signal
if (c.signal_strength > max_sig) {
    max_sig = c.signal_strength;
    best_det = &c;
}
```

The behavior of a real seeker when encountering decoys depends on:

- **Decoy kinematic separation**: The decoy must separate from the carrier's line of sight to be resolved by the seeker.
  Thermal decoys cannot provide sufficient angular separation within 0.1-0.3 seconds after dispensing
- **Seeker resolution**: When the angular distance between decoy and carrier is smaller than the seeker's instantaneous field of view (IFOV) or track gate, the seeker tracks the **energy centroid (centroid)** of both, not a single strongest signal. Centroid tracking causes the missile to fly toward some point between the target and decoy, rather than either one
- **Signal transient**: Thermal decoys have a rise time (0.1-0.5 seconds to peak) and decay (2-5 seconds), during which signal strength continuously changes. The current model uses instantaneous fixed signal strength
- **Kinematic discrimination**: A real seeker not only compares signal strength but also uses kinematic filters to determine if a contact could be a target following a ballistic (inertial) trajectory — thermal decoys decelerate rapidly due to their small mass, and their speed/acceleration patterns differ significantly from those of the carrier

### 2.5 Navigation Gain Is a Fixed Constant

```cpp
double nav_gain = missile.nav_gain > 0 ? missile.nav_gain : 3.0;
```

The effective navigation ratio (N') in real PN guidance is typically 3-5, but in practice:

- The effective navigation ratio `N' = N × Vc / Vm × cos(γ)`, where γ is the angle between the missile velocity vector and the LOS. When the missile is at a large off-boresight angle (initial launch phase or target sharp turn), the effective navigation ratio is significantly reduced
- The terminal guidance phase typically uses a higher N' (4-5) to reduce miss distance, while the midcourse guidance phase uses a lower N' (3) to conserve energy
- Some modern missiles use **variable gain guidance laws**: N' varies with time-to-go (t_go)

### 2.6 Sign Inconsistencies in Coordinate Systems

There are multiple coordinate transformations (NAV to math coordinate system) and sign inferences in the code, and comments reveal hesitant design thinking:

```cpp
// Lines 158-168: Multiple PN formula variants coexist in comments
// a_cmd = N * V_c * Omega (Scalar approximation) -> Direction?
// Vector form: accel = N * V_closing_scalar * (Omega x Unit(V_missile)) ?
// Actually usually applied perpendicular to LOS.
```

```cpp
// Lines 218-220
// Heuristic approach matching "Rate of Turn of Velocity = N * Rate of Turn of LOS"
// Turn Rate Vec = N * Omega_vec.
```

This indicates that the current PN implementation is a **mixture after multiple iterations**, not a single clear guidance law.
`omega × V_missile` produces acceleration (torque direction), which is then converted to a Rodrigues rotation of the velocity vector — but whether the result is correct depends on the consistency of the `omega` cross product direction and the Rodrigues rotation axis. There is no unit test or analytical solution to verify the equivalence of this transformation.

---

## III. Deficiencies of Missile Kinematics (Energy Model)

### 3.1 Constant Speed — No Thrust/Drag/Mass Change

```cpp
// default_guidance_model.cpp:268
double new_speed = missile.max_speed; // Assume sustains speed for now
velocity.vx = (v_new_x / vn_norm) * new_speed;
```

After each guidance update, the speed is normalized to `max_speed`. This means:

- **The missile never decelerates.** A real missile experiences:
  - Boost phase: accelerates to maximum speed within 2-5 seconds, motor burnout
  - Sustain phase: some missiles have a sustainer motor to maintain speed for 10-60 seconds
  - Coast phase: flies inertially after burnout, speed continuously decreases due to aerodynamic drag.
    Typical medium-range AAMs (e.g., AIM-120) can lose 30-50% of their speed after burnout at maximum range
- **The missile never consumes mass.** During the burn of a real solid rocket motor, propellant mass accounts for 30-50% of total launch mass. After burnout, mass is significantly reduced, and available load factor increases accordingly. Current `Mass` is fixed at 80kg
- **Same performance at high/low altitude.** At 40,000 ft in low-density air, aerodynamic control surface efficiency drops substantially (dynamic pressure ~1/4 of sea level), and the missile's available load factor is significantly reduced.
  Meanwhile, reduced drag prolongs the coast phase. The current model's `turn_rate` limit does not vary with altitude/dynamic pressure at all
- **Launch velocity inheritance mismatch.** Carrier velocity is correctly inherited as the missile's initial speed, but then immediately overwritten to `max_speed`. If the carrier launches at 0.8M, the missile is instantly accelerated to 1000 m/s (≈ 3M), effectively possessing unlimited rocket engine acceleration

### 3.2 Meaning of Max Speed Is Distorted

The current `max_speed = 1000 m/s` (≈ Mach 2.9 at sea level, ≈ Mach 3.3 at high altitude) changes role from "maximum achievable speed" to "constant cruise speed". The real missile's `max_speed` is the peak speed at motor burnout, with the following characteristics:

- Only achievable under specific altitude and launch conditions (high-speed carrier launch + high altitude, low drag)
- Duration is extremely short (starts decaying due to drag after 1-3 seconds)
- When launched at low altitude, due to high air density, peak speed is significantly lower than when launched at high altitude

### 3.3 Aerodynamic Drag Completely Missing

A missile as an object moving at high speed in air (Mach 2-4) should experience:

- **Zero-lift drag**: Form drag (friction + pressure) ∝ ρ × V² × S × Cd0.
  At Mach 3, aerodynamic heating raises surface temperature above 300°C, changing boundary layer characteristics
- **Induced drag**: When the missile turns at high G, significant induced drag (Cd_i ∝ Cl²) is generated due to high angle of attack, causing rapid speed loss. A missile pulling 30G can lose 10-20% of its speed within 1-2 seconds
- **Wave drag**: At supersonic speeds, nose shock waves and wing shock waves generate wave drag.
  Wave drag rises sharply near Mach 1.2, affecting acceleration and cruise performance

The absence of drag in the current model means the missile does not consume kinetic energy during high-G turns — this is physically equivalent to the missile having infinite thrust and zero drag.

---

## IV. Deficiencies of the Seeker/Lock Model

### 4.1 Seeker Sensor Is a Full Copy of a Radar/IR Sensor

```cpp
// simulation_kernel_weapon_api.cpp:185-189
.set<Sensor>({sensor_max_range, sensor_fov_deg, sensor_scan_period, -1.0,
              sensor_detection_prob, 2.0, sensor_bearing_noise,
              sensor_range_noise, sensor_track_memory, 0.2,
              20.0, // doppler_notch_width (m/s)
              static_cast<int>(sensor_max_range > 8000.0 ?
                  SensorType::Radar : SensorType::Infrared)})
```

The missile seeker is modeled as an independent `Sensor` component, identical to a copy of an airborne radar.

Differences in real missile seekers:

- **Semi-Active Radar Homing (SARH)**: The missile itself has no radar transmitter; it only receives the reflected signal of the target illuminated by the carrier's radar. The missile cannot independently search/acquire the target; it relies entirely on the carrier's STT (Single Target Track) illumination until impact. In the current model, the missile has its own independent radar
- **Active Radar Homing (ARH, e.g., AIM-120)**: The missile relies on carrier datalink updates during the midcourse phase (not its own radar), and only activates its own radar for terminal active guidance at close range (15-20 km from target). In the current model, the missile starts independent detection from the moment of launch
- **Infrared Homing (IR, e.g., AIM-9)**: Passively detects target thermal radiation, has no range measurement capability. Cannot directly obtain target range and range rate — LOS rate must be estimated from pure angle measurements, making PN guidance accuracy of passive IR missiles lower than that of active radar missiles. In the current model, the `ContactList` for IR missiles still contains range information (from an omniscient sensor scan)
- **Seeker scan pattern**: Real IR seekers use reticles or focal plane arrays (FPA), not "frame scanning" like radar. The current model uniformly uses a 0.05-second scan period, which is too fast for radar (mechanical scanning radar typically 0.5-2 seconds) and possibly too slow for IR (FPA frame rate can reach 100Hz+)

### 4.2 Lock Range and Seeker FOV Do Not Reflect Real Seeker Constraints

```cpp
double missile_seeker_fov = 180.0;
double missile_seeker_range = 30000.0;
```

- `seeker_fov_deg = 180` means the missile can lock a target **behind** it.
  A real missile seeker's field of view is typically within ±30° to ±60° range (AIM-9X using FPA has a high off-boresight capability around ±90°). 180° means the missile does not need to point toward the target to lock — physically, this would require the seeker to be mounted on a gimbal that can look backward
- `seeker_lock_range = 30000m` is the same as `sensor_max_range = 30000m`.
  A real active radar seeker's lock range is usually much smaller than its maximum detection range, because locking requires higher SNR (track mode) rather than just detection (search mode)

### 4.3 Lock Condition Lacks Lock-On Before Launch (LOBL) Requirement

```cpp
// simulation_kernel_weapon_api.cpp:79-94
const ContactList* contacts = attacker.get<ContactList>();
bool has_track = false;
for (const auto& c : contacts->contacts) {
    if (c.target_id != target_id) continue;
    has_track = true; break;
}
```

The launch condition only requires the target's presence in the carrier's `ContactList`, without considering:

- **Lock-On Before Launch (LOBL)**: Most IR missiles require the seeker to have acquired the target lock before launch (hearing the "growl" tone).
  The carrier sensor having a target contact ≠ the missile seeker can independently lock that target
- **Lock-On After Launch (LOAL)**: Some modern missiles (e.g., AIM-9X + JHMCS high off-boresight launch) support LOAL, where the missile is first launched toward a predicted intercept point and then acquires the target in flight. This requires midcourse guidance/datalink
- **Carrier radar illumination mode**: Semi-active radar missiles (e.g., AIM-7) require the carrier to be in STT (Single Target Track) mode for continuous illumination. Tracks from TWS (Track-While-Scan) mode cannot support SARH launch

### 4.4 No Target Discrimination/Rejection Capability

In the current model, the seeker unconditionally accepts signals in the `ContactList` that fall within its FOV.
Real seekers have countermeasure rejection capabilities:

- **Infrared Counter-Countermeasures (IRCCM)**: Based on dual-color discrimination, kinematic discrimination (decoy decelerates rapidly vs. carrier maintains speed), rise-time discrimination (decoy peaks in 0.1s vs. carrier sustained radiation)
- **Chaff rejection**: Based on Doppler discrimination (chaff rapidly decelerates to wind speed vs. carrier maintains speed), range gate pull-off (RGPO) detection (characteristic exponent of false range)
- **Velocity gate pull-off (VGPO) detection**: Detecting typical patterns of VGPO (velocity step change followed by constant velocity movement)

---

## V. Proximity Fuze and Hit Determination

### 5.1 Fuze Logic Cannot Distinguish Miss Direction

```cpp
// damage_system.h:66-75
if (dist < m[i].proximity_last_dist_m - epsilon) {
    m[i].proximity_engaged = true;    // Still approaching
    m[i].proximity_last_dist_m = dist;
    continue;
}
// Starting to move away → trigger fuze
```

The proximity fuze trigger condition is "distance starts increasing and minimum distance < fuse_distance".
This only depends on scalar distance, and does not distinguish between "passing above the target", "passing below the target", or "passing in front of the target".

Real proximity fuzes (e.g., laser proximity fuze or radio proximity fuze) have:

- **Directional kill warhead**: The explosion is not an isotropic sphere, but a narrow fragment cone (typically inclined 10-30° forward). The fuze needs to determine the target's direction and relative velocity to optimize detonation timing and direction
- **Range rate triggering**: Laser fuzes further optimize the detonation moment by measuring the target's range rate so that the fragment cone intersects the target

### 5.2 Hit Probability Model's Quality-Evasion Coupling Is Unreasonable

```cpp
// damage_system.h:83-92
double quality = std::clamp(1.0 - min_dist / fuse, 0.0, 1.0);
double evasion = std::clamp(std::abs(ac->turn_rate_cmd), 0.0, 1.0);
double base_hit = 0.35 + 0.65 * quality;
double hit_prob = std::clamp(base_hit * (1.0 - 0.3 * evasion), 0.05, 0.98);
```

- `evasion` uses `turn_rate_cmd` (normalized turn rate command) as an evasion indicator.  
  The actual evasion effect depends on the **increase in miss distance** generated by the target's maneuver, not the absolute value of the turn command.  
  A target performing small-amplitude, high-frequency jinking produces a much larger miss distance than large, smooth turns.
- The evasion effect and distance quality are **multiplied independently**, implying that evasion and proximity act independently – in reality they are strongly correlated: a target performing a large maneuver during the terminal phase of the missile simultaneously increases the minimum distance and constitutes evasion.
- The clamp range of `hit_prob` [0.05, 0.98] means that even if the minimum distance is zero (direct hit), there is only a 98% probability of scoring a hit, while a minimum distance at the edge of the fuse distance still gives a minimum hit probability of 5%. This statistical distribution has no physical justification in real ammunition.

### 5.3 Absence of Fuze Delay and Warhead Fragment Propagation Time

In reality, there is a time‑delay chain between fuze detection, detonation, and fragment arrival at the target:

- Fuze detection of the target → fuze processing delay (~1–5 μs for laser, ~50–200 μs for radio)
- Detonation signal → booster initiation → main charge detonation (~10–50 μs)
- Fragment acceleration to maximum velocity (~100–500 μs)
- Fragment flight to the target position (~1–5 ms depending on distance)

During this time, the missile flies at ~1000 m/s, so the relative position may shift by 1–5 meters. This means the fuze must **lead‑trigger** (提前起爆) based on the target's relative motion to predict the intercept moment. The current model triggers in the same frame when "the distance begins to increase" – this is a zero‑delay simplification, leading to a systematic miss‑distance bias.

---

## 6. Lethality Model

### 6.1 Inconsistency Between Generic HP Deduction and Geometric Damage Dual‑Track Model

```cpp
// default_effects_model.cpp:118-133
hp->current_hp -= missile.damage;
// ...
if (hp->current_hp <= 0) {
    target_entity.destruct();
    // ...
}
// 然后继续执行几何命中盒判定...
```

HP deduction is performed before the geometric hit‑box check. If HP deduction directly triggers `destruct`, the subsequent geometric hit‑box logic is completely skipped. This means there are **two inconsistent damage determination paths**: HP reaches zero → instant destruction (ignoring intermediate subsystem damage states), and hit‑box check → subsystem damage but the entity may survive.

In reality: there is no independent "HP" concept – damage is the result of physical interaction. The fragments/blast/continuous rod from the missile warhead cause local structural damage to the target, and the loss of function of each subsystem is the cumulative consequence of these local injuries, not an a priori "HP value".

### 6.2 Subsystem Damage Is a Binary "Instant Kill"

```cpp
// default_effects_model.cpp:157-159
sys_health->systems[system] -= 1.0; // Instant kill for now
if (sys_health->systems[system] < 0)
    sys_health->systems[system] = 0;
```

Each system has only 1.0 "health points", which are immediately zeroed when covered by a hit‑box. In reality:

- **Radar damage** ranges from antenna damage (gain loss 3–6 dB) to receiver/processor damage (complete failure) – it is gradual. A fragment hitting the antenna array may only damage some T/R modules (for AESA, 10–30% module loss still allows degraded operation).
- **Engine damage** ranges from slight thrust reduction to single‑engine flameout to dual‑engine shutdown. Engines have redundancy (F‑16 is single‑engine without redundancy, F‑15/F‑22 have dual‑engine redundancy); after one engine fails, the aircraft can still maintain flight and possibly return to base.
- **Fuel system damage** ranges from slow leakage (0.5–1 kg/s) to severe leakage (5–10 kg/s) to complete tank rupture. Leak location (self‑sealing tank vs. external tank) determines leakage rate and whether it can be isolated.

### 6.3 Rotation Transformation from World to Body Axis Has Uncertainty Noted in Comments

```cpp
// default_effects_model.cpp:24-31
// Coordinate system is ENU. Heading 0=North (Y).
// This math can be tricky. For MVP reliability, let's treat Heading
// as rotation around Z. Pitch around X, Roll around Y?
// Actually, standard Euler inverse: R_total = R_z(heading) * R_x(pitch) * R_y(roll).
// Inverse is R_y(-r)*R_x(-p)*R_z(-h).
// But standard aerospace sequence is usually Yaw -> Pitch -> Roll.
// Let's implement a simplified 2D+Height transformation for stability first.
```

The comments indicate that the `world_to_body` function underwent multiple attempts and doubts, and the current implementation is a 2D+height approximation that ignores pitch and roll.

```cpp
// default_effects_model.cpp:70
double local_z = dz; // Assuming flat pitch/roll for MVP interception
```

When the target is in any non‑horizontal attitude (climbing/diving/banking), the hit‑box coordinate transformation will produce incorrect results – the missile may be judged to hit the wrong component or miss a real hit location.

### 6.4 No Warhead Type Differentiation

In the current model, `missile.damage = 120.0` is a generic scalar. Real air‑to‑air missiles use various warhead types:

- **Continuous‑rod warhead** (e.g., AIM‑9, AIM‑120): metal rods expand into an expanding ring after explosion, damaging the target by cutting. Effective damage radius depends on rod expansion diameter and velocity – typically effective at 5–15 meters.
- **Fragment warhead** (e.g., R‑73, Python series): pre‑formed fragments (tungsten alloy cubes/cylinders) penetrate the target structure at high speed. Spatial distribution of fragments (fragment cone angle, density, velocity) determines damage probability.
- **Blast wave effect**: at close range (<3 m), the overpressure from the blast wave can cause structural deformation/skin stripping even without direct fragment hits.

The current model, using a unified `damage` constant, cannot distinguish these mechanisms.

---

## 7. Launch Envelope and Launch Conditions

### 7.1 No Launch Acceptability Region (LAR) Check

The only conditions for missile launch are:

1. Sufficient ammunition (`ammo->missiles_remaining > 0`)
2. Cooling completed (`current_time - last_fire_time > cooldown_s`)
3. Target in the carrier sensor contact list (`has_track == true`)

Real missile launches must satisfy the **Launch Acceptability Region (LAR)**, which includes:

- **Range threshold**: target within the missile’s maximum powered range (R_max) and minimum range (R_min, considering fuze safety and seeker acquisition time)
- **Off‑boresight angle threshold**: the current line‑of‑sight direction of the target must be within the seeker’s maximum off‑boresight angle (critical for Lock‑On Before Launch)
- **Target angular velocity (LOS rate) threshold**: excessively high LOS rate requires the missile to make an overly large initial turn, potentially exhausting energy too quickly or causing the seeker to lose the target before lock‑on.
- **Altitude/heading difference**: climbing/diving consumes additional energy; the launch envelope is significantly reduced at large pitch angles.
- **Carrier speed/altitude**: launching at low altitude/low speed results in low initial dynamic pressure and poor maneuverability, and engine thrust efficiency in dense air is lower than nominal.
- **R_max and R_min are dynamic** – they vary significantly with launch altitude, launch speed, target altitude, target speed, and relative azimuth (head‑on/pursuit/side). For the same missile, the maximum range for a head‑on launch can be 2–4 times that of a tail‑chase launch.

### 7.2 No Rapid Fire / Multi‑Target Launch Restrictions

Currently, `cooldown_s` is the only firing rate limit. In real fire control systems, there are also:

- **Radar timeline constraints**: after launching a SARH missile, the carrier radar must continuously illuminate the target until impact (tens of seconds for an AIM‑7), during which the radar cannot switch targets or launch another SARH missile. For ARH missiles, the carrier must provide data‑link updates during the mid‑course guidance phase (every 1–2 seconds), limiting the number of missiles that can be guided simultaneously.
- **Fire control solution delay**: from pressing the launch button to the missile physically leaving the rail, there is a time delay for the fire control computer to compute the intercept solution → missile seeker cooling/calibration → weapon release (0.5–3 seconds depending on the system).

---

## 8. Disconnection Between Seeker, Carrier, and Data Link

### 8.1 No Mid‑Course Guidance Data Link Between Missile and Carrier

```cpp
// default_guidance_model.cpp:64-68
const ContactList* contacts = missile_entity.get<ContactList>();
if (!contacts) return;
```

The missile relies entirely on its own seeker’s `ContactList` for guidance. In reality, the guidance of medium‑ to long‑range missiles (e.g., AIM‑120) is divided into:

- **Mid‑course guidance** (command‑inertial): the carrier sends target position/velocity updates to the missile via data link. The missile uses its own IMU for inertial navigation, supplemented by carrier‑provided target state corrections. Update frequency 1–2 Hz (Link 16 bandwidth limitation).
- **Terminal active guidance**: at 15–20 km from the target, the missile’s own radar locks onto the target and switches to fully autonomous PN guidance.

The current model is equivalent to the missile being fully autonomous from launch to impact – meaning the carrier can disengage immediately after launch, which is seriously inconsistent with reality for SARH and early ARH missiles.

### 8.2 Zero Effect of Launch Altitude/Speed on Pk

The single‑shot kill probability (Pk) of a real missile varies significantly with launch conditions:

- The Pk of the same missile launched at 40,000 ft / Mach 1.2 may be 2–3 times that launched at sea level / Mach 0.6 (due to higher initial kinetic energy and lower air resistance).
- The Pk for a head‑on launch is generally higher than for a tail‑chase launch (higher relative target speed, shorter time for miss distance to accumulate in the terminal phase).

In the current model, Pk is determined solely by `hit_prob` (minimum distance + evasion), and is completely independent of the kinematic conditions at launch.

---

## 9. Terms That Should Not Be Used for the Current Implementation

1. Do not call the current guidance system “proportional navigation guidance” – it is **LOS‑rate‑driven velocity vector rotation**, with no acceleration commands, no autopilot, and no body dynamics.
2. Do not call the current missile an “air‑to‑air missile simulation” – it is a **constant‑velocity kinematic point mass with immediate lock‑on and zero drag**, with no boost/glide phases, no mass consumption, and no aerodynamic damping.
3. Do not call the current damage model a “warhead damage simulation” – it is a **generic HP deduction plus binary subsystem switches**, with no fragment distribution, no warhead type, and no progressive damage.
4. Do not call the current seeker an “active/infrared seeker simulation” – it is **a replica component of the carrier sensor**, does not distinguish between ARH/SARH/IR guidance modes, has no mid‑course data link, and no LOBL/LOAL states.
5. Do not call the current launch logic “fire control solution” – it is a **cooldown + ammunition + contact existence three‑condition launch**, with no launch envelope, no radar timeline constraints.

This conclusion is frozen until the weapon system analysis is explicitly reopened next time.
```
