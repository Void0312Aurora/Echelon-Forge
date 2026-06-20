# A9 High-Fidelity Weapon System

Status: `2026-06-20` **archived / accepted** with 5 explicitly deferred clusters and 0 open residuals. R2 EKF tracking validation is closed by focused C++ regression coverage. Zero regressions vs main. See [acceptance](a9_high_fidelity_weapon_system_acceptance_20260616.md) for full checklist.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task index: [../../README.md](../../README.md)
- A2 sealed damage-model record: [../a2_high_fidelity_damage_model/README.md](../a2_high_fidelity_damage_model/README.md)
- A2 follow-on proximity fuze realism (PF-R4 pass, PF-R5 pass_with_residuals):
  [../../a2_high_fidelity_damage_model/archive/missile_lethality_proximity_fuze_realism/README.md](../../a2_high_fidelity_damage_model/archive/missile_lethality_proximity_fuze_realism/README.md)
- A8 damage effect chain: [../a8_damage_effect_chain/README.md](../a8_damage_effect_chain/README.md)
- Agent subproject standard: [../../../../agent/rules/subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)
- Realism authority boundary: [../../../../standards/foundation/realism_authority_boundary.zh.md](../../../../standards/foundation/realism_authority_boundary.zh.md)
- Public-source admission: [../../../../standards/foundation/public_data_source_admission.zh.md](../../../../standards/foundation/public_data_source_admission.zh.md)
- Current guidance model: [../../../../../src/models/weapons/default_guidance_model.cpp](../../../../../src/models/weapons/default_guidance_model.cpp)
- Current guidance types: [../../../../../src/models/weapons/missile_guidance_types.h](../../../../../src/models/weapons/missile_guidance_types.h)
- Current damage system: [../../../../../src/systems/combat/damage_system_common.h](../../../../../src/systems/combat/damage_system_common.h)
- Current missile tuning: [../../../../../src/core/engine/simulation_kernel_missile_tuning.h](../../../../../src/core/engine/simulation_kernel_missile_tuning.h)
- Current weapon release: [../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- Lethality chain contract (C++): [../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)
- Lethality chain contract (Python): [../../../../../tools/diagnostics/lethality_chain_contract.py](../../../../../tools/diagnostics/lethality_chain_contract.py)
- Engagement event types: [../../../../../src/core/engine/engagement_event_types.h](../../../../../src/core/engine/engagement_event_types.h)
- Forward-looking weapons planning: [../../../../forward/weapons/weapons_engagement.md](../../../../forward/weapons/weapons_engagement.md)
- Current guidance tests: [../../../../../tests/runtime/air_combat/weapon_guidance_realism/](../../../../../tests/runtime/air_combat/weapon_guidance_realism/)

## Purpose

This subproject upgrades six air-combat weapon subsystems from
**engineering-proxy fidelity toward research-grade fidelity**, while remaining
strictly **non-authoritative** and **non-weapon-specific**:

- **G1 — APN Guidance**: Augmented Proportional Navigation with
  configurable navigation ratio, target-acceleration feed-forward term,
  and low-pass-filtered bearing-acceleration estimator (τ=0.30s).
- **G2 — Kalman Filter Seeker**: 9-state Singer-model EKF in world
  Cartesian coordinates with body↔world transforms; configurable via
  `use_kalman_seeker` in MissileTuning/JSON/Python.
- **G3 — Configurable-Order Autopilot**: order=1 (legacy lag), order=2
  (state-space filter), order=3 (state-space + actuator lag τ=0.03s);
  configurable damping ζ.
- **G4 — Fuze Surrogate Refinement**: `hit_to_kill` coverage penalty;
  `coverage_profile` field in FuzeProfile; PF-R4 surrogate preserved.
- **G5 — Mach-Dependent Aerodynamics**: configurable transonic breakpoints
  (`mach_transonic_start`/`_end`); power-on base-drag reduction
  (`cd0_power_on_ratio`, default 0.90); Mach-indexed Cd₀ and k(M)
  engineering-proxy tables.
- **G6 — Physics-Based Warhead** (opt-in): Gurney fragment velocity,
  atmospheric fragment decay, rod weld cap (1,150 m/s), cutting threshold
  (610 m/s); activated when `gurney_constant_mps` + `explosive_mass_kg`
  + `case_mass_kg` are configured. Legacy empirical formulas preserved as default.

All upgrades preserve the full lethality chain event surface
(`NearestApproachEvent` through `TrainingProjectionEvent`, including
`StructuralBreakupEvent`). No subsystem claims `pk_authority`,
`deterministic_fuze_authority`, `effect_scale_authority`, or stock weapon truth.

## Current State

| Subsystem | Status | Key Artifacts |
|-----------|--------|---------------|
| G1 — APN Guidance | **pass** | `default_guidance_model.cpp`: APN feed-forward + low-pass filter (τ=0.30s). Pipeline: 8 files. |
| G2 — Kalman Seeker | **pass** | `kalman_seeker.h` (295 lines, new). Body↔world transforms. `use_kalman_seeker` in full pipeline. |
| G3 — Autopilot | **pass** | `default_guidance_model.cpp`: order=1/2/3. State-space filter + actuator lag. |
| G4 — Proximity Fuze | **pass** | `damage_system_common.h`: hit_to_kill penalty. `FuzeProfile.coverage_profile`. PF-R4 preserved. |
| G5 — Aerodynamics | **pass** | `default_guidance_model.cpp`: Mach-indexed Cd₀/k(M) tables + power-on ratio. Pipeline complete. |
| G6 — Warhead | **pass** | `default_effects_warhead_detail.inc`: Gurney V₀ + fragment decay + rod cap/threshold (opt-in). C/M/E fields plumbed. |
| G7 — Integration | **pass** | P3-C 7/7 round-trip. P3-D zero regressions. P4-A/B validation artifacts retained. |
| A2 authority | retained / sealed | A2 remains non-authoritative for stock weapon truth, Pk, and deterministic fuze. |

## Scope

In scope:

- **G1 — APN Guidance**: Implement augmented proportional navigation with target
  acceleration feed-forward. Derive from optimal control / ZEM formulation. Add
  configurable navigation ratio N' and target-accel gain parameter.
- **G2 — Kalman Filter Seeker**: Implement a 9-state EKF tracker (relative position,
  velocity, acceleration in Cartesian) with Singer-model process noise and
  configurable angle/range measurement noise. Replace first-order smoothing when
  `use_kalman_seeker = true`; preserve existing smoothing as fallback.
- **G3 — Three-Loop Autopilot**: Model the rate / stability / acceleration topology
  as a configurable second-order or third-order transfer function with closed-loop
  time constant τ and damping ζ. Preserve G-limiting and rate saturation.
- **G4 — Fuze Surrogate Refinement**: Build on the completed PF-R4 surrogate.
  Add mechanism-specific coverage differentiation between `blast_fragmentation`
  and `continuous_rod`. Add any missing diagnostic fields identified during P0-B
  gap audit. Must not regress PF-R5 validation residuals.
- **G5 — Mach-Dependent Aerodynamics**: Replace fixed Cd₀ with a Mach-indexed
  lookup table, add power-on/power-off base-drag distinction, and proper induced-drag
  formulation k(M)·CL².
- **G6 — Physics-Based Warhead Refinements**: Add Gurney fragment velocity,
  atmospheric fragment decay, directional fragmentation efficiency factor, and
  continuous-rod expansion kinematics with weld-limited velocity cap.
- **G7 — Integration & Diagnostics**: Wire all upgrades into the existing
  `MissileTuning` struct, guidance/damage systems, Python bindings, scenario configs,
  and diagnostic probes.

Out of scope:

- Claiming `pk_authority`, `deterministic_fuze_authority`, or stock weapon truth.
- AIM-120C-specific classified parameters, ITAR-restricted data, or real fuze
  constants.
- Navy or ground domain weapon effects (air-combat only).
- Target maneuver prediction (IMM banks, adaptive filtering) — deferred to future.
- ECM/EW effects on seeker or fuze performance — deferred to future.
- Real-time hardware-in-the-loop constraints.
- Training reward redesign (the reward surface consumes lethality facts but this
  subproject does not tune for RL).
- Reopening sealed A2, MLF-2, MLF-3, MLF-4, or MLF-5 packages.
- Re-implementing PF-R3 from scratch (PF-R4/PF-R5 are already complete).

## Phase Plan

| Phase | Goal | Status |
|-------|------|--------|
| `P0 Boundary` | Freeze scope, authority, non-goals. Link parent docs. | pass |
| `P1 Evidence` | Per-subsystem gap audit, source ledger, test coverage map. | pass (P1-A); P1-B/C deferred |
| `P2 Implementation` | Implement G1-G6 upgrades in C++ models and ECS components. | pass (14/14 clusters) |
| `P3 Integration` | Wire upgrades into MissileTuning, Python bindings, scenario config. | pass |
| `P4 Validation` | Engagement geometry sweep, parameter sensitivity. | pass (P4-A/B); P4-C deferred |
| `P5 Closure` | Acceptance closeout, parent docs sync, residual register. | pass |

## Task Clusters

- Task cluster plan:
  [a9_high_fidelity_weapon_system_task_clusters_20260616.md](a9_high_fidelity_weapon_system_task_clusters_20260616.md)
- Current status:
  [a9_high_fidelity_weapon_system_current_status_20260616.md](a9_high_fidelity_weapon_system_current_status_20260616.md)
- Dispatch queue:
  [a9_high_fidelity_weapon_system_dispatch_queue_20260616.md](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md)
- Acceptance draft:
  [a9_high_fidelity_weapon_system_acceptance_20260616.md](a9_high_fidelity_weapon_system_acceptance_20260616.md)

## Outputs And Evidence

- [Source ledger](p1_evidence/source_ledger_20260616.md): 14 entries with full
  admission fields per `public_data_source_admission.zh.md`.
- [Gap audit](p1_evidence/p0b_gap_audit_summary_20260616.md): 6-subsystem
  proxy-vs-target comparison.
- [Acceptance](a9_high_fidelity_weapon_system_acceptance_20260616.md): 49-item
  checklist, 9-entry residual register.
- [P4-A geometry sweep](p4_validation/p4a_apn_geometry_sweep_20260616.py):
  12 data points (4 geometries × 3 APN gain levels).
- [P4-B sensitivity sweep](p4_validation/p4b_sensitivity_sweep_20260616.py):
  15 data points (3 params × 5 levels).
- [Mach aero proxy table validation](p4_validation/mach_aero_table_proxy_20260617.md):
  Cd₀(M) and k(M) engineering-proxy table values, validation commands, and
  non-authoritative boundary.
- [EKF tracking validation](p4_validation/ekf_tracking_validation_20260617.md):
  R2 closure evidence for covariance convergence, dropout/reacquire recovery,
  and weaving-target track continuity.
- [P3-C tuning example](p3_integration/p3c_a9_tuning_example.py):
  11/11 A9 fields round-trip verified.
- C++ implementation: 12 files modified, `kalman_seeker.h` (295 lines, new).
  13 new configurable parameters across MissileTuning/WarheadProfile/FuzeProfile.

## Acceptance Gate

This subproject can be marked `accepted` only when:

- All six G1-G6 model upgrades compile and pass focused subsystem tests.
- G4 does not regress PF-R4 surrogate behavior or widen PF-R5 validation
  residuals.
- Existing guidance realism tests (`tests/runtime/air_combat/weapon_guidance_realism/`)
  continue to pass or are updated with documented rationale.
- The full lethality chain event surface (`NearestApproachEvent`,
  `FuzeEvaluationEvent`, `WarheadMechanismEvent`, `SpatialCoverageEvent`,
  `ComponentLoadEvent`, `ComponentDamageEvent`, `PlatformConsequenceEvent`,
  `StructuralBreakupEvent`, `LifecycleTransitionEvent`,
  `TrainingProjectionEvent`) is preserved and every event type remains
  observable.
- APN guidance demonstrably reduces miss distance against maneuvering targets
  compared to classical PN baseline.
- Kalman filter tracker shows improved track continuity and covariance convergence
  compared to first-order smoothing baseline.
- Fuze surrogate already emits `sensor_opportunity_source`, `target_detected`,
  `target_detection_confidence`, and `detonation_point_source` diagnostic fields
  (PF-R4); G4 refinement adds mechanism-specific coverage differentiation.
- Mach-dependent aero table produces physically plausible speed profiles across
  the subsonic-transonic-supersonic envelope.
- Warhead fragment velocity follows Gurney equation, and continuous-rod velocity is
  capped at weld-limited threshold (<1,150 m/s).
- Validation matrix CSV, summary, and heatmaps are retained under this subproject.
- Parent A2 and air_combat docs continue to reject `pk_authority`,
  `deterministic_fuze_authority`, and stock weapon truth.
- All public-source data is annotated with source URL, retrieval date, and
  non-authoritative admission in the source ledger.

Detailed acceptance checklist: [a9_high_fidelity_weapon_system_acceptance_20260616.md](a9_high_fidelity_weapon_system_acceptance_20260616.md).

## Residuals

| ID | Description | Status |
|----|-------------|--------|
| R2 | EKF tracking performance quantitatively validated by focused C++ tests | closed |
| R4 | Mach Cd₀/k(M) multi-row lookup tables implemented with engineering-proxy values | closed |

Closed: R1 (APN filter), R2 (EKF quantitative validation), R3 (autopilot order=3),
R4 (Mach tables), R5 (Gurney), fragment decay.

All authority claims (`pk_authority`, `deterministic_fuze_authority`,
`effect_scale_authority`, `component_failure_probability_authority`,
`real_weapon_pk_authority`, `stock_weapon_truth`) remain refused.
No AIM-120C-specific parameters. No classified/ITAR/FOUO data.

## Archive

This is the physical archive packet for the completed A9 subproject. The
parent registry entry is
[../../archive_registry.md](../../archive_registry.md), and the compact closure
record is [archive_record_20260617.md](archive_record_20260617.md).
