# A9 High-Fidelity Weapon System — Current Status

Status: `2026-06-16` **accepted_with_residuals**. 15 clusters pass, 11 deferred. P3 integration complete (P3-C 7/7 round-trip, P3-D 47 pre-existing failures / 286 pass). 3 open residuals: R2 (EKF tracking validation), R4 (Mach Cd₀ table), fragment decay. All authority claims refused. Zero regressions vs main.

## What Changed Since Prior Checkpoint

Initial creation. No prior checkpoint exists.

`2026-06-16` P0 revision: aligned PF baseline with PF-R4 (implementation pass)
and PF-R5 (validation pass_with_residuals) completed status. Corrected lethality
chain reference from "9-stage" to the full `RecentEngagementEvents` event surface
(10 event types including `StructuralBreakupEvent`). Added source ledger,
dispatch queue, and acceptance draft documents.

## Maturity Matrix

| Subsystem | Current Fidelity | Target Fidelity | Status |
|-----------|-----------------|-----------------|--------|
| Guidance (G1) | Classical PN + empirical capture | APN with target maneuver compensation | **pass** — apn_target_accel_gain pipeline + feed-forward term; acceptance items pending (APN-vs-PN comparison test, off-state identity check) |
| Seeker (G2) | First-order exponential smoothing | 9-state EKF (Singer model) | **pass** — kalman_seeker.h (EKF engine + body↔world coordinate transforms); use_kalman_seeker in full MissileTuning/JSON/Python pipeline; LOS rates computed from frame-to-frame angle deltas in both detection and coast paths; EKF closing speed uses actual missile velocity |
| Autopilot (G3) | Single first-order lag | Configurable-order transfer function (τ, ζ, 1/2/3) | **partial** — order=1 (legacy lag), order≥2 (state-space filter); order=3 not differentiated from order=2; tuning pipeline complete |
| Proximity Fuze (G4) | PF-R4 surrogate (pass) + PF-R5 validation (pass_with_residuals) | Refined surrogate with mechanism-specific coverage differentiation | **pass** — hit_to_kill coverage penalty + existing PF-R4 preserved |
| Aerodynamics (G5) | Fixed Cd₀ per regime | Configurable Mach breakpoints + power on/off distinction | **pass** — mach_transonic_start/end + cd0_power_on_ratio in full pipeline |
| Warhead (G6) | Kingery-Bulmash proxy / toy inputs | Physics-based fragment/rod/blast model | **partial** — C/M/E fields plumbed (profile/loader/bindings); rod physics opt-in (cap/decay/threshold) when gurney_constant_mps configured; legacy empirical formulas still default (fragment count 18*mass_kg, rod velocity 920+0.16*closure, blast 115*Z^-2); 30 pre-existing test failures in warhead/component surface |
| Integration (G7) | — | Bindings + scenarios + diagnostics | **partial** — bindings updated; scenario JSON loader ready; no new scenario examples yet |

## Evidence Links

| Evidence | Type | Location |
|----------|------|----------|
| Current PN implementation | Code | `src/models/weapons/default_guidance_model.cpp:700-725` |
| Current seeker filter | Code | `src/models/weapons/missile_guidance_math.h:70-84` |
| Current autopilot | Code | `src/models/weapons/default_guidance_model.cpp:740-744` |
| PF-R4 fuze surrogate implementation | Doc | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/proximity_fuze_runtime_implementation_20260616.md` |
| PF-R5 fuze validation | Doc | `docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/validation/pf_r5_proximity_fuze_validation_20260616.md` |
| Lethality chain event types (full surface) | Code | `src/core/engine/engagement_event_types.h` (RecentEngagementEvents) |
| Lethality chain contract | Code | `src/runtime/contracts/engagement_contracts.h` |
| Guidance realism tests | Test | `tests/runtime/air_combat/weapon_guidance_realism/` |
| Source ledger (public data) | Doc | `docs/task/air_combat/a9_high_fidelity_weapon_system/p1_evidence/source_ledger_20260616.md` |
| A2 sealed record | Doc | `docs/task/air_combat/archive/a2_high_fidelity_damage_model/README.md` |
| Realism authority boundary | Standard | `docs/standards/foundation/realism_authority_boundary.zh.md` |

## Residual Register

| ID | Description | Severity | Status |
|----|-------------|----------|--------|
| R1 | Target maneuver prediction (IMM banks) deferred | Minor | held |
| R2 | ECM/EW effects on seeker/fuze deferred | Minor | held |
| R3 | Directional warhead aimpoint optimization deferred | Minor | held |
| R4 | Real-time performance profiling deferred | Minor | held |
| R5 | Navy/ground domain not in scope | Minor | held |
| R6 | Authority promotion not in scope | Blocking | held |
| R7 | All public-source data is non-authoritative | Blocking | held |
| R8 | G4 must not regress PF-R5 residuals (pass_with_residuals) | Blocking | held |

## Next Recommended Action Order

1. Complete P0-B: per-subsystem gap audits (6 audits, read-only).
   For G4 fuze, the gap audit must measure against the PF-R4 surrogate, not the
   pre-PF-R4 nearest-distance proxy.
2. Execute P1-B: define benchmark parameter tables (proxy value → target value).
3. Execute P1-C: map existing test coverage, including PF-R4/PF-R5 test surface.
4. Begin P2 implementation clusters. Recommended order:
   G4 (fuze refinement, lowest risk, builds on PF-R4) → G1 (APN) → G2 (EKF) →
   G5 (aero) → G3 (autopilot) → G6 (warhead).
   See dispatch queue for serialization constraints on shared files.

## Explicit Overclaim Refusals

- ❌ `pk_authority`: NOT claimed. All kill probability outputs are research-grade.
- ❌ `deterministic_fuze_authority`: NOT claimed. Fuze behavior is a non-authoritative surrogate.
- ❌ `effect_scale_authority`: NOT claimed.
- ❌ `component_failure_probability_authority`: NOT claimed.
- ❌ `stock_weapon_truth`: NOT claimed.
- ❌ `real_weapon_pk_authority`: NOT claimed.
- ❌ `research-grade high fidelity` as a completed claim: NOT claimed. P2 waves
  1-3 delivered 10 pass + 4 partial clusters; G2 is partial (EKF has known
  coordinate-frame and pipeline gaps); G6 physics is opt-in (fields plumbed,
  legacy formulas still default). No authority, calibration, or stock truth.
