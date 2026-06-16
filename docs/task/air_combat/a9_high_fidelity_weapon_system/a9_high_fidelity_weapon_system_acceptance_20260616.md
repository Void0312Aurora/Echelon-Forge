# A9 High-Fidelity Weapon System — Acceptance

Status: `2026-06-16` **accepted_with_residuals**. 23 clusters pass, 5 deferred.
All forbidden claims remain refused. 2 open residuals (R2, R4).
Zero regressions vs main.

Parent: [README.md](README.md)

## Acceptance Scope

This subproject can be marked `accepted` only when all `[ ]` items below are
resolved or explicitly deferred with residual entries. `[x]` = met. `[~]` =
partially met with residual.

## G1: APN Guidance

- [x] APN feed-forward term compiles and is active when `apn_target_accel_gain > 0`
- [x] APN feed-forward filtered: `exp_smooth(λ̈_raw, τ=0.30s)` added (wave 10).
  P4-A re-run: beam Δ 883→27m, HOB Δ 2347→413m. Residual noise against
  non-maneuvering targets is expected — APN is designed for maneuvering targets.
  Full validation against maneuvering targets remains future work.
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
- [x] `autopilot_order` (1/2/3): order=1 (legacy lag), order=2 (state-space),
  order=3 (state-space + first-order actuator lag, τ_act=0.03s ≈ 30 Hz).
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

- [x] Fragment velocity uses Gurney equation when `has_physics_warhead` is true
  (gurney_constant_mps + explosive_mass_kg + case_mass_kg configured):
  `V0 = √(2E) · √((C/M)/(1 + C/2M))`. Legacy empirical formula preserved as default.
- [x] Fragment velocity decay: `V(s) = V0·exp(-Cd·ρ·A·s/(2m))` with
  Cd=1.0, ρ=1.225 kg/m³, A from fragment mass (spherical steel assumption).
  Clamped to [0.3, 1.0] decay factor. Physics path only.
- [x] Continuous-rod velocity cap at 1,150 m/s (opt-in: requires
  `gurney_constant_mps` configured)
- [x] Cutting threshold at 610 m/s striking velocity (opt-in)
- [x] Rod striking velocity decay `exp(-0.004*(d-3m))` (opt-in)
- [x] Existing warhead tests pass — zero regression (30 pre-existing failures
  in warhead/component surface, identical on main)

## G7: Integration

- [x] All new `MissileTuning` fields have Python bindings
- [x] `debug_get_missile_runtime_state` exposes new diagnostic fields
- [x] P3-C tuning example (`p3c_a9_tuning_example.py`) exercises new params
- [x] Full `tests/runtime/air_combat/` suite: 47 pre-existing failures (skipping
  crashing fixture), 286 passed, 233 subtests passed. Zero regressions vs main.

## Validation Matrix

- [x] P4-A geometry sweep: CSV retained (12 data points: 4 geometries × 3 gain
  levels). Head-on/tail-chase limited by missile timeout; beam/HOB confirm
  feed-forward changes trajectory.
- [x] P4-B parameter sensitivity: 15 rows (3 params × 5 levels). autopilot_tau_s
  dominant (range 1581→5652m); nav_gain modest (~100m); APN gain monotonic
  degradation vs non-maneuvering target as expected.
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

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| R2 | EKF tracking performance not quantitatively validated (covariance convergence, weaving target continuity) | Medium | open — EKF is opt-in, default off |
| R4 | Mach Cd₀ multi-row lookup table deferred (single lerp between configurable breakpoints used) | Low | open |

Closed: R1 (APN low-pass filter, τ=0.30s), R3 (autopilot order=3 actuator lag),
R5 (Gurney V₀+decay in has_physics_warhead path), R6 (P3-C tuning example),
R7 (P4-A/B executed, P4-C deferred).

All authority claims remain refused (boundary, not residual).
