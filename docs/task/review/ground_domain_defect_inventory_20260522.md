# Ground Domain — Defect Inventory And Migration Gap Analysis

Status: `2026-05-22` compiled from architecture audit of G0-G5 baseline.
Source: cross-domain architecture analysis of air, naval, and ground tasking layers.

## 1. Purpose

This inventory documents every known defect, gap, and architectural incompleteness in
the ground domain as of the G5 MVP scenario shell acceptance. Each item carries a
severity, a concrete file/line reference, and a recommended resolution path.

## 2. Severity Classification

| Level | Meaning |
|-------|---------|
| **BLOCKER** | Would prevent declaring ground as "maintained" for any stage beyond P2 tasking. |
| **HIGH** | Structural gap that limits domain completeness. |
| **MEDIUM** | Architectural debt that accumulates risk over time. |
| **LOW** | Documentation, naming, or consistency issue; resolve opportunistically. |

## 3. Defect Ledger

### D-001: No C++ `command/ground/` Directory

**Severity:** BLOCKER
**Reference:** `src/components/command/` — contains `air/` and `naval/` but no `ground/`.
**Impact:** All ground command construction flows through `ground_profile.py::build_kernel_mission_command()`, labeled `"Compatibility shell only; G1 does not define ground command semantics."` — blind field pass-through from raw dict.
**Resolution:** Create `src/components/command/ground/mission_command_ground.h` only after `MissionCommand` aggregate pattern stabilizes (see D-003). Define minimal ground command vocabulary.

### D-002: No C++ `tasking/ground/` Directory

**Severity:** BLOCKER
**Reference:** `src/components/tasking/` — contains `air/` and `naval/` with domain-specific enums and DTOs but no `ground/`.
**Impact:** Ground tasking uses common-core fields only. No ground-specific fields without C++ type definitions.
**Resolution:** Create `src/components/tasking/ground/` with `ground_tasking_enums.h`, `task_order_ground.h`, `leader_intent_ground.h`, `pilot_report_ground.h`.

### D-003: MissionCommand Aggregate Missing Ground

**Severity:** HIGH
**Reference:** `src/components/command/mission_command.h` — aggregates `MissionCommandCore + MissionCommandAir + MissionCommandNaval` via flat inheritance. No ground member.
**Impact:** When ground needs command semantics, adding `MissionCommandGround` to flat inheritance makes the "high-risk caller convergence point" riskier.
**Resolution:** Do NOT add `MissionCommandGround` to flat inheritance. Use capability composition (field bags or variant members) per Architecture Law 15.

### D-004: Stage Node Manifest Registry Has No P2 Node

**Severity:** HIGH
**Reference:** `src/runtime/contracts/stage_node_manifest_registry.h` — 5 nodes (P7×2, P9×1, P10×2). P2 (TaskingIntent) has zero nodes for any domain.
**Impact:** Cannot declare "maintained" facade visibility without a registered stage node.
**Resolution:** Register a P2 tasking node manifest. Start with `diagnostics_only` visibility; promote to `maintained_facade_surface` when proven.

### D-005: Clock Domain — Only Tactical Cadence Defined

**Severity:** HIGH
**Reference:** `docs/task/ground/archive/ground_domain_bootstrap_plan_20260521.md` §6.4.
**Impact:** Only tactical decision rate (1 Hz) is declared. Motion, sensing, fires, observation export cadences are undefined. The 1 Hz is sometimes misread as "the whole ground domain runs at 1 Hz."
**Resolution:** Extend the clock domain table with ALL planned ground pipelines and their cadence ranges, even if marked "deferred."

### D-006: No Ground-Specific Enums in C++

**Severity:** HIGH
**Reference:** Compare air (`air_tasking_enums.h`: `LeaderPhase`, `TakeoffProcedureType`, etc.) and naval (`naval_tasking_enums.h`: `NavalWarfareRole`, `NavalStationType`) — ground has none.
**Impact:** Concepts like echelon, posture, formation_width have no typed representation.
**Resolution:** Define `GroundEchelonLevel`, `GroundTacticalPosture`, `GroundSupportRelationship` as first-wave enums.

### D-007: Fidelity Profile Not Evaluated For Ground

**Severity:** MEDIUM
**Reference:** `src/runtime/contracts/fidelity_profile_contracts.h` — 6 labels; only `exact_evaluation` admitted.
**Impact:** When ground runtime behavior begins, no baseline exists to compare against.
**Resolution:** Before G6: define backend profile, parity budget, and fidelity request scoped to P2 tasking.

### D-008: WP21 Dependency — Ground Blocked On Counterfactual Restore

**Severity:** MEDIUM
**Reference:** `src/runtime/contracts/counterfactual_replay_contracts.h` — all restore validation rejects with `"snapshot_restore_boundary_not_supported_for_wp21b"`.
**Impact:** Ground cannot participate in counterfactual experiments until WP21-B implements snapshot/restore.
**Resolution:** Not directly actionable for ground. Track WP21-B. Design ground counterfactual participation against WP21 contract vocabulary from the start.

### D-009: common_core Fallback Defaults To Air

**Severity:** MEDIUM
**Reference:** `python/rl/tasking/common_core_profile.py:76` — `return "air"` when domain cannot be identified.
**Impact:** Misconfigured ground scenarios silently get air task-family inference (CAP, RTB instead of Move, Occupy).
**Resolution:** Replace silent air fallback with warning log or fail-closed sentinel. Consider requiring `tasking_profile` as mandatory in all scenario JSONs.

### D-010: `build_kernel_mission_command` Is A Compatibility Shell

**Severity:** MEDIUM
**Reference:** `python/rl/profile/ground_profile.py:253-276` — docstring states it explicitly.
**Impact:** `infer_route_ref_id()`, `infer_recovery_base_id()`, etc. all return 0. Shell sufficient for G5 smoke but insufficient for real ground command semantics.
**Resolution:** Do not expand this shell. Implement proper ground command builder when ready (G6+).

### D-011: Ground Adapter Re-exports Air's Leader Phase Manager

**Severity:** LOW
**Reference:** `python/rl/tasking/ground_adapter.py:11-12` — imports from `leader_tasking.py` which contains air-specific logic.
**Impact:** If ground scenario uses `ScriptedC2TaskManager`, it gets air phase inference (takeoff→CAP→RTB→landing).
**Resolution:** Add ground phase inference path or create separate `ground_leader_tasking.py`.

### D-012: `.seed` File Pattern Is Not A Permanent Solution

**Severity:** LOW
**Reference:** `examples/config/database/ground/units/ground_platoon_starter.seed`.
**Impact:** No migration plan from `.seed` to runtime `.json` unit schema exists.
**Resolution:** Define promotion criteria: capability families declared, spawn path confirmed, contract test passing.

### D-013: No Ground Scenarios Directory In `scenarios/README.md`

**Severity:** LOW
**Reference:** G5 acceptance criteria — verify `scenarios/README.md` was updated.
**Impact:** Discoverability gap.
**Resolution:** Verify and update `scenarios/README.md` if needed.

### D-014: No Architecture Test For Ground Domain Boundary

**Severity:** LOW
**Reference:** `tests/architecture/` — contains WP5-WP20 tests but no ground-specific architecture test.
**Impact:** Architecture invariants not enforced for ground.
**Resolution:** Add `tests/architecture/test_ground_domain_boundary.py` verifying: bridge dispatch, profile normalization, no private runtime path.

## 4. Summary

| Severity | Count | Items |
|----------|-------|-------|
| BLOCKER | 2 | D-001, D-002 |
| HIGH | 4 | D-003, D-004, D-005, D-006 |
| MEDIUM | 4 | D-007, D-008, D-009, D-010 |
| LOW | 4 | D-011, D-012, D-013, D-014 |

## 5. Recommended Resolution Order

1. **Immediately (G5 follow-up):** D-013, D-014
2. **Before G6:** D-005, D-009, D-011
3. **Before G6 — requires C++ work:** D-001, D-002, D-006
4. **Before "maintained":** D-004, D-007
5. **Blocked externally:** D-003, D-008
6. **Opportunistic:** D-010, D-012
