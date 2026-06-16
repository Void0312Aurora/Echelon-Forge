# A9 High-Fidelity Weapon System — Dispatch Queue

Status: `2026-06-16` P0 boundary freeze. No worker packets dispatched yet.

Parent: [README.md](README.md)
Task clusters: [a9_high_fidelity_weapon_system_task_clusters_20260616.md](a9_high_fidelity_weapon_system_task_clusters_20260616.md)

## Dispatch State

| Cluster | Status | Worker | Dispatched | Completed | Artifacts |
|---------|--------|--------|-----------|-----------|-----------|
| P0-A | active | main thread | 2026-06-16 | — | README, task clusters, current status |
| P0-B | planned | — | — | — | — |
| P1-A | planned | — | — | — | — |
| P1-B | planned | — | — | — | — |
| P1-C | planned | — | — | — | — |
| P2-A1 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-A2 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-B1 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-B2 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-B3 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-C1 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-C2 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-D1 | held (P0-B/P1 evidence + PF baseline guard) | — | — | — | — |
| P2-D2 | held (P0-B/P1 evidence + PF baseline guard) | — | — | — | — |
| P2-E1 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-E2 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-F1 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-F2 | held (P0-B/P1 evidence) | — | — | — | — |
| P2-F3 | held (P0-B/P1 evidence) | — | — | — | — |
| P3-A | held (P0-B/P1 evidence) | — | — | — | — |
| P3-B | held (P0-B/P1 evidence) | — | — | — | — |
| P3-C | held (P0-B/P1 evidence) | — | — | — | — |
| P3-D | held (P0-B/P1 evidence) | — | — | — | — |
| P4-A | held (P0-B/P1 evidence) | — | — | — | — |
| P4-B | held (P0-B/P1 evidence) | — | — | — | — |
| P4-C | held (P0-B/P1 evidence) | — | — | — | — |
| P5-A | held (P0-B/P1 evidence) | — | — | — | — |
| P5-B | held (P0-B/P1 evidence) | — | — | — | — |

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

- **default_guidance_model.cpp**: P2-A1, P2-A2, P2-B3, P2-C1 — serial only
- **simulation_kernel_missile_tuning.h**: P2-A1, P2-B2, P2-C2, P2-D2, P2-E2, P2-F3 — serial only
- **weapon_common.h**: P2-A1, P2-B2, P2-D2, P2-F3 — serial only
- **damage_system_common.h**: P2-D1 — single cluster
- **default_effects_warhead_detail.inc**: P2-F1, P2-F2 — serial within G6
