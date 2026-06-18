# MLF-6 Structural Failure — Current Status

Status: `2026-06-18` active v8 ready-for-acceptance — P1/P2 corrected, P3 state
machine implemented, P4 event writer connected to the event store/facade,
P5 diagnostic export implemented, P6 focused validation complete, and P7
broader regression is green after obsolete-oracle updates. Archive movement is
still withheld per user instruction; this package is ready for user acceptance,
not yet archived.
Seven design decisions (D1-D7) frozen.

## What Changed (v1 → v2)

- **Removed aerodynamics bridging from MLF-6 scope.** Flight-dynamics response to
  breakup belongs in MLF-7 per the MLF-1 contract (`damage/air` write surface).
  MLF-6 write surface is `damage/physics` only.
- **Froze seven design decisions (D1-D7):** ECS consumption path,
  non-modification of existing ECS components, new `StructuralBreakupState`
  component for irreversible state, `detached_part_ref` string semantics,
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

## What Changed (v2 → v2.1)

- **Fixed all relative links** in README.md and README.zh.md: `examples/` and
  `src/` paths corrected from 7 `../` to 5; `docs/` subpaths corrected from 5
  `../` to 4.
- **Added D7: `StructuralBreakupState` ECS component.** Irreversible per-airframe
  breakup state is persisted in a new ECS component, not internal system state.
  This is the only approach that survives world-batch serialization, save/load,
  replay, and downstream queries (MLF-7).
- **Amended D2 and D5** to reference the new component and clarify that MLF-6
  writes a *new* ECS component while touching no *existing* ECS components.
- **Bound diagnostics probe to existing facade surface.** P5 diagnostic tool
  is a thin consumer of `StructuralBreakupEvent` bindings already in
  `bindings_runtime.cpp:449-457` and `bindings_core.cpp`; no new binding layer.

## What Changed (v3 → v4)

- **Implemented the P4 event writer.** `StructuralFailureUpdate` now records
  `StructuralBreakupEvent` rows for new group transitions and multi-axis breakup
  activation.
- **Connected structural breakup events through the event store and facade.**
  The store completes lethality-chain headers for the canonical
  `structural_breakup` stage, resolves recent component-damage causes, and
  exports `structural_breakup_events` with the existing packet surface.
- **Added focused P4 evidence.** `structural_failure_events` covers transition
  emission, multi-axis emission, and component-damage cause attribution.

## What Changed (v4 → v5)

- **Implemented the P5 diagnostics export.** `tools/diagnostics/structural_breakup_export.py`
  normalizes existing `StructuralBreakupEvent` binding objects from
  `EngagementEventPacket`, `RecentEngagementEvents`, or event lists into stable
  rows and per-chain summaries.
- **Kept the surface thin.** The probe consumes the existing facade/binding
  vectors only; it adds no C++ binding surface and does not duplicate the
  runtime export pipeline.
- **Added focused P5 evidence.** `tests/tools/test_structural_breakup_export.py`
  covers all event fields, per-chain summaries, chain filtering, and CSV/JSON
  write helpers.

## What Changed (v5 → v6)

- **Implemented P6 focused break-mode validation.** The
  `structural_failure_break_modes` suite covers wing_loss, tail_loss,
  engine_detach, fuselage_rupture, multi_axis, no-damage zero-event, and
  wing_loss irreversibility.
- **Added named CTest lanes.** `ctest -R structural_failure` now runs the
  structural state, event-writer, and break-mode suites instead of matching no
  tests.
- **Kept broader regression separate.** `ef_test_all` passes, but full
  air_combat/world_batch regression remains the P7 gate.

## What Changed (v6 → v7)

- **Executed the P7 broad regression lane.** With the current build on
  `feature/mlf-6-structural-failure`,
  `PYTHONPATH=/home/void0312/Workshop/CMO/build-workshop pytest -q tests/runtime/air_combat/ tests/world_batch/`
  initially exposed 14 feature-only obsolete-oracle failures. After updating
  those tests to the current geometry/event-materiality contracts, the branch
  no longer had feature-only failures. The remaining first-pass residual is
  superseded by v8 below.
- **Compared against the main baseline.** A temporary `main` worktree at
  `/tmp/cmo-main-p7` (`main` HEAD `3f11ec68`) showed the broad-suite residual
  was inherited baseline behavior rather than MLF-6 feature-only regression.
  This first-pass baseline comparison is superseded by v8 below.
- **Reconfirmed MLF-6 focused lanes remain green.**
  `ctest --test-dir build-workshop -R structural_failure --output-on-failure`
  passed 3/3; `ctest --test-dir build-workshop -R ef_test_all --output-on-failure`
  passed; the structural/facade Python guard set passed 45/45.
- **Hardened smoke assumptions found by P7.** The F-16C component geometry rows
  now keep current component centers inside parent hitboxes for direct sampling,
  and the event-store component-damage export now suppresses non-material
  projection crumbs below a 0.01 integrity-drop threshold.
- **Updated obsolete broad-suite oracles.** Legacy tests now assert current
  geometry gradients, materialized component-damage event semantics, and seeded
  live-fuze evidence instead of stale absolute probability/old-coordinate
  assumptions.
- **Held closure without archive movement.** P7 evidence was recorded while
  archive movement remained out of scope.

## What Changed (v7 → v8)

- **Completed the P7 broad regression lane.** After the remaining obsolete
  live-chain, component-geometry, typed-edge, and world_batch reward-oracle
  updates, the full P7 command now passes:
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/`
  → `447 passed in 36.77s`.
- **Converted inherited-baseline hold to ready-for-acceptance.** The prior
  first-pass red state is superseded; no feature-only or inherited broad
  failures remain in the P7 lane.
- **Kept archive movement out of scope.** The user requested P7 closeout without
  archival, so the package remains active / ready-for-acceptance until explicit
  user acceptance/archive instruction.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-6 boundary (P0) | active | [README.md](README.md) v2, D1-D7 frozen, [task clusters](missile_lethality_structural_failure_task_clusters_20260617.md), [dispatch queue](missile_lethality_structural_failure_dispatch_queue_20260617.md), [acceptance gate](missile_lethality_structural_failure_acceptance_20260617.md) | Scope remains frozen |
| MLF-6 component inventory (P1) | complete | [component inventory](missile_lethality_structural_failure_component_inventory_20260617.md); write-count validation passes | Read-only doc |
| MLF-6 break-mode mapping (P2) | complete | [break-mode mapping](missile_lethality_structural_failure_break_mode_mapping_20260617.md); default 26 + TG-P7 32 coverage validation passes | Design doc; consumed by P3 |
| MLF-6 state machine (P3) | complete | `src/components/combat/structural_failure.h`, `src/systems/combat/structural_failure_system.h`, `src/tests/test_structural_failure_system.cpp`; `ef_test --test-suite=structural_failure_state` passes | Writes only new `StructuralBreakupState` |
| MLF-6 event writer (P4) | complete | `src/systems/combat/structural_failure_system.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/runtime/facade/runtime_facade.cpp`; `ef_test --test-suite=structural_failure_events` | Event-store extension of P3 |
| MLF-6 diagnostics (P5) | complete | `tools/diagnostics/structural_breakup_export.py`, `tests/tools/test_structural_breakup_export.py`; `pytest -q tests/tools/test_structural_breakup_export.py` | Python probe; existing bindings only |
| MLF-6 focused tests (P6) | complete | `structural_failure_break_modes`; `ctest --test-dir build-workshop -R structural_failure --output-on-failure` | Focused C++ coverage |
| MLF-6 regression (P7) | complete / ready for acceptance | `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat/ tests/world_batch/` → `447 passed`; focused MLF-6 lanes green | No archive movement until explicit user instruction |
| `StructuralBreakupEvent` contract | active / writer connected | `engagement_contracts.h`, `structural_failure_system.h` | Contract populated by P4; no aero/loss coupling |
| `structural_breakup_events` vector | active / populated and exportable | `engagement_event_types.h`, `simulation_kernel_engagement_event_store.cpp`, `runtime_facade.cpp`, `structural_breakup_export.py` | Collector stores breakup facts; P7 broad regression is green; MLF-6 still does not consume aero/loss-state authority |
| `ComponentDamageState` (ECS) | active / MLF-6 read surface | `damage_common.h` | MLF-6 reads; does not mutate |
| `structural_integrity` scalar | active / MLF-6 forbidden touch | `damage_air.h:114` | MLF-6 neither reads nor writes |
| Flight dynamics | active / deferred to MLF-7 | `aerodynamics_system.h` | MLF-6 does not modify |
| Loss-state classification | active / deferred to MLF-7 | `damage_system_common.h:403-423` | MLF-6 does not modify |

## Residual Register

| ID | Description | Severity | Status |
| --- | --- | --- | --- |
| MLF6-R1 | P4 event writer was missing and `structural_breakup_events` was contract-only. | medium | closed by v4 focused event-writer tests |
| MLF6-R2 | P5 diagnostics probe was not implemented. | low | closed by v5 focused export tests |
| MLF6-R3 | Full air_combat/world_batch regression was red after the first P7 pass. | medium | closed by v8: `447 passed` |
| MLF6-R4 | Archive movement is intentionally withheld until explicit user instruction. | medium | held / no archive by request |

## Recommended Next Actions

1. Present MLF-6 for user acceptance; the P7 broad lane is green.
2. Do not move the subproject into archive until the user explicitly asks.
3. If accepted, open the next follow-on as MLF-7 secondary consequence coupling
   rather than extending MLF-6.

## Forbidden Claims (Must Remain Refused)

- [x] `pk_authority` must remain `false`.
- [x] `deterministic_kill_authority` must remain `false`.
- [x] `real_weapon_structural_kill_authority` must remain `false`.
- [x] `wreck_debris_lifecycle_authority` must remain `false` (MLF-8).
- [x] `flight_dynamics_modification_authority` must remain `false` (MLF-7).
- [x] `structural_integrity_modification_authority` must remain `false` (MLF-7).
- [x] `loss_state_modification_authority` must remain `false` (MLF-7).
- [x] No AIM-120C, MQ-9, or specific platform/weapon calibration.
- [x] No naval or ground platform structural models.
- [x] No reopening of sealed MLF-1 through MLF-5 packages.
