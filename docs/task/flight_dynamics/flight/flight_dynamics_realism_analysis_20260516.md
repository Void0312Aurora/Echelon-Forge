<!-- Machine-translated draft generated on 2026-05-18 from docs/task/flight_dynamics/flight/flight_dynamics_realism_analysis_20260516.zh.md. Review before treating this file as authoritative. -->

# Flight Dynamics Realism Analysis and Air Combat Prerequisites

Status: `2026-05-16` Frozen analysis version.

Related files:

- [Aerodynamic State System](../../../../src/systems/physics/aero_state_system.h)
- [Force System (Gravity/Thrust)](../../../../src/systems/physics/force_system.h)
- [Aerodynamic System (Lift/Drag/Moment)](../../../../src/systems/physics/aerodynamics_system.h)
- [Ground Contact System](../../../../src/systems/physics/ground_contact_system.h)
- [Rotational Integration System](../../../../src/systems/physics/rotational_system.h)
- [Translational Integration System](../../../../src/systems/physics/leapfrog_system.h)
- [Flight Control Model](../../../../src/models/air/default_control_model.cpp)
- [Flight Control System Entry](../../../../src/systems/physics/control_system.h)
- [Dynamics Component Definitions](../../../../src/components/physics/dynamics.h)
- [Force/Moment/Inertia Components](../../../../src/components/physics/forces.h)
- [Aerodynamic Reference Geometry Component](../../../../src/components/systems/logistics.h) (MassProperties)
- [Physics Engine Upgrade Roadmap](../../../forward/physics_engine_roadmap.md)
- [Engine Capability List](../../../manual/engine_capabilities.md)
- [Physics Engine Inventory](../../../manual/physics_engine_inventory.md)
- [Air Combat 1v1 Cut-in Analysis](../../air_combat/air_combat_1v1_entry_analysis_20260516.zh.md)
- [Air Combat 1v1 Training Smoke Test Progress](../../air_combat/air_combat_1v1_training_smoke_progress_20260516.zh.md)
- [Air Combat 1v1 Deep Stall Root Cause Follow-up](../../air_combat/air_combat_1v1_stall_rootcause_followup_20260516.zh.md)
- [First Batch of Realism Gate Keeping Tests](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)

Document positioning:

- This document only records the known deficiencies of the current flight dynamics pipeline and their corresponding real physics/engineering situation.
- It does not cover acceptable simplifications, does not provide prioritization, and does not give a work plan.
- Sections 10 to 12 additionally record the impact analysis and acceptance threshold of flight dynamics as a prerequisite for air combat.

## Postscript: `2026-05-17` Closure Markers

Closure criteria:

- `Unsolved`: The original argument is still basically valid, currently still directly treatable as a pending issue.
- `Partially solved`: Some partial implementation or gate-keeping contract exists, but the main distortion remains.
- `Minimal closure achieved`: It is no longer appropriate to state as "completely missing"; a minimal operational closed loop already exists.
- `Solved`: The old discussion is no longer suitable as a description of the current state.

This postscript only answers "Are these arguments still valid today?", not rewriting this document into a progress board.

| Item | Current Marker | Description |
|------|----------------|-------------|
| `2.1` Lift Model | `Partially solved` | Minimal `Mach/stall` schedule entry and gate-keeping exist, but negative angle-of-attack asymmetry, `beta` coupling, and aircraft-type curves are still not closed |
| `2.2` Drag Model | `Partially solved` | Minimal `Mach/cd0/induced drag` scheduling exists, but wave drag decomposition, external store interference, and more credible ground effect are still missing |
| `2.3` Moment Model | `Partially solved` | `stall_progress / pitch_break surrogate / alpha_dot` have entered runtime, but control surface derivatives and full stability derivative scheduling are still missing |
| `2.4` Stall/Post-Stall Dynamics | `Partially solved` | Minimal `pitch break / recovery trend` exists, but `hysteresis / wing rock / post-stall` are still not closed |
| `2.5` Thrust and Propulsion System | `Minimal closure achieved` | `spool / AB / TSFC / shared propulsion fact` are connected, but it is still not an aircraft-level engine model |
| `2.6` Inertia and Mass | `Unsolved` | `Ixz`, post-release inertia recalculation, and fuel distribution effects on inertia are still not integrated |
| `2.7` Integrator Accuracy | `Unsolved` | No evidence of closure for rotational integration and `Velocity-Verlet` upgrade |
| `2.8` Atmosphere and Environment | `Partially solved` | The atmosphere input skeleton is unified, but high-altitude speed of sound, turbulence, and wind shear are still missing |
| `2.9` FBW Flight Control System | `Unsolved` | `g-command / gain scheduling / G-limiter / control allocation` have not entered the current main line |
| `2.10` Stale Code/Documentation Desync | `Solved` | This stale description no longer represents the current implementation and should be considered historical residue |
| Section 5 Main Risks for Air Combat | `Partially solved` | Thrust transients and high-AoA recovery have minimal closure, but compressibility and `RSS/FBW` remain main risks |
| Section 6 Realism Gate Keeping | `Minimal closure achieved` | `coarse realism guards` have been committed, but cannot replace high-fidelity acceptance |
| Section 7 Post-Merge Conclusion | `Partially solved` | "Can support pipeline but cannot claim high fidelity" still holds, but the base has advanced noticeably |

---

## I. Current System Pipeline Overview

The current flight dynamics pipeline, in ECS registration order, is:

```
AeroStateSystem       → Compute angle of attack, sideslip, dynamic pressure, Mach
ForceClearSystem      → Clear ForceAccumulator
ForceSystem           → Add gravity + thrust (with density/Mach calibration)
AerodynamicsSystem    → Add lift + drag + aerodynamic moments
GroundContactSystem   → Ground spring-damper + tire friction + NWS
RotationalIntegration → Euler equations + Euler angle kinematics
LeapfrogIntegration   → Störmer-Verlet translational integration
```

The control chain is:

```
PilotAction / MissionCommand
  → ControlModel (FBW rate commands / autopilot)
    → ControlLawState
      → Control moments injected into ForceAccumulator
```

---

## II. Known Discrepancy Points

### 2.1 Lift Model

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Cl_α fixed at 0.1/deg, no Mach dependence** | `aerodynamics_system.h:64` `kClAlphaPerDeg = 0.1` | Prandtl-Glauert compressibility correction: `Cl_α(M) = Cl_α(0) / √(1-M²)` (subsonic), decreases in supersonic according to Ackeret theory. In transonic region (M 0.8-1.2), Cl_α peaks at 2-3 times low-speed value. Current model severely underestimates available lift at high subsonic speeds, overestimates at supersonic speeds |
| **Stall angle of attack hardcoded as constant** | `aerodynamics_system.h:83` `alpha_stall_deg = 15.0 + 6.0*flaps` | Real stall angle of attack varies nonlinearly with Mach (compressibility reduces stall AoA by ~2-4°), Reynolds number, and flap deflection. Current flap effect only provides a simple offset |
| **Deep stall plateau Cl=0.22 physically unreasonable** | `aerodynamics_system.h:88` `cl_deep_mag = 0.22` | Real deep separated flow region experiences significant oscillation of lift coefficient (unsteady vortex shedding), no smooth plateau exists. At 90° AoA, flat plate Cl≈0 (pure drag), should not remain constant |
| **No negative angle-of-attack stall asymmetry** | `aerodynamics_system.h:79` `alpha_abs` judgment | Wing with camber has asymmetric positive/negative stall behavior. Negative AoA stall typically occurs earlier (Cl_min about -0.8 to -1.2), while positive AoA stall has Cl_max ≈ 1.2-1.6 |
| **No sideslip-lift coupling** | Lift calculation completely independent of beta | At large sideslip angle, effective sweep changes, affecting lift curve slope. Typical fighter can lose 10-15% of Cl_max at β=20° |

### 2.2 Drag Model

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Cd0 hardcoded as 0.02, no Mach dependence** | `aerodynamics_system.h:108` `double Cd0 = 0.02` | Transonic wave drag causes Cd0 to increase sharply at M>0.8. Near M=1.0, it can be 3-5 times subsonic value; area rule can reduce but not eliminate. Current model severely underestimates drag in transonic region |
| **k=0.1 constant, no Mach dependence** | `aerodynamics_system.h:124` `double k = 0.1` | Shock/boundary layer interaction in transonic region increases induced drag factor |
| **Ground effect correction accuracy for induced drag unknown** | `aerodynamics_system.h:142` `k_eff = k*(1 - 0.70*ge)` | This formula applies to high aspect ratio wings. Ground effect reduction for low aspect ratio delta/cropped delta wings is 30-50% |
| **No external store interference drag** | `aerodynamics_system.h:110` only adds `0.001*drag_index` | In addition to store's own drag, interference drag from fuselage/wing contributes 20-40% of total store drag; currently completely missing |
| **No base drag / wave drag / induced drag decomposition** | Single Cd0 + k*Cl² | Real drag should be decomposed into form drag (friction + pressure), induced drag, wave drag, each with different speed/AoA dependencies |

### 2.3 Moment Model

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **No control surface derivatives** | Moment model has no Cl_δa, Cm_δe, Cn_δr | Real pitching moment = Cm_α·α + Cm_δe·δe + Cm_q·q_hat + Cm_α̇·α̇_hat. Moments from control surface deflections are equally important as stability derivatives. Although FBW injects control as moments, surface deflection simultaneously changes bare airframe aerodynamic characteristics (e.g., δe changes horizontal tail effective AoA, thus affecting overall Cm_α) |
| **Missing Cm_α̇ (downwash lag damping)** | No such term | Pitching moment due to rate of change of AoA (from downwash lag at tail) is critical for short-period mode. Missing this term leads to low short-period damping and high frequency |
| **No Cn_p (roll-induced yaw)** | `aerodynamics_system.h:245` comment `// Neglect Cn_p for now` | Asymmetric lift from left and right wings during roll produces yawing moment, a key term for Dutch roll mode |
| **Stability derivatives are hardcoded constants** | `Cm_α = -0.8`, `Cn_β = 0.15` | Real derivatives vary significantly with α and M. At high α, downwash enhancement changes horizontal tail effectiveness, altering Cm_α. Transonic shock movement greatly changes all derivatives |
| **Cm_α fixed for a statically stable aircraft** | `Cm_α = -0.8` | Modern fighters (F-16, Su-27) use Relaxed Static Stability (RSS); subsonic Cm_α ≈ -0.2 or even slightly positive—entirely dependent on FBW augmentation. Current model flattens this decisive design characteristic into a traditional stable layout |
| **Uniform damping decay in deep stall** | `aerodynamics_system.h:223` `damp_scale = 1 - 0.7*stall_rel` | In stall, pitch damping (horizontal tail immersed in separated wake) decays fastest, yaw damping (vertical tail still in relatively clean flow) decays slowest. Should not use a uniform coefficient |

### 2.4 Stall/Post-Stall Dynamics

Systematic deviation between real physics and current model:

```
Real Physics                           Current Model
───────────                           ───────────────
Cl has sharp kink near stall AoA      smoothstep transition smooth
Cm produces strong nose-down moment   Cm continues linearly into deep stall,
at stall (pitch break, pressure        pitching moment from linear extrapolation of Cm_α·α
center shift aft)
Lateral-directional damping drops      Damping decays uniformly,
significantly, wing rock appears        no wing rock
Significant angle-of-attack hysteresis No hysteresis
in stall-recovery
```

The absence of pitch break is especially critical—in real aircraft, the pressure center shifts aft during stall, producing a strong nose-down moment that aids automatic recovery. Currently, even at AoA > 30°, it still uses linear extrapolation of `Cm_α = -0.8`, severely underestimating the nose-down recovery trend at high AoA, while flattening the training value of pitch break as a "sensible physical signal" of stall.

### 2.5 Thrust and Propulsion System

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Throttle nearly binary** | `force_system.h:127-132` >0.9 directly jumps to full afterburner | Real turbofan has continuous thrust curve. Afterburner has independent regulation (4-5 stages), not a 0/1 switch |
| **No engine transient delay** | Thrust command instantaneously effective | Idle → military requires 2-4 seconds (rotor inertia), military → full afterburner requires additional 1-2 seconds (ignition + flame stabilization). Lack of this delay causes RL to learn high-frequency throttle pulses—completely infeasible on real engines due to thermal cycling/overtemperature |
| **Ram factor has no upper limit decay** | `force_system.h:152` `1.0 + 0.3*M` | At M>1.5, shock losses reduce ram benefit. Actual ram factor at M=2.0 is ~1.2-1.3, not 1.6 |
| **Temperature effect completely missing** | Thrust scaled only by σ | Gas turbine thrust ∝ δ/√θ; hot day/high altitude thrust is 15-25% lower than cold day/sea level at same density |
| **mil/AB thrust are fixed values** | `Propulsion.mil_thrust_n`, `ab_thrust_n` | Scaling only by σ and ram is insufficient—real installed thrust curve varies with M/h including installation losses, inlet distortion, etc., non-monotonically |
| **No fuel-thrust consistency** | `LogisticsSystem` independently calculates fuel consumption | Afterburner SFC is 2-3 times military; fuel consumption should vary consistently with thrust |

### 2.6 Inertia and Mass

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Inertia tensor is only diagonal** | `forces.h:40-43` only has `ixx, iyy, izz` | Real aircraft have Ixz in the plane of symmetry. For fighters, Ixz can reach 5-15% of Ixx; ignoring it distorts rapid roll-yaw coupling |
| **Inertia not updated after store release** | `Mass.stores_mass_kg` changes but `Inertia` not automatically recalculated | After missile launch, rotational inertia remains at original value, distorting turn response |
| **No fuel distribution effect on inertia** | Fuel consumption only changes total weight | Wing fuel tank consumption in high aspect ratio aircraft changes roll inertia Ixx distribution |
| **Risk of dual mass/inertia storage** | Both `Mass` and `MassProperties` store `empty_mass_kg` | Risk of inconsistency between physics and logistics sides |

### 2.7 Integrator Accuracy

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Leapfrog is not true Velocity-Verlet** | `leapfrog_system.h:67-79` | Both half-kicks use a(t) instead of a(t+dt). For time-dependent aerodynamic forces, this is first-order approximation, not strictly symplectic. True Velocity-Verlet requires re-evaluating force function to obtain a(t+dt) for the second half-kick |
| **Rotational integration is explicit Euler** | `rotational_system.h:113-115` | `p += p_dot * dt` etc., not symplectic, accumulates energy error in long-term rotation. Proper approach uses quaternion integration of angular velocity or at least midpoint rule |
| **Ground hard stop is non-physical** | `leapfrog_system.h:84-89` when z < -5m directly truncates velocity and displacement | This is not physical contact, but numerical crash protection—yet introduces discontinuous velocity jumps |

### 2.8 Atmosphere and Environment

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Speed of sound completely wrong above 11km** | `aero_state_system.h:77` `340.29 - 4.0*alt_km` | In stratosphere (>11km), speed of sound is constant at ~295 m/s; linear extrapolation gives ~260 m/s at 20km—error ~13% |
| **No turbulence/gusts** | Wind field only steady component | Missing Dryden/von Kármán turbulence model. Real atmosphere has significant convective turbulence at low altitude (<3000m), clear air turbulence and wind shear at high altitude |
| **No wind shear** | Wind field vertically uniform | Low-level wind shear (microburst) is a critical flight safety scenario, can produce abrupt speed changes of 30-50kt during takeoff/landing |

### 2.9 FBW Flight Control System

| Discrepancy | Code Location | Real Physics/Engineering |
|-------------|---------------|-------------------------|
| **Rate command gains not scheduled across envelope** | `default_control_model.cpp:362-364` kRoll/Pitch/YawGain are constants | Real FBW gains are functions of q_bar, M, α, and configuration. Low speed/high α requires larger gain to maintain same angular rate; high speed requires smaller gain to avoid overload exceedance |
| **Stick force-to-load factor gradient not modeled** | Pure rate command | Real FBW cruise is typically g-command (stick displacement → normal load factor, not pitch rate) to avoid large load factor overshoot at high speed with same stick deflection |
| **No actuator dynamics** | Control moments directly injected | Real full-moving horizontal tail has rate limit (40-60°/s), and aerodynamic hinge moment at high speed reduces effective deflection rate |
| **No G-limiter** | Does not exist | F-16 typically +9G/-3G envelope; currently no normal load factor constraint. RL policy can execute any numerical normal load factor |
| **No cross-coupling control surface scheduling** | Moments directly applied to body axes | No control allocation (pitch = horizontal tail + flaperons, roll = flaperons + differential horizontal tail + spoilers, yaw = rudder + differential horizontal tail). Real flight control mixing logic determines deflection combination of each surface |

### 2.10 Stale Code/Documentation Desync

`force_system.h:174-176` still contains outdated comments:

```cpp
// === 4. LIFT (Simplified) ===
// For now, we model lift implicitly through the control model
// A proper lift model will be added in Phase 2
```

This comment claims "lift handled implicitly, Phase 2 to be implemented", but `AerodynamicsSystem` already implements full explicit lift/drag/moment calculation. This is stale residue not cleaned up after code evolution.

---

## III. Statements That Should Not Be Used Currently

To avoid semantic drift, the following statements should be explicitly avoided:

1. Do not refer to the current aerodynamic model as "real flight dynamics simulation"—it is
   **"textbook linear aerodynamics + simplified stall + no compressibility effects"**.
2. Do not refer to the current FBW system as "F-16 level flight control"—it is
   **"generic rate command FBW abstraction"**, no g-command, no control allocation, no RSS stabilization.
3. Do not refer to the current propulsion system as "turbofan engine simulation"—it is
   **"two-point thrust + density/ram scaling"**, no transients, no temperature effects, no RPM.
4. Do not refer to the current stall model as "post-stall dynamics"—it is
   **"static lift coefficient smoothstep transition"**, no pitch break, no wing rock, no hysteresis.

A more accurate description is:

- **RL training-consistent physics environment**
- **Simplified linear aerodynamics + stall transition + FBW abstraction**
- **Suitable for takeoff/cruise/basic maneuver training, not suitable for transonic/supersonic/post-stall combat**

---

## IV. Why Flight Dynamics Is a Prerequisite for Air Combat

In air combat simulation, flight dynamics is not a "background layer", but the foundation that determines whether training leads to correct learning.

### 4.1 Energy Maneuvering Is a Core Variable in Air Combat

Air combat decisions heavily depend on the real coupling among:

- Speed
- Altitude
- Thrust
- Drag
- Normal load factor
- Nose pointing rate

If the relative relationships among these quantities are distorted, even if the strategy "wins" in the current environment, what is learned may only be a speculative path exploiting the simplified model, not a transferable tactic.

### 4.2 Flight Control/Aerodynamic Distortions Directly Change the "Learnable Action Space"

For RL, the action space is not the literal definition of `stick_pitch / stick_roll / throttle`, but what these actions actually yield in terms of attitude and energy changes in the world.

Once the following deviations exist, the strategy will be systematically led in the wrong direction:

- Throttle can instantaneously produce thrust changes that a real engine cannot provide
- High AoA region lacks real pitch break / recovery trends
- Roll, pitch, sideslip responses are too strong or too weak
- High-speed drag rise is insufficient, leading to "free energy"

### 4.3 Sensors/Weapons/Termination Logic Also Depend on Platform Dynamics

Air combat is not just "see and shoot". Platform dynamics change:

- Closure rate
- Attitude stability
- Platform controllability before launch
- Break engagement / re-engagement windows
- Entry and exit rhythm of missile launch envelope

Therefore, even if the weapon chain and termination rules are all correct, once platform dynamics deviate too much, the high-level result will still be distorted.

---

## V. The Most Impactful Flight Dynamics Risks for Air Combat Advancement in Current Mainline

Combining the existing flight dynamics analysis and the current `1v1` training status, the most concerning aspect is not that "the model is not yet detailed enough", but that the following distortions have already started to directly affect air combat training performance.

### 5.1 Missing Transonic/Supersonic Compressibility Distorts Energy Management

In the current aerodynamic model:

- `Cl_alpha`
- `Cd0`
- `k`
- `Cm_alpha`

all lack reliable Mach-dependent corrections.

This means:

- High-speed available lift may be misestimated
- Missing wave drag underestimates high-speed energy loss
- Performance differences between high-altitude high-speed and low-altitude subsonic are flattened

For air combat, this is not a "detail issue", but directly changes:

- Whether a pursuit is worthwhile
- Whether a dive for speed exchange is economical
- The order of benefit between sustained turn and zoom climb separation

### 5.2 Current Bare Airframe Longitudinal Static Stability Still Resembles a "Classic Stable Aircraft"

Currently `Cm_alpha` is hardcoded to a magnitude typical of a traditional stable layout aircraft.

This weakens the most critical behavioral differences of modern fighters:

- Relaxed Static Stability
- Nose pointing capability after FBW augmentation
- High AoA transient response

Therefore, if the current air combat line continues to push into higher maneuver combat, it can easily train "modern fighter air combat" into a strategy of "traditional stable aircraft + generic rate command FBW".

### 5.3 Missing Engine Transients Causes "Throttle Cheating" to Be Mistaken as a Tactic

Current thrust response is still nearly instantaneous.

In air combat, this has two direct consequences:

- The strategy will learn high-frequency throttle pulses, not real energy management rhythm
- Time constants for speed recovery, zoom climb maintenance, and drag-out re-acceleration are all overly optimistic

Such deviations will not just manifest as "the engine looks unrealistic", but will rewrite the entire engagement rhythm.

### 5.4 Insufficient High AoA Recovery Mechanism Turns Stalls into Major Learning Noise

In existing `1v1` smoke tests, very concrete symptoms have already appeared:

- `failfast_deep_stall` dominates termination
- Typical `AoA` reaches `50 deg+`
- `pitch` can reach `77-82 deg`

This indicates that the current problem is no longer an abstract "might affect air combat", but rather:
**The coupling of flight dynamics / flight control / training signals has already exposed real issues in high AoA recovery and energy management within the main line.**

---

## VI. Thresholds and First Batch of Realism Tests Before Proceeding with Air Combat Simulation

It is recommended to divide flight dynamics acceptance into three layers.

### 6.1 Gate A: Physical Consistency

This layer first answers "Does it obviously violate basic physics?"

Minimum requirements:

- Same `seed` results are reproducible
- No non-finite values appear
- Free fall approximately satisfies `-g`
- Positive and negative inputs at least satisfy direction consistency and approximate symmetry

This layer mainly addresses "whether the code is broken", not "whether it is realistic enough".

### 6.2 Gate B: Coarse Realism Gate Keeping

This layer answers "Does the trend resemble an aircraft, rather than a rigid body toy forcibly dragged by the flight controls?"

At least the following should be automatically checked:

- Larger throttle should yield higher specific energy change rate
- Larger nose-up input should yield higher AoA, greater climb, and more obvious speed exchange
- Left and right roll should be approximately symmetric, and should not produce large sideslip without cause
- Basic response in moderate-low AoA range should be smooth, bounded, and reproducible

This layer cannot prove "sufficiently high fidelity", but can prevent the most dangerous regression: the surface behavior still looks flyable, but the internal physical trends are already reversed.

### 6.3 Gate C: Air Combat Prerequisite Threshold

This layer answers "Is it sufficient to proceed with deeper air combat training?"

The prioritized recommended thresholds are:

- After entering high AoA, there should be observable recovery trend, not just relying on failfast termination
- High-speed drag and energy loss should at least have the correct trend
- Climb/dive speed exchange relationship should not show obvious unphysical benefits
- Platform attitude and energy state before launch should not stay in unrealistic high AoA region for long periods

The current mainline still has gaps relative to this threshold, so it is more suitable to describe the current stage as:

- The air combat process foundation is in place
- Flight dynamics realism gate-keeping is being filled in
- "Credible air combat maneuver performance" is not yet claimed

### 6.4 First Batch of Suggested Automated Realism Gate-Keeping Items

This round first implements a set of coarse realism gate-keeping tests, aiming not for aircraft-level certification, but to provide a minimum physical trend check before air combat progression.

#### 6.4.1 Throttle - Specific Energy Ordering

Goal:

- `idle` vs `full throttle`: the latter should clearly increase specific energy
- At minimum, there should be no inverted trend of "more thrust but lower specific energy"

Significance:

- It is closer to the energy state of air combat interest than just looking at `IAS`
- Can early expose regressions in thrust/drag/gravity coupling

#### 6.4.2 Speed-Altitude Exchange for Nose-Up Input

Goal:

- Larger nose-up input should yield greater climb gain
- Accompanied by higher `AoA` and more obvious speed loss

Significance:

- Checks whether longitudinal maneuvers have basic energy conservation intuition
- Prevents distortions like "nose-up almost gives free altitude increase" or "nose-up does not increase AoA"

#### 6.4.3 Left-Right Roll Mirror Symmetry

Goal:

- Left roll and right roll with same amplitude input should be approximately symmetric
- Lateral displacement direction opposite and magnitude similar
- Should not introduce excessive `beta` without cause

Significance:

- Checks for sign errors or asymmetric coupling anomalies in lateral-directional response
- Such problems in air combat will directly contaminate break turns / jinks / out-of-plane maneuvers

#### 6.4.4 Response in Moderate-Low AoA Range is Bounded

Goal:

- In these probes, `AoA`, `G`, `roll`, `pitch` should all remain in interpretable ranges

Significance:

- Not requiring "realistic limits", but first blocking the most dangerous numerical drift

### 6.5 First Batch of Tests Already Implemented in This Round

New addition in this round:

- [tests/runtime/test_flight_dynamics_realism_guards.py](../../../../tests/runtime/test_flight_dynamics_realism_guards.py)

Coverage:

1. Total specific energy ordering of `full throttle` versus `idle`
2. Altitude gain / angle of attack growth / speed exchange trends under different pitch inputs
3. Left-right roll mirroring and sideslip constraints

Run command:

```bash
source tools/maintenance/cmo_env.sh
cmo_env_validate
cmo_python -m pytest -q tests/runtime/test_flight_dynamics_realism_guards.py
```

Note:

- These tests are **coarse realism guards**, not model fidelity certification
- Their positioning is "before continuing to expand the air combat pipeline, first ensure that the underlying trends are not obviously reversed"

### 6.6 What these tests explicitly cannot prove

Even if the initial guard tests all pass, one cannot claim that:

- Credible transonic/supersonic air combat physics have been achieved
- Credible post-stall maneuvers have been achieved
- Credible modern fighter RSS / FBW maneuvering characteristics have been achieved
- Credible engine transients and energy recovery pacing have been achieved

In other words, they only demonstrate:

- The current model still exhibits "aircraft-like" trends in several key input-output relationships
- Rather than having reached tactical-level high fidelity

### 6.7 Recommended next reinforcement directions

If flight dynamics continues to be advanced as the air combat prerequisite line, the following are recommended for prioritization in the next round:

1. `pitch break / stall recovery` guard test
2. Trim and drag trend tests under `Mach` variation
3. Engine step throttle response test
4. Total specific energy consistency test during high-speed dive and pull-up

Among these:

- `Mach` corrections
- Engine transients
- Stall recovery trends

Should still be regarded as the three most important physics prerequisite works.

---

## VII. Consolidated Conclusion

In the current repository, a more accurate advancement stance should be:

1. Flight dynamics is already sufficient to support air combat workflows, weapon chains, and basic training loops.
2. However, it is not yet sufficient to confidently explain "why the learned air combat maneuvers are correct."
3. Therefore, air combat advancement cannot only look at reward, win rate, and weapon chain closure;
   the flight dynamics realism guard must be established concurrently.
4. The most important physics prerequisite works remain: compressibility corrections, engine transients, and stall recovery trends.
5. The value of the newly added tests in this round is not to declare "problem solved," but to formally land this guard line in the repository,
   so that subsequent air combat iterations will at least not unknowingly continue to amplify underlying dynamics distortions.
