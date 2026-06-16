# A9 High-Fidelity Weapon System — Acceptance Draft

Status: `2026-06-16` draft. No acceptance gate has been attempted yet.
This document defines the acceptance conditions; it does not claim any gate is
already passed.

Parent: [README.md](README.md)

## Acceptance Scope

This subproject can be marked `accepted` only when the conditions in each
section below are met. Conditions currently marked `[ ]` are not yet satisfied.

## G1: APN Guidance

- [ ] APN feed-forward term compiles and is active when `apn_target_accel_gain > 0`
- [ ] APN reduces miss distance against a maneuvering target compared to
  classical PN baseline on the same engagement geometry
- [ ] Off state (`apn_target_accel_gain = 0`) produces behavior identical to
  classical PN within floating-point tolerance
- [ ] Existing `weapon_guidance_realism/launch_guidance.py` tests pass
- [ ] New APN-vs-PN comparison test exists and passes

## G2: Kalman Filter Seeker

- [ ] EKF compiles as a standalone model file
- [ ] EKF tracks a non-maneuvering target with covariance convergence within
  configurable frames
- [ ] EKF maintains track continuity through a weaving maneuver
- [ ] Fallback mode (`use_kalman_seeker = false`) preserves existing
  first-order smoothing behavior
- [ ] Tunable noise parameters round-trip through Python bindings

## G3: Three-Loop Autopilot

- [ ] Second/third-order autopilot transfer function compiles
- [ ] Step response rise time matches configurable τ within 10%
- [ ] Existing G-limit tests continue to pass
- [ ] Configurable `autopilot_order` (1/2/3) switches between transfer functions

## G4: Sensor-Driven Fuze Surrogate

- [ ] PF-R4 surrogate implementation preserved (not regressed)
- [ ] PF-R5 matrix validation residuals not widened
- [ ] New refinement (if any) emits diagnostic fields without breaking existing
  `fuze_type` routing, contact/timed paths, or no-detonation no-load invariant
- [ ] Mechanism-specific coverage scores differ between `blast_fragmentation`
  and `continuous_rod`

## G5: Mach-Dependent Aerodynamics

- [ ] Mach-indexed Cd₀ table interpolates smoothly across Mach envelope
- [ ] Power-on drag is lower than power-off drag at the same Mach
- [ ] Induced drag scales with lateral acceleration
- [ ] Speed profile across subsonic-transonic-supersonic is physically plausible
  (no discontinuities, no negative drag)

## G6: Physics-Based Warhead Refinements

- [ ] Fragment velocity follows Gurney equation for given C/M ratio
- [ ] Fragment velocity decays with distance per exponential atmospheric model
- [ ] Continuous-rod velocity is capped at weld-limited threshold (<1,150 m/s)
- [ ] Cutting margin respects minimum striking velocity threshold (>610 m/s)
- [ ] Existing warhead tests continue to pass

## G7: Integration

- [ ] All new `MissileTuning` fields round-trip through Python bindings
- [ ] `debug_get_missile_runtime_state` exposes new diagnostic fields
- [ ] Example scenario JSON exercises new fidelity parameters
- [ ] Full `tests/runtime/air_combat/` suite passes or regressions documented

## Validation Matrix

- [ ] P4-A geometry sweep CSV retained (≥100 runs per bucket)
- [ ] P4-B parameter sensitivity CSV and heatmaps retained
- [ ] P4-C side-by-side comparison summary retained

## Documentation

- [ ] Parent `air_combat/README.md` updated with a9 completion status
- [ ] Archive boundary is explicit: which artifacts are sealed, which are current
- [ ] All public-source data annotated with URL, retrieval date, and
  non-authoritative admission

## Forbidden Claims (Must Remain Refused)

- [ ] `pk_authority` remains `false`
- [ ] `deterministic_fuze_authority` remains `false`
- [ ] `effect_scale_authority` remains `false`
- [ ] `component_failure_probability_authority` remains `false`
- [ ] `real_weapon_pk_authority` remains `false`
- [ ] No AIM-120C-specific parameter claims appear in any output
- [ ] No classified, ITAR, or FOUO data appears in any source ledger
