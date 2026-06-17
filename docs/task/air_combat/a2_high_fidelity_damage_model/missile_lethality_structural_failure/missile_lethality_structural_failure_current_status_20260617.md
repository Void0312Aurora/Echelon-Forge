# MLF-6 Structural Failure — Current Status

Status: `2026-06-17` planning v2 — subproject corrected per P0 self-review. Six
design decisions (D1-D6) frozen. No implementation dispatched.

## What Changed (v1 → v2)

- **Removed aerodynamics bridging from MLF-6 scope.** Flight-dynamics response to
  breakup belongs in MLF-7 per the MLF-1 contract (`damage/air` write surface).
  MLF-6 write surface is `damage/physics` only.
- **Froze six design decisions (D1-D6):** ECS consumption path,
  `structural_integrity` non-modification, `detached_part_ref` string semantics,
  irreversible cumulative state machine, ECS system registration point, and
  loss-state deferral to MLF-7.
- **Split phases from 5 to 7 (P0-P7):** added dedicated P1 Inventory,
  P2 Break-Mode Mapping, and split P3 State Machine from P4 Event Writer.
  Granularity now matches MLF-5's pattern.
- **Added concrete component-to-break-mode mapping as an explicit phase (P2)**
  with F-16C-specific structural group classification.
- **Clarified consumption path:** MLF-6 reads live ECS `ComponentDamageState`,
  not event-store `ComponentDamageEvent` rows.
- **Clarified `detached_part_ref`:** string label, not world entity reference.
  Entity creation deferred to MLF-8.
- **Task clusters expanded from 8 to 9** to match new phase granularity.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-6 boundary (P0) | active | [README.md](README.md) v2, D1-D6 frozen, [task clusters](missile_lethality_structural_failure_task_clusters_20260617.md), [dispatch queue](missile_lethality_structural_failure_dispatch_queue_20260617.md), [acceptance draft](missile_lethality_structural_failure_acceptance_20260617.md) | Docs-only; no runtime changes |
| MLF-6 component inventory (P1) | planned | not yet started | Read-only doc |
| MLF-6 break-mode mapping (P2) | planned | not yet started | Design doc only |
| MLF-6 state machine (P3) | planned | not yet started | `structural_failure_system.h/.cpp` |
| MLF-6 event writer (P4) | planned | not yet started | Event-store extension of P3 |
| MLF-6 diagnostics (P5) | planned | not yet started | Python probe |
| MLF-6 focused tests (P6) | planned | not yet started | C++ test files |
| MLF-6 regression (P7) | planned | not yet started | Test suite execution |
| `StructuralBreakupEvent` contract | exists / no writer | `engagement_contracts.h:213-221` | Contract shape only |
| `structural_breakup_events` vector | exists / empty | `engagement_event_types.h:17` | Collector exists; no writer |
| `ComponentDamageState` (ECS) | active / MLF-6 read surface | `damage_common.h` | MLF-6 reads; does not mutate |
| `structural_integrity` scalar | active / MLF-6 forbidden touch | `damage_air.h:114` | MLF-6 neither reads nor writes |
| Flight dynamics | active / deferred to MLF-7 | `aerodynamics_system.h` | MLF-6 does not modify |
| Loss-state classification | active / deferred to MLF-7 | `damage_system_common.h:403-423` | MLF-6 does not modify |

## Residual Register

| ID | Description | Severity | Status |
| --- | --- | --- | --- |
| — | No residuals yet; subproject in planning | — | — |

## Recommended Next Actions

1. Confirm v2 scope, D1-D6 decisions, and corrected MLF-6/MLF-7 boundary with
   project owner.
2. `MLF-6B`: Execute component inventory — map every `ComponentDamageState` field
   and every F-16C component name.
3. `MLF-6C`: Design break-mode mapping table with integrity thresholds.
4. `MLF-6D`: Implement `StructuralFailureUpdate` state machine (first runtime
   change).

## Forbidden Claims (Must Remain Refused)

- [ ] `pk_authority` must remain `false`.
- [ ] `deterministic_kill_authority` must remain `false`.
- [ ] `real_weapon_structural_kill_authority` must remain `false`.
- [ ] `wreck_debris_lifecycle_authority` must remain `false` (MLF-8).
- [ ] `flight_dynamics_modification_authority` must remain `false` (MLF-7).
- [ ] `structural_integrity_modification_authority` must remain `false` (MLF-7).
- [ ] `loss_state_modification_authority` must remain `false` (MLF-7).
- [ ] No AIM-120C, MQ-9, or specific platform/weapon calibration.
- [ ] No naval or ground platform structural models.
- [ ] No reopening of sealed MLF-1 through MLF-5 packages.
