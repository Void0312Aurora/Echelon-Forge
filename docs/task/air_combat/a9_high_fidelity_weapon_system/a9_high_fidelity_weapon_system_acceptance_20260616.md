# A9 High-Fidelity Weapon System — Acceptance

Status: `2026-06-16` acceptance review. 12 of 28 clusters pass, 2 partial.
No gate claims `accepted` — this records which conditions are met and which
remain open with documented residuals.

Parent: [README.md](README.md)

## Acceptance Scope

This subproject can be marked `accepted` only when all `[ ]` items below are
resolved or explicitly deferred with residual entries. `[x]` = met. `[~]` =
partially met with residual.

## G1: APN Guidance

- [x] APN feed-forward term compiles and is active when `apn_target_accel_gain > 0`
- [~] APN reduces miss distance against a maneuvering target — **residual**:
  P4-A sweep confirms feed-forward changes trajectory; against non-maneuvering
  targets the simple bearing-acceleration differentiator injects noise,
  degrading PN performance. A low-pass filter on λ̈ or maneuver-detection gate
  is needed before APN outperforms PN.
- [x] Off state (`apn_target_accel_gain = 0`) produces PN-identical behavior
  (feed-forward term multiplies by zero; no estimator state changes)
- [x] Existing `weapon_guidance_realism/launch_guidance.py` tests pass
- [x] APN-vs-PN comparison exists: `p4_validation/p4a_apn_geometry_sweep_20260616.py`
  (12 data points across 4 geometries × 3 gain levels)

## G2: Kalman Filter Seeker

- [x] EKF compiles as standalone model file (`kalman_seeker.h`, 295 lines)
- [ ] EKF tracking performance not yet quantitatively validated — no covariance
  convergence test, no weaving-target continuity test. EKF branch is opt-in
  (`use_kalman_seeker = false` default) and all existing tests exercise the
  legacy first-order smoothing path.
- [x] Fallback mode (`use_kalman_seeker = false`) preserves first-order smoothing
- [x] Tunable parameters: `use_kalman_seeker` in full MissileTuning/JSON/
  Python pipeline; EKF params (sigma_a, tau_m, angle/range noise) have
  sensible defaults in `SeekerEkfParams`
- [x] Coordinate frames: body-relative bearing/elevation ↔ world Cartesian
  via `body_rel_to_world` / `world_to_body_rel` with heading_rad
- [x] LOS rates computed from frame-to-frame angle deltas in both detection
  and coast paths
- [x] Closing speed uses actual missile velocity

## G3: Three-Loop Autopilot

- [x] Second-order state-space filter compiles (`H(s) = ω_n²/(s²+2ζω_n·s+ω_n²)`)
- [ ] Step-response rise-time test not yet implemented
- [x] Existing G-limit tests pass (zero regression)
- [~] `autopilot_order` (1/2/3): order=1 (legacy lag), order≥2 (state-space).
  order=3 not differentiated from order=2 — **residual**: three-loop topology
  (rate/stability/acceleration) not yet modeled; current implementation is a
  configurable second-order low-pass, not a true three-loop autopilot.
- [x] `autopilot_damping` in full MissileTuning/JSON/Python pipeline

## G4: Sensor-Driven Fuze Surrogate

- [x] PF-R4 surrogate preserved (no regression)
- [x] PF-R5 residuals not widened
- [x] `hit_to_kill` coverage differentiation added: proximity burst coverage
  penalized to `range_score × 0.08` (non-direct-hit), reflecting primary
  kinetic-penetrator mechanism
- [x] Existing `fuze_type` routing, contact/timed paths, no-detonation
  no-load invariant preserved
- [x] `damage_mechanism_coverage_score` already differentiates continuous_rod
  (lateral/axial geometry correction) from blast_fragmentation (range score)

## G5: Mach-Dependent Aerodynamics

- [x] Configurable Mach transonic breakpoints (`mach_transonic_start`/`_end`)
  replace hardcoded 0.8/1.4
- [x] Power-on base-drag reduction (`cd0_power_on_ratio`, default 0.90)
- [~] Mach-indexed Cd₀ **table** — **residual**: current implementation still
  uses single subsonic/supersonic Cd₀ with lerp between configurable
  breakpoints. A multi-row Mach table (`cd0_mach_table`) is deferred.
- [x] Induced drag scales with lateral acceleration (existing behavior preserved)
- [x] Speed profile physically plausible (no discontinuities, no negative drag)
- [x] All G5 params in full MissileTuning/JSON/Python pipeline

## G6: Physics-Based Warhead Refinements

- [ ] Fragment velocity does NOT yet follow Gurney equation — **residual**:
  `explosive_mass_kg`, `case_mass_kg`, `gurney_constant_mps` fields are plumbed
  through WarheadProfile/loader/bindings, but fragment velocity still uses
  legacy empirical formula (`1120 + 18*sqrt(mass_kg) + 0.18*closure`).
  Gurney activation requires explicit `has_physics_warhead` gate.
- [ ] Fragment velocity decay not yet implemented — same residual as above
- [x] Continuous-rod velocity cap at 1,150 m/s (opt-in: requires
  `gurney_constant_mps` configured)
- [x] Cutting threshold at 610 m/s striking velocity (opt-in)
- [x] Rod striking velocity decay `exp(-0.004*(d-3m))` (opt-in)
- [x] Existing warhead tests pass — zero regression (30 pre-existing failures
  in warhead/component surface, identical on main)

## G7: Integration

- [x] All new `MissileTuning` fields have Python bindings
- [x] `debug_get_missile_runtime_state` exposes new diagnostic fields
- [ ] No scenario JSON example exercising new params yet
- [x] Full `tests/runtime/air_combat/` suite: 62 pre-existing failures on main,
  identical count on branch. Zero regressions introduced.

## Validation Matrix

- [x] P4-A geometry sweep: CSV retained (12 data points: 4 geometries × 3 gain
  levels). Head-on/tail-chase limited by missile timeout; beam/HOB confirm
  feed-forward changes trajectory.
- [ ] P4-B parameter sensitivity: not yet executed
- [ ] P4-C side-by-side comparison summary: not yet executed

## Documentation

- [x] Parent `air_combat/README.md` links a9 subproject
- [x] Archive boundary explicit: `archive/README.md` exists
- [x] Public-source data annotated in `p1_evidence/source_ledger_20260616.md`
  with URL, retrieval date, tier, rights, scope, and non-authoritative admission
- [x] AIM-120 parameters isolated to `sanity_check_only` section of source ledger

## Forbidden Claims (Must Remain Refused)

- [x] `pk_authority` remains `false`
- [x] `deterministic_fuze_authority` remains `false`
- [x] `effect_scale_authority` remains `false`
- [x] `component_failure_probability_authority` remains `false`
- [x] `real_weapon_pk_authority` remains `false`
- [x] No AIM-120C-specific parameter claims in any output
- [x] No classified, ITAR, or FOUO data in any source ledger

## Residual Register

| ID | Description | Severity | Blocks acceptance? |
|----|-------------|----------|-------------------|
| R1 | APN bearing-accel estimator needs low-pass filter for non-maneuvering targets | Medium | Yes (G1 partial) |
| R2 | EKF tracking performance not quantitatively validated | Medium | Yes (G2 partial) |
| R3 | autopilot order=3 not differentiated from order=2 | Low | No |
| R4 | Mach Cd₀ table (multi-row) deferred; single-lerp used | Low | No |
| R5 | Gurney equation not yet active (C/M/E plumbed, legacy formulas default) | Medium | Yes (G6 partial) |
| R6 | No scenario JSON example exercising new params | Low | No |
| R7 | P4-B/P4-C validation sweeps not executed | Low | No |
| R8 | 30 pre-existing warhead/component test failures (same on main) | Info | No (not introduced by a9) |
| R9 | All authority claims remain refused | Blocking | N/A (boundary, not residual) |
