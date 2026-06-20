# A9 P0-B Gap Audit Summary

Status: `2026-06-16` P0-B complete — 6 subsystem gap audits executed (read-only).

## Audit Results Summary

| Subsystem | Gaps Found | Critical Gaps | Files Touched by Fixes | Recommended First Cluster |
|-----------|-----------|---------------|----------------------|--------------------------|
| G1 — APN Guidance | 7 | #2 (no a_T feed-forward), #3 (no estimator), #1 (opaque N') | `default_guidance_model.cpp`, `missile_guidance_types.h`, `weapon_common.h`, `missile_tuning.h` | P2-A1 (APN term + kPnGainScale removal) |
| G2 — Kalman Seeker | 13 | #1 (no state vector), #2 (no covariance), #5 (no Kalman gain) | `default_guidance_model.cpp`, `weapon_common.h`, new `kalman_seeker.h/.cpp` | P2-B1 (EKF engine in new file) |
| G3 — Autopilot | 8 | #7 (no actual loops—just a lag filter), #4 (no ζ) | `default_guidance_model.cpp`, `missile_guidance_types.h`, `missile_tuning.h` | P2-C1 (second-order transfer function) |
| G4 — Fuze Refinement | 8 | #1 (hit_to_kill gets non-zero coverage), #2 (fuze type unused in coverage) | `damage_system_common.h` | P2-D1 (hit_to_kill gate + fuze-type coverage) |
| G5 — Aerodynamics | 7 | #1 (only 2 fixed Cd0), #2 (no power on/off distinction) | `default_guidance_model.cpp`, `missile_guidance_types.h`, `missile_tuning.h` | P2-E1 (Mach-indexed Cd0 table) |
| G6 — Warhead | 10 | G7 (no C/M/E fields), G1 (no Gurney), G4 (rod cap 1450→1150) | `warhead_detail.inc`, `weapon_common.h`, `missile_tuning.h` | P2-F1 (Gurney equation) |

## Key Cross-Cutting Findings

### G4: Already Partially Differentiated
`damage_mechanism_coverage_score` (damage_system_common.h:193) already treats
continuous_rod differently from blast_fragmentation via lateral/axial geometry
correction. The genuinely missing differentiation is:
- **hit_to_kill**: receives non-zero coverage from range_score despite requiring
  direct hit (HIGH priority — physically incorrect Pk)
- **fuze type × warhead family**: radar vs laser proximity fuzes have different
  beam patterns but coverage score treats all as spherical

### G2: Measurement Noise Already Configured But Unused
`sensor_bearing_noise_std` and `sensor_range_noise_std` exist in
`MissileTuning` (missile_tuning.h:23-24) but are never consumed by
`GuidanceResolvedTuning` or any filter logic. EKF R-matrix construction can
consume them directly.

### G6: Data Model Is the Root Blocker
Gaps G1 (Gurney), G2 (decay), G6 (kill interval), G3 (directionality), and
G10 (fragment statistics) all depend on Gap G7: `WarheadProfile` has a single
`mass_kg` with no distinction between explosive mass (C), case mass (M), or
Gurney constant (E). All physics-based refinements are blocked until C/M/E
fields exist in the data model.

### G3/G5/G1: All Touch default_guidance_model.cpp
Per serialization constraints, these MUST be sequential. The dispatch order
from the task clusters doc (P2-A1 → P2-A2 → P2-B3 → P2-C1 → P2-E1) respects
this constraint.

## Recommended Implementation Order

Based on risk, dependency, and impact:

| Priority | Cluster | Rationale |
|----------|---------|-----------|
| 1 | P2-D1 (G4 fuze) | Smallest scope (1 file), builds on PF-R4, fixes physically incorrect hit_to_kill Pk |
| 2 | P2-A1 (G1 APN) | Core engagement behavior; kPnGainScale removal is high-regression but bounded |
| 3 | P2-E1 (G5 aero) | Independent of G1/G2 for Cd0 table; shares default_guidance_model.cpp so must follow G1 |
| 4 | P2-B1 (G2 EKF) | Largest scope (new file), can develop in parallel with G5/G6 once kalman_seeker.h exists |
| 5 | P2-F3 (G6 data model) | C/M/E fields unblock all G6 physics; additive change to weapon_common.h |
| 6 | P2-C1 (G3 autopilot) | Smallest surface area change (3 lines → second-order TF) |
| 7 | P2-F1 (G6 Gurney) | Depends on P2-F3 (C/M/E fields); then Gurney equation replaces empirical fit |

## Audit Artifacts

Detailed per-subsystem audits are retained in the session transcript. Key
findings are summarized above. No code was modified during P0-B.
