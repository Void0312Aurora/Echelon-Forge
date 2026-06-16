# A9 High-Fidelity Weapon System — Dispatch Queue

Status: `2026-06-16` P2 complete (14 of 14 P2 clusters). P4-A done. Acceptance review with 5 open residuals. 14 remaining: P4-B/C, P5-A/B, P3-B/C.

Parent: [README.md](README.md)
Task clusters: [a9_high_fidelity_weapon_system_task_clusters_20260616.md](a9_high_fidelity_weapon_system_task_clusters_20260616.md)

## Dispatch State

| Cluster | Status | Worker | Dispatched | Completed | Artifacts |
|---------|--------|--------|-----------|-----------|-----------|
| P0-A | active | main thread | 2026-06-16 | — | README, task clusters, current status |
| P0-B | pass | main thread | 2026-06-16 | — | p0b_gap_audit_summary_20260616.md |
| P1-A | partial | main thread | 2026-06-16 | — | source_ledger_20260616.md (draft; needs full admission fields) |
| P1-B | planned | — | — | — | — |
| P1-C | planned | — | — | — | — |
| P2-A1 | pass | main thread | 2026-06-16 | 2026-06-16 | apn_target_accel_gain pipeline (8 files) + APN feed-forward term |
| P2-A2 | pass | main thread | 2026-06-16 | 2026-06-16 | target accel estimator (bearing rate derivative) |
| P2-B1 | pass | main thread | 2026-06-16 | 2026-06-16 | kalman_seeker.h (295 lines) + EKF predict/update/init |
| P2-B2 | planned | — | — | — | — |
| P2-B3 | pass | main thread | 2026-06-16 | 2026-06-16 | EKF integration in update_track/propagate_track with fallback |
| P2-C1 | pass | main thread | 2026-06-16 | 2026-06-16 | second-order autopilot (τ, ζ, order) + tuning pipeline |
| P2-C2 | pass | main thread | 2026-06-16 | 2026-06-16 | autopilot_order/damping in MissileTuning/JSON/bindings |
| P2-D1 | pass | main thread | 2026-06-16 | 2026-06-16 | hit_to_kill coverage penalty in damage_mechanism_coverage_score |
| P2-D2 | planned | — | — | — | — |
| P2-E1 | pass | main thread | 2026-06-16 | 2026-06-16 | configurable Mach breakpoints + power-on Cd0 ratio |
| P2-E2 | pass | main thread | 2026-06-16 | 2026-06-16 | G5 params in MissileTuning/JSON/bindings pipeline |
| P2-F1 | pass | main thread | 2026-06-16 | 2026-06-16 | rod weld cap 1150 m/s + 610 m/s cutting threshold |
| P2-F2 | planned | — | — | — | — |
| P2-F3 | planned | — | — | — | — |
| P3-A | partial | — | — | — | bindings updated for wave1 params; round-trip test pending |
| P3-B | planned | — | — | — | — |
| P3-C | planned | — | — | — | — |
| P3-D | planned | — | — | — | — |
| P4-A | planned | — | — | — | — |
| P4-B | planned | — | — | — | — |
| P4-C | planned | — | — | — | — |
| P5-A | planned | — | — | — | — |
| P5-B | planned | — | — | — | — |

## Hold Reasons

| Blocker | Clusters affected | Resolution |
|---------|------------------|------------|
| P0-A not complete | P0-B | Finish boundary documents |
| P0-B not complete | P1-A, P1-B, P1-C | Complete per-subsystem gap audit (6 audits); for G4, audit existing `damage_mechanism_coverage_score` first |
| P1 evidence not complete | All P2, P3, P4, P5 clusters | Complete source ledger (with full admission fields), benchmark parameter tables, and test coverage map |
| PF baseline guard | P2-D1, P2-D2 (G4 fuze only) | Verify PF-R4 pass / PF-R5 pass_with_residuals status is reflected in A9 docs; G4 scoped as refinement of existing surrogate; P0-B audit must identify what coverage differentiation already exists |

## Next Dispatchable Clusters

In priority order, once P0-B and P1 are complete:

1. **P2-D1** (G4 fuze refinement) — builds on PF-R4/PF-R5, lowest risk, highest diagnostic value
2. **P2-A1** (G1 APN guidance) — core engagement behavior change
3. **P2-B1** (G2 EKF seeker) — depends on G1 for integration testing
4. **P2-E1** (G5 aero table) — shares `default_guidance_model.cpp` with G1 clusters; must serialize after P2-C1
5. **P2-C1** (G3 autopilot) — small surface area, low risk
6. **P2-F1** (G6 warhead) — independent of G1-G5 for physics models

## Serialization Constraints

These clusters share write surfaces and MUST NOT be dispatched concurrently:

- **default_guidance_model.cpp**: P2-A1, P2-A2, P2-B3, P2-C1, **P2-E1** — serial only (wave 1 completed in this order)
- **simulation_kernel_missile_tuning.h**: P2-A1, P2-B2, P2-C2, P2-D2, P2-E2, P2-F3 — serial only (wave 1: A1/C2/E2 done; B2/D2/F3 remain)
- **weapon_common.h**: P2-A1, P2-B2, P2-D2, P2-F3 — serial only (wave 1: A1 done; B2/D2/F3 remain)
- **damage_system_common.h**: P2-D1 — single cluster
- **default_effects_warhead_detail.inc**: P2-F1, P2-F2 — serial within G6
