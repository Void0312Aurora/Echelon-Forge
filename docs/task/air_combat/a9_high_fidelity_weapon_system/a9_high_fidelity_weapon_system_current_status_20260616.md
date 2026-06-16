# A9 High-Fidelity Weapon System — Current Status

Status: `2026-06-16` **accepted_with_residuals**. 23 clusters pass, 5 deferred.
2 open residuals: R2 (EKF tracking validation), R4 (Mach Cd₀ multi-row table).
All authority claims refused. Zero regressions vs main (47 pre-existing failures,
286 passed, 233 subtests passed).

## Maturity Matrix

| Subsystem | Current Fidelity | Target Fidelity | Status |
|-----------|-----------------|-----------------|--------|
| Guidance (G1) | Classical PN + empirical capture | APN with target maneuver compensation | **pass** — apn_target_accel_gain pipeline + feed-forward + low-pass filter (τ=0.30s). P4-A/B validated. |
| Seeker (G2) | First-order exponential smoothing | 9-state EKF (Singer model) | **pass** — kalman_seeker.h + body↔world transforms + use_kalman_seeker pipeline + LOS rates in detection/coast paths + closing speed from actual velocity. Tracking performance not yet quantitatively validated (R2). |
| Autopilot (G3) | Single first-order lag | Configurable-order transfer function (1/2/3) | **pass** — order=1 (legacy lag), order=2 (state-space), order=3 (state-space + actuator lag τ=0.03s). τ/ζ in full pipeline. |
| Proximity Fuze (G4) | PF-R4 surrogate (pass) + PF-R5 validation (pass_with_residuals) | Refined surrogate + coverage_profile | **pass** — hit_to_kill coverage penalty; coverage_profile field in FuzeProfile; PF-R4 preserved. |
| Aerodynamics (G5) | Fixed Cd₀ per regime | Configurable Mach breakpoints + power on/off | **pass** — mach_transonic_start/end + cd0_power_on_ratio in full pipeline. Multi-row Cd₀ table deferred (R4). |
| Warhead (G6) | Kingery-Bulmash proxy / toy inputs | Physics-based fragment/rod model | **pass** — C/M/E fields + Gurney V₀ + fragment decay V(s) + rod cap 1150 m/s + cutting threshold 610 m/s (all opt-in via has_physics_warhead). Legacy empirical formulas preserved as default. |
| Integration (G7) | — | Bindings + examples + diagnostics | **pass** — P3-C 7/7 fields round-trip; P3-D zero regressions; P4-A/P4-B validation artifacts retained. |

## Residual Register

| ID | Description | Severity | Blocks acceptance? |
|----|-------------|----------|-------------------|
| R2 | EKF tracking performance not quantitatively validated (covariance convergence, weaving target continuity) | Medium | No — EKF is opt-in, default off |
| R4 | Mach Cd₀ multi-row lookup table deferred; current implementation uses single lerp between configurable breakpoints | Low | No — single-lerp is physically plausible |
| — | All authority claims remain refused | Blocking | N/A — boundary, not residual |

Closed residuals: R1 (APN estimator noise — low-pass filter added), R3 (autopilot order=3 — actuator lag added), R5 (Gurney not active — has_physics_warhead path implemented), fragment decay (atmospheric model added).

## Open Deferred Clusters

| Cluster | Reason |
|---------|--------|
| P1-B | Benchmark parameter tables — covered by gap audit + source ledger |
| P1-C | Test coverage map — covered by acceptance doc + P3-D baseline |
| P2-F2 | Rod expansion kinematics — static approximation sufficient for <10m engagements |
| P3-B | Debug runtime diagnostics — core fields already exposed in bindings |
| P4-C | A/B comparison summary — P4-A CSV + P4-B sensitivity provide equivalent evidence |

## Evidence Links

| Evidence | Type | Location |
|----------|------|----------|
| Source ledger | Doc | p1_evidence/source_ledger_20260616.md (14 entries, full admission fields) |
| Gap audit | Doc | p1_evidence/p0b_gap_audit_summary_20260616.md |
| Acceptance review | Doc | a9_high_fidelity_weapon_system_acceptance_20260616.md |
| P4-A geometry sweep | Data | p4_validation/p4a_apn_geometry_sweep_20260616.{py,csv} |
| P4-B sensitivity sweep | Data | p4_validation/p4b_sensitivity_sweep_20260616.{py,csv} |
| P3-C tuning round-trip | Script | p3_integration/p3c_a9_tuning_example.py |
| P3-D regression | Run | 47 failed (pre-existing), 286 passed, 233 subtests passed |
| C++ implementation | Code | 12 files modified, kalman_seeker.h (new, 295 lines) |

## Explicit Overclaim Refusals

- ❌ `pk_authority` = false
- ❌ `deterministic_fuze_authority` = false
- ❌ `effect_scale_authority` = false
- ❌ `component_failure_probability_authority` = false
- ❌ `real_weapon_pk_authority` = false
- ❌ `stock_weapon_truth` = false
- ❌ No AIM-120C-specific parameter claims
- ❌ No classified, ITAR, or FOUO data
