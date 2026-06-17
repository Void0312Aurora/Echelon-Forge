# A9 High-Fidelity Weapon System — Archive Record

Status: `accepted` on `2026-06-17` (R2 and R4 closed in follow-up; 5 clusters remain explicitly deferred).
Source: [../../a9_high_fidelity_weapon_system/](../../a9_high_fidelity_weapon_system/README.md)
Branch: `feature/a9-high-fidelity-weapon-system` (13 commits, zero regressions vs main).

## Scope Delivered

Six air-combat weapon subsystems upgraded from engineering-proxy fidelity
toward research-grade fidelity:

| Subsystem | Key Deliverable |
|-----------|----------------|
| G1 — APN Guidance | Augmented PN + low-pass filtered acceleration estimator (τ=0.30s) |
| G2 — Kalman Seeker | 9-state Singer EKF in world Cartesian; `use_kalman_seeker` pipeline |
| G3 — Autopilot | Configurable-order (1/2/3) with state-space filter + actuator lag |
| G4 — Proximity Fuze | `hit_to_kill` coverage penalty; `FuzeProfile.coverage_profile` |
| G5 — Aerodynamics | Mach-indexed Cd₀/k(M) tables + power-on base-drag reduction |
| G6 — Warhead | Gurney V₀ + fragment decay + rod cap/threshold (opt-in via C/M/E fields) |

## Cluster Summary

23 pass, 5 deferred, 0 partial (28 total).

## Residuals

No residual remains open.

| ID | Description | Status |
|----|-------------|--------|
| R2 | EKF tracking performance quantitatively validated | closed |
| R4 | Mach Cd₀/k(M) multi-row lookup tables implemented with engineering-proxy values | closed |

Both closures remain non-authoritative and not weapon-specific.

## Deferred Clusters

| Cluster | Reason |
|---------|--------|
| P1-B | Benchmark parameter tables — covered by gap audit + source ledger |
| P1-C | Test coverage map — covered by acceptance doc + P3-D baseline |
| P2-F2 | Rod expansion kinematics — static approximation sufficient for <10m |
| P3-B | Debug runtime diagnostics — core fields already exposed in bindings |
| P4-C | A/B comparison summary — P4-A/B provide equivalent evidence |

## Authority Boundary

All of the following remain `false`:
`pk_authority`, `deterministic_fuze_authority`, `effect_scale_authority`,
`component_failure_probability_authority`, `real_weapon_pk_authority`,
`stock_weapon_truth`.

No AIM-120C-specific parameters. No classified, ITAR, or FOUO data.

## Evidence Artifacts

| Artifact | Location (relative to A9 subproject) |
|----------|--------------------------------------|
| Source ledger (14 entries) | `p1_evidence/source_ledger_20260616.md` |
| Gap audit (6 subsystems) | `p1_evidence/p0b_gap_audit_summary_20260616.md` |
| Acceptance checklist (49 items) | `a9_high_fidelity_weapon_system_acceptance_20260616.md` |
| P4-A geometry sweep (12 rows) | `p4_validation/p4a_apn_geometry_sweep_20260616.{py,csv}` |
| P4-B sensitivity sweep (15 rows) | `p4_validation/p4b_sensitivity_sweep_20260616.{py,csv}` |
| Mach aero proxy table | `p4_validation/mach_aero_table_proxy_20260617.md` |
| EKF tracking validation | `p4_validation/ekf_tracking_validation_20260617.md`; `src/tests/test_kalman_seeker.cpp` |
| P3-C tuning round-trip (11/11) | `p3_integration/p3c_a9_tuning_example.py` |
| C++ implementation | A9 guidance/seeker/autopilot/fuze/aero/warhead implementation, including `kalman_seeker.h` |

## C++ Files Modified

| File | Subsystem |
|------|-----------|
| `src/components/combat/common/weapon_common.h` | G1-G6 struct fields |
| `src/models/weapons/missile_guidance_types.h` | G1/G3/G5 constants |
| `src/models/weapons/missile_guidance_math.h` | — (referenced, not modified) |
| `src/models/weapons/default_guidance_model.cpp` | G1/G3/G5 logic |
| `src/models/weapons/kalman_seeker.h` | G2 (new, 295 lines) |
| `src/models/weapons/detail/default_effects_warhead_detail.inc` | G6 physics |
| `src/systems/combat/damage_system_common.h` | G4 fuze logic |
| `src/core/engine/simulation_kernel_missile_tuning.h` | G1-G6 config |
| `src/core/engine/simulation_kernel_weapon_release_service.cpp` | Pipeline wiring |
| `src/content/unit_definition.h` | JSON schema |
| `src/content/unit_definition_loader.cpp` | JSON deserialization |
| `src/interfaces/python/bindings_core.cpp` | Python bindings |
| `src/runtime/contracts/engagement_contracts.h` | — (referenced, not modified) |
| `src/core/engine/engagement_event_types.h` | — (referenced, not modified) |

## Test Regression

P3-D: 47 pre-existing failures (same as main, skipping crashing 1v1 fixture),
286 passed, 233 subtests passed. Zero regressions introduced by A9 branch.
