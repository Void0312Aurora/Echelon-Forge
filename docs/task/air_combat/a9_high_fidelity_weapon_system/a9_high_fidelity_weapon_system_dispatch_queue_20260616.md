# A9 High-Fidelity Weapon System — Dispatch Queue

Status: `2026-06-16` P2 complete (12 pass, 2 deferred). P4-A pass. Executing P3.

Parent: [README.md](README.md)
Task clusters: [a9_high_fidelity_weapon_system_task_clusters_20260616.md](a9_high_fidelity_weapon_system_task_clusters_20260616.md)

## Dispatch State

| Cluster | Status | Worker | Dispatched | Completed | Artifacts |
|---------|--------|--------|-----------|-----------|-----------|
| P0-A | pass | main thread | 2026-06-16 | 2026-06-16 | README (en/zh), task clusters, current status, dispatch queue, acceptance draft, archive README |
| P0-B | pass | main thread | 2026-06-16 | 2026-06-16 | p0b_gap_audit_summary_20260616.md (6-subsystem gap audit) |
| P1-A | partial | main thread | 2026-06-16 | — | source_ledger_20260616.md (14 entries with full admission fields; covers G1-G6) |
| P1-B | deferred | — | — | — | Benchmark parameter tables deferred: proxy→target mappings partially captured in gap audit |
| P1-C | deferred | — | — | — | Test coverage map deferred: existing surface documented in acceptance doc |
| P2-A1 | pass | main thread | 2026-06-16 | 2026-06-16 | APN pipeline (8 files) + feed-forward term + low-pass filter (τ=0.30s) |
| P2-A2 | pass | main thread | 2026-06-16 | 2026-06-16 | Bearing-acceleration estimator + filtered state variables |
| P2-B1 | pass | main thread | 2026-06-16 | 2026-06-16 | kalman_seeker.h (295 lines): EKF predict/update/init + body↔world transforms |
| P2-B2 | pass | main thread | 2026-06-16 | 2026-06-16 | use_kalman_seeker in MissileTuning/JSON/bindings/spawn pipeline |
| P2-B3 | pass | main thread | 2026-06-16 | 2026-06-16 | EKF integration in update_track/propagate_track with fallback; LOS rates computed; closing speed uses actual velocity |
| P2-C1 | pass | main thread | 2026-06-16 | 2026-06-16 | Second-order state-space autopilot + order=3 actuator lag (τ=0.03s) |
| P2-C2 | pass | main thread | 2026-06-16 | 2026-06-16 | autopilot_order/damping in MissileTuning/JSON/bindings |
| P2-D1 | pass | main thread | 2026-06-16 | 2026-06-16 | hit_to_kill coverage penalty; PF-R4 preserved |
| P2-D2 | deferred | — | — | — | Fuze refinement params deferred: existing coverage differentiation sufficient for current scope |
| P2-E1 | pass | main thread | 2026-06-16 | 2026-06-16 | Configurable Mach breakpoints + power-on Cd0 ratio |
| P2-E2 | pass | main thread | 2026-06-16 | 2026-06-16 | G5 params in MissileTuning/JSON/bindings pipeline |
| P2-F1 | pass | main thread | 2026-06-16 | 2026-06-16 | Rod weld cap (1150 m/s) + cutting threshold (610 m/s) opt-in |
| P2-F2 | deferred | — | — | — | Rod expansion kinematics deferred: static approximation sufficient for <10m engagements |
| P2-F3 | pass | main thread | 2026-06-16 | 2026-06-16 | C/M/E fields in WarheadProfile (5 new fields) + Gurney fragment velocity + JSON/bindings |
| P3-A | partial | — | — | — | Bindings updated for all new fields; formal round-trip test not yet written |
| P3-B | deferred | — | — | — | debug runtime state already exposes core new fields; remaining diagnostics deferred |
| **P3-C** | **planned** | main thread | — | — | Scenario JSON example exercising new params |
| **P3-D** | **in_progress** | main thread | 2026-06-16 | — | Test suite run: 62 pre-existing failures (same as main), zero regressions introduced |
| P4-A | pass | main thread | 2026-06-16 | 2026-06-16 | p4a_apn_geometry_sweep (12 rows: 4 geometries × 3 gain levels, CSV retained) |
| P4-B | deferred | — | — | — | Parameter sensitivity sweep deferred: P4-A provides baseline evidence |
| P4-C | deferred | — | — | — | A/B comparison deferred: P4-A CSV provides side-by-side evidence |
| P5-A | planned | main thread | — | — | Acceptance closeout record |
| P5-B | planned | main thread | — | — | Parent air_combat/README.md update |

## Execution Order (P3 → P5)

Per the phase plan, remaining work executes sequentially:

```
P3-D (regression record) → P3-C (scenario JSON) → P5-A (closeout) → P5-B (parent sync)
```

P1-B/C, P2-D2/F2, P3-B, P4-B/C are explicitly deferred — their evidence value
does not justify the implementation cost given current scope.

## Serialization Constraints (Historical)

All P2 clusters touching shared files were serialized in waves 1-10. No
remaining clusters share write surfaces.
