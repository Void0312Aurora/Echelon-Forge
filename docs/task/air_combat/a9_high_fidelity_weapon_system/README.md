# A9 High-Fidelity Weapon System

Status: `2026-06-16` planning / P0 boundary freeze. No implementation has started.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent air-combat task index: [../README.md](../README.md)
- A2 sealed damage-model record: [../archive/a2_high_fidelity_damage_model/README.md](../archive/a2_high_fidelity_damage_model/README.md)
- A2 follow-on proximity fuze realism (PF-R4 pass, PF-R5 pass_with_residuals):
  [../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/README.md](../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/README.md)
- A8 damage effect chain: [../archive/a8_damage_effect_chain/README.md](../archive/a8_damage_effect_chain/README.md)
- Agent subproject standard: [../../../agent/rules/subproject_creation_standard.md](../../../agent/rules/subproject_creation_standard.md)
- Realism authority boundary: [../../../standards/foundation/realism_authority_boundary.zh.md](../../../standards/foundation/realism_authority_boundary.zh.md)
- Public-source admission: [../../../standards/foundation/public_data_source_admission.zh.md](../../../standards/foundation/public_data_source_admission.zh.md)
- Current guidance model: [../../../../src/models/weapons/default_guidance_model.cpp](../../../../src/models/weapons/default_guidance_model.cpp)
- Current guidance types: [../../../../src/models/weapons/missile_guidance_types.h](../../../../src/models/weapons/missile_guidance_types.h)
- Current damage system: [../../../../src/systems/combat/damage_system_common.h](../../../../src/systems/combat/damage_system_common.h)
- Current missile tuning: [../../../../src/core/engine/simulation_kernel_missile_tuning.h](../../../../src/core/engine/simulation_kernel_missile_tuning.h)
- Current weapon release: [../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp](../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- Lethality chain contract (C++): [../../../../src/runtime/contracts/engagement_contracts.h](../../../../src/runtime/contracts/engagement_contracts.h)
- Lethality chain contract (Python): [../../../../tools/diagnostics/lethality_chain_contract.py](../../../../tools/diagnostics/lethality_chain_contract.py)
- Engagement event types: [../../../../src/core/engine/engagement_event_types.h](../../../../src/core/engine/engagement_event_types.h)
- Forward-looking weapons planning: [../../../forward/weapons/weapons_engagement.md](../../../forward/weapons/weapons_engagement.md)
- Current guidance tests: [../../../../tests/runtime/air_combat/weapon_guidance_realism/](../../../../tests/runtime/air_combat/weapon_guidance_realism/)

## Purpose

The current air-combat weapon system operates at **engineering-proxy fidelity**
across most subsystems. The guidance law is classical proportional navigation
(PN) with an empirical terminal capture augmentation, the seeker uses
first-order exponential smoothing filters, the autopilot is a single first-order
lag, and aerodynamics use fixed drag coefficients. The proximity fuze surrogate
(PF-R4/PF-R5) has already been upgraded from a pure nearest-distance gate to a
sensor-opportunity / detection / trigger layered model, but remains
non-authoritative.

This subproject **plans** to upgrade each remaining proxy subsystem **toward
research-grade fidelity** while remaining strictly **non-authoritative** and
**non-weapon-specific**:

- **Guidance (G1)**: Plan to upgrade from classical PN to Augmented Proportional
  Navigation (APN) with target maneuver compensation derived from optimal control
  / ZEM formulation.
- **Seeker/tracker (G2)**: Plan to replace first-order exponential smoothing with
  a 9-state extended Kalman filter (position, velocity, acceleration in Cartesian
  frame) with Singer-model process noise.
- **Autopilot (G3)**: Plan to replace the single first-order lag with a
  three-loop (rate / stability / acceleration) topology parameterized by
  closed-loop time constant τ and damping ζ.
- **Proximity fuze (G4)**: Refine the already-implemented PF-R4 surrogate
  (currently at `pass`) with mechanism-specific coverage differentiation and
  additional diagnostic fields. PF-R5 matrix validation is `pass_with_residuals`;
  G4 must not regress or widen those residuals.
- **Warhead lethality (G6)**: Plan to refine blast-fragmentation and
  continuous-rod models with physics-based fragment velocity (Gurney equations),
  fragment decay, and directional efficiency factors.
- **Aerodynamics (G5)**: Plan to replace fixed `Cd₀` constants with
  Mach-dependent drag tables, power-on/power-off base-drag distinction, and
  proper induced-drag formulation.

Every planned upgrade must preserve the full lethality chain event surface
defined by `RecentEngagementEvents` in
[engagement_event_types.h](../../../../src/core/engine/engagement_event_types.h):
`NearestApproachEvent`, `FuzeEvaluationEvent`, `WarheadMechanismEvent`,
`SpatialCoverageEvent`, `ComponentLoadEvent`, `ComponentDamageEvent`,
`PlatformConsequenceEvent`, `StructuralBreakupEvent`,
`LifecycleTransitionEvent`, and `TrainingProjectionEvent`. No upgraded
subsystem claims `pk_authority`, `deterministic_fuze_authority`,
`effect_scale_authority`, or stock weapon truth.

## Current State

| Area | Status | Evidence | Boundary |
|------|--------|----------|----------|
| A2 authority | retained / sealed | [../archive/a2_high_fidelity_damage_model/README.md](../archive/a2_high_fidelity_damage_model/README.md) | A2 remains non-authoritative for stock weapon truth, Pk, and deterministic fuze. |
| Classical PN guidance | implemented / proxy | [default_guidance_model.cpp:700-725](../../../../src/models/weapons/default_guidance_model.cpp#L700-L725) | PN with empirical capture term; no target maneuver compensation. |
| First-order seeker filter | implemented / proxy | [missile_guidance_math.h:70-84](../../../../src/models/weapons/missile_guidance_math.h#L70-L84) | α-β level smoothing; no covariance propagation, no acceleration state. |
| Single-lag autopilot | implemented / proxy | [default_guidance_model.cpp:740-744](../../../../src/models/weapons/default_guidance_model.cpp#L740-L744) | First-order lag τ=0.12s; no rate/stability inner loops. |
| PF-R4 fuze surrogate | **implemented / pass** | [PF-R4 implementation](../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/proximity_fuze_runtime_implementation_20260616.md); touched 13 files across C++, Python bindings, tests, and diagnostics | Surrogate is non-authoritative explainability, not real fuze calibration. |
| PF-R5 fuze validation | **pass_with_residuals** | [PF-R5 validation](../a2_high_fidelity_damage_model/missile_lethality_proximity_fuze_realism/validation/pf_r5_proximity_fuze_validation_20260616.md); CSV, JSON, heatmap retained | Validates surrogate gating trends only; live guidance offsets are not pure detonation-point symmetry tests. |
| A9 G4 fuze refinement scope | planned | This README; [task clusters](a9_high_fidelity_weapon_system_task_clusters_20260616.md) cluster P2-D | G4 refines existing surrogate (mechanism coverage differentiation, additional diagnostics); does NOT re-implement PF-R3. |
| Fixed-Cd aerodynamics | implemented / proxy | [missile_guidance_types.h:17-18](../../../../src/models/weapons/missile_guidance_types.h#L17-L18) | Single Cd₀ per regime; no Mach table, no power-on/off distinction. |
| Blast-frag warhead | implemented / candidate | [default_effects_warhead_detail.inc](../../../../src/models/weapons/detail/default_effects_warhead_detail.inc) | Kingery-Bulmash proxy; mass/radius are toy inputs. |
| Continuous-rod warhead | implemented / candidate | MLF-4 evidence pack | Rod cutting band modeled; not calibrated. |
| Web research source ledger | collected / non-authoritative | [p1_evidence/source_ledger_20260616.md](p1_evidence/source_ledger_20260616.md) | Public sources only; no classified/ITAR parameters. |

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

| Phase | Goal | Entry condition | Exit condition | Status |
|-------|------|-----------------|----------------|--------|
| `P0 Boundary` | Freeze scope, authority, and non-goals. Link parent docs. Align PF baseline with PF-R4/PF-R5 completed status. | User request for high-fidelity weapon subproject. | README, task clusters, current status, dispatch queue, acceptance draft, source ledger, and archive boundary exist. Parent README links a9. PF status correctly reflects PF-R4 pass / PF-R5 pass_with_residuals. | active |
| `P1 Evidence` | Complete per-subsystem gap audit and benchmark parameter tables. Collect web research source ledger. Map existing test coverage. | P0 exists with PF baseline aligned. | 6 gap audits, benchmark parameter tables, test coverage map, and source ledger are documented. | planned |
| `P2 Implementation` | Implement G1-G6 upgrades in C++ models and ECS components. | P1 evidence exists. Gate review per subsystem passes. | All six model upgrades compile, pass focused unit tests, and preserve existing contract tests. G4 does not regress PF-R5 residuals. | planned |
| `P3 Integration` | Wire upgrades into MissileTuning, Python bindings, scenario JSON, and diagnostic probes. | P2 passes per-subsystem gates. | Integration tests pass; existing air_combat scenario smoke tests green. | planned |
| `P4 Validation` | Run matrix validation: engagement geometry sweep, subsystem parameter sensitivity, comparison against proxy baseline. | P3 integration tests pass. | Validation matrix artifacts (CSV, heatmaps, summary) retained. Residuals documented. | planned |
| `P5 Closure` | Sync parent docs, acceptance gate, residual register, and archive. | P4 validation complete with residuals. | Acceptance closeout records final surrogate boundary. Parent README updated. | planned |

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

Current outputs (P0):

- This README and [Chinese companion](README.zh.md).
- [Source ledger](p1_evidence/source_ledger_20260616.md): public-source parameter
  tables for all 6 subsystems with URL, retrieval date, and non-authoritative
  admission annotations.
- [Task clusters](a9_high_fidelity_weapon_system_task_clusters_20260616.md):
  28 clusters across 6 phases (2 P0 + 3 P1 + 14 P2 + 4 P3 + 3 P4 + 2 P5).
- [Current status](a9_high_fidelity_weapon_system_current_status_20260616.md):
  maturity matrix, evidence links, residual register.
- [Dispatch queue](a9_high_fidelity_weapon_system_dispatch_queue_20260616.md):
  worker packet state and serialization constraints.
- [Acceptance draft](a9_high_fidelity_weapon_system_acceptance_20260616.md):
  per-subsystem checklist with forbidden-claim assertions.

Planned outputs (P1-P5):

- Per-subsystem current-runtime gap audit (6 audits: guidance, seeker, autopilot,
  fuze-refinement, aero, warhead).
- Benchmark parameter tables with proxy-value → target-value mappings.
- Test coverage map with gap prioritization.
- C++ model implementations for G1-G6 with focused unit tests.
- Updated `MissileTuning` struct with new configurable parameters.
- Updated Python bindings exposing new tuning knobs and runtime diagnostics.
- Scenario config examples exercising the new fidelity parameters.
- Validation matrix: engagement geometry sweep (head-on, tail-chase, beam, high
  off-boresight), parameter sensitivity heatmaps, proxy-vs-upgraded comparison
  artifacts.
- Acceptance closeout record.

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

## Residuals And Next Steps

Anticipated residuals:

- **Target maneuver prediction**: IMM/CV/CA/CT filter banks for predicting target
  acceleration rather than estimating it from measurements alone. Deferred — the
  Kalman filter provides smoothed estimates only.
- **ECM/EW interaction**: Seeker and fuze performance degradation under jamming.
  Deferred — requires separate EW subsystem maturity.
- **Directional warhead aimpoint optimization**: PIOS-style 3D fragment steering
  based on IR seeker aimpoint data. Deferred — requires classified-quality sensor
  fusion.
- **Real-time performance**: Kalman filter and three-loop autopilot impose
  additional CPU cost per missile per tick. Profiling and optimization deferred
  until integration benchmarks.
- **Navy/ground domain**: These upgrades are air-combat only. Navy and ground
  lethality chains remain placeholder / deferred.
- **Authority promotion**: All upgrades remain research-grade and
  non-authoritative. Authority promotion requires independent review, source
  authority closeout, and explicit acceptance under the realism authority boundary
  standard.

## Archive

Archive index: [archive/README.md](archive/README.md). No historical records have
been archived yet.
