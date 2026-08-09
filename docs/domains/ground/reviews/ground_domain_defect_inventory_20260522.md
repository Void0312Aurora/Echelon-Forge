# Ground Domain — Defect Inventory And Migration Gap Analysis

Language: English canonical; [Chinese companion](ground_domain_defect_inventory_20260522.zh.md).

Document kind: `review`
Lifecycle: `maintained`
Canonical: `docs/domains/ground/reviews/ground_domain_defect_inventory_20260522.md`
Owner: `domains/ground/reviews`
Last verified: `2026-08-08`
Review basis: `2026-05-22` inventory with a `2026-06-09` closeout update; not a current defect authority.

Status: retained review compiled from the `2026-05-22` G0-G5 audit, with a
`2026-06-09` closeout update. New defects require a current issue or review.
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

### D-001: No C++ `command/ground/` Directory — ~~BLOCKER~~ **CLOSED 2026-06-09**

`src/components/domains/ground/command/` now exists with `mission_command_ground.h` + README (EN/ZH).

### D-002: No C++ `tasking/ground/` Directory — ~~BLOCKER~~ **CLOSED 2026-06-09**

`src/components/domains/ground/tasking/` now exists with full structure: `ground_tasking_enums.h`, `leader_intent_ground.h`, `pilot_report_ground.h`, `task_order_ground.h` + README (EN/ZH).

### D-003: MissionCommand Aggregate Missing Ground — ~~HIGH~~ **CLOSED 2026-06-09**

`mission_command.h` now includes `MissionCommandGround` in the flat inheritance chain with `mission_command_ground_owner_slice()` and `mission_command_ground_static_task_directive()` accessors.

### D-004: Stage Node Manifest Registry Has No P2 Node

**Severity:** HIGH
**Reference:** `src/runtime/contracts/stage_node_manifest_registry.h` — 5 nodes (P7×2, P9×1, P10×2). P2 (TaskingIntent) has zero nodes for any domain.
**Impact:** Cannot declare "maintained" facade visibility without a registered stage node.
**Resolution:** Register a P2 tasking node manifest. Start with `diagnostics_only` visibility; promote to `maintained_facade_surface` when proven.

### D-005: Clock Domain — Only Tactical Cadence Defined

**Severity:** HIGH
**Reference:** `docs/systems/environment/reviews/environment_substrate_g0_closure_20260606/README.md` §6.4.
**Impact:** Only tactical decision rate (1 Hz) is declared. Motion, sensing, fires, observation export cadences are undefined. The 1 Hz is sometimes misread as "the whole ground domain runs at 1 Hz."
**Resolution:** Extend the clock domain table with ALL planned ground pipelines and their cadence ranges, even if marked "deferred."

### D-006: No Ground-Specific Enums in C++ — ~~HIGH~~ **PARTIAL 2026-06-09**

Basic enums now exist: `GroundTaskMode`, `GroundStatusPhase` (`ground_tasking_enums.h`). Still missing: `GroundEchelonLevel`, `GroundTacticalPosture`, `GroundSupportRelationship`. Downgraded to MEDIUM.

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

### D-014: No Architecture Test For Ground Domain Boundary — ~~LOW~~ **CLOSED 2026-06-09**

`tests/architecture/ground/` now exists with `test_realism_gradient_guardrails.py` and `test_tasking_component_boundary.py`.

## 4. Summary

| Severity | Count | Items |
|----------|-------|-------|
| ~~BLOCKER~~ | ~~2~~ 0 | ~~D-001, D-002~~ (both closed) |
| HIGH | ~~4~~ 2 | D-004, D-005 |
| MEDIUM | ~~4~~ 5 | D-006(downgraded), D-007, D-008, D-009, D-010 |
| LOW | ~~4~~ 3 | D-011, D-012, D-013 |
| **CLOSED** | **5** | D-001, D-002, D-003, D-006(partial→downgraded), D-014 |

## 5. Recommended Resolution Order

1. **Immediately (G5 follow-up):** D-013, D-014
2. **Before G6:** D-005, D-009, D-011
3. **Before G6 — requires C++ work:** D-001, D-002, D-006
4. **Before "maintained":** D-004, D-007
5. **Blocked externally:** D-003, D-008
6. **Opportunistic:** D-010, D-012
