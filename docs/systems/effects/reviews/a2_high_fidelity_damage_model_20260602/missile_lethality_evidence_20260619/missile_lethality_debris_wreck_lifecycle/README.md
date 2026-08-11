# MLF-8 Debris And Wreck Lifecycle

Status: `2026-06-19` accepted / archived. P0 boundary, P1 inventory, P2
lifecycle contract, P3 runtime representation, P4 diagnostics/facade exposure,
P5 focused validation, P6 broader smoke, and P7 acceptance/archive are
complete for the bounded diagnostics-only MLF-8 slice.

Language:

- English canonical: `README.md`
- Chinese companion: [README.zh.md](README.zh.md)

Inputs:

- Parent A2 follow-on index: [../../README.md](../../README.md)
- MLF-6 structural failure fact writer:
  [../missile_lethality_structural_failure/README.md](../missile_lethality_structural_failure/README.md)
- MLF-7 secondary consequence coupling:
  [../missile_lethality_secondary_consequence_coupling/README.md](../missile_lethality_secondary_consequence_coupling/README.md)
- A8 damage-effect chain:
  [../../../archive/a8_damage_effect_chain/README.md](../../../../../../../README.md)
- Subproject creation standard:
  [../../../../../agent/rules/subproject_creation_standard.md](../../../../../../engineering/automation/rules/subproject_creation_standard.md)
- Realism authority boundary:
  ../../../../../standards/foundation/realism_authority_boundary.zh.md（`git show e8dc0b29~1:docs/standards/foundation/realism_authority_boundary.zh.md`）
- Structural breakup state and event fields:
  [../../../../../../src/components/combat/structural_failure.h](../../../../../../../src/components/combat/structural_failure.h),
  [../../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)
- Ground impact lifecycle and current active-state API:
  [../../../../../../src/components/systems/logistics.h](../../../../../../../src/components/systems/logistics.h),
  [../../../../../../src/core/engine/simulation_kernel_observation_api.cpp](../../../../../../../src/core/engine/simulation_kernel_observation_api.cpp)

## Purpose

MLF-8 is the eighth phase of the Missile Lethality Framework. It turns the
deferred "detached part" and terminal wreck/debris questions into a bounded,
resumable execution surface.

MLF-6 records which structural part detached. MLF-7 projects that breakup into
maintained aircraft damage, platform damage, loss state, and diagnostics. MLF-8
asks the next question: how should detached part labels and terminal airframes
be represented as lifecycle facts, wreck records, or debris records without
claiming calibrated real-world debris throw, Pk, or stock-weapon lethality?

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Structural breakup facts | accepted upstream | `StructuralBreakupEvent.detached_part_ref`, `detached_part_count`, `break_mode`, and `airframe_breakup` exist from MLF-6 | Labels are facts, not world objects yet |
| Secondary consequence bridge | accepted upstream | MLF-7 writes bounded aircraft/platform consequence state and diagnostics | MLF-7 explicitly deferred first-class debris/wreck lifecycle |
| Terminal original entity path | active maintained behavior | Fire/fuel lost aircraft can remain observable during descent and retire after ground impact; `is_unit_active()` now follows `is_alive()` | Original entity retirement is not the same as a reusable wreck/debris object model |
| Lifecycle event contract | accepted / archived | `LifecycleTransitionEvent` carries detached-part and terminal-wreck lifecycle facts with diagnostics-only visibility | Base slice writes lifecycle facts, not first-class debris/wreck entities |
| External debris evidence | fail-closed retained material | Existing TP-21/debris admission artifacts are hash/evidence gates, not admitted calibration data | No selected debris-output authority is released by this subproject setup |

## Scope

In scope:

- Inventory current structural breakup outputs, terminal aircraft lifecycle
  behavior, ground-contact state, event-store support, Python bindings, facade
  export, diagnostics, and reward consumers.
- Define a lifecycle contract for original airframe retirement, terminal wreck
  facts, detached-part debris facts, and optional future debris entities.
- Decide when MLF-8 may use existing `LifecycleTransitionEvent` fields and when
  it needs a separate internal component or entity type.
- Implement only bounded lifecycle representation for detached parts and
  terminal wrecks after the contract is accepted.
- Keep MLF-8 lifecycle events diagnostics-only until a later training or
  calibration gate explicitly promotes them.
- Add focused tests for no-breakup, single detached part, multi-part breakup,
  terminal wreck, event-chain linkage, active-state semantics, and reward
  non-leakage.
- Keep parent README, task clusters, current status, dispatch queue, and
  acceptance records synchronized.

Out of scope:

- No Pk or statistical lethality trend. That remains MLF-9.
- No real-world debris throw distribution, fragment range, or casualty/damage
  probability calibration. That remains MLF-10 or a later evidence gate.
- No weapon-specific or aircraft-specific authoritative debris model.
- No reopening of archived MLF-1 through MLF-7 packages except to fix upstream
  fact bugs.
- No training reward authority from MLF-8 diagnostics unless a future contract
  changes `consumer_visibility` deliberately.
- No naval or ground debris lifecycle model in this slice.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Write surface | Status |
| --- | --- | --- | --- | --- | --- |
| `P0 Boundary` | Create MLF-8 subproject and freeze authority boundaries. | User request to enter MLF-8. | README, task clusters, status, dispatch queue, contract surface, archive placeholder, and parent navigation exist. | docs only | complete / link-pass |
| `P1 Inventory` | Inventory current breakup, lifecycle, event, binding, facade, reward, and diagnostics surfaces. | P0 docs exist. | Inventory identifies reusable fields, gaps, and forbidden direct-write surfaces. | docs/tests docs | complete / inventory-pass |
| `P2 Lifecycle Contract` | Define original-airframe, wreck, debris, and event-chain semantics. | P1 complete. | Contract table states producers, consumers, visibility, and acceptance checks. | docs only | complete / contract-pass |
| `P3 Runtime Representation` | Implement bounded lifecycle state and event writing. | P2 accepted. | Runtime produces deterministic lifecycle facts without Pk, calibration, or reward leakage. | `src/**`, bindings, focused tests | complete / focused-pass |
| `P4 Diagnostics And Facade` | Make MLF-8 facts inspectable through maintained diagnostics/facade surfaces. | P3 focused pass. | Recent events, facade packet, and diagnostic probes expose chain-linked lifecycle rows. | diagnostics/facade/tests | complete / focused-pass |
| `P5 Validation` | Validate structural-to-lifecycle cases and no-false-positive behavior. | P3/P4 complete. | Focused C++/Python lanes cover each accepted lifecycle path. | tests | complete / focused-pass |
| `P6 Regression Smoke` | Ensure air-combat, reward, and training surfaces are not accidentally rewritten. | P5 pass. | Maintained smoke lanes remain green and diagnostics-only facts stay out of reward. | tests only | complete / smoke-pass |
| `P7 Acceptance` | Record accepted/held claims and archive boundary. | P6 pass or residuals held. | Acceptance page and parent indexes state exact MLF-8 proof and deferrals to MLF-9/10. | docs only | complete |

## Task Clusters

- Task cluster plan:
  [missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md](missile_lethality_debris_wreck_lifecycle_task_clusters_20260619.md)
- Current status:
  [missile_lethality_debris_wreck_lifecycle_current_status_20260619.md](missile_lethality_debris_wreck_lifecycle_current_status_20260619.md)
- Inventory:
  [missile_lethality_debris_wreck_lifecycle_inventory_20260619.md](missile_lethality_debris_wreck_lifecycle_inventory_20260619.md)
- Lifecycle contract:
  [missile_lethality_debris_wreck_lifecycle_contract_20260619.md](missile_lethality_debris_wreck_lifecycle_contract_20260619.md)
- Dispatch queue:
  [missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.md](missile_lethality_debris_wreck_lifecycle_dispatch_queue_20260619.md)
- Acceptance gate:
  [missile_lethality_debris_wreck_lifecycle_acceptance_20260619.md](missile_lethality_debris_wreck_lifecycle_acceptance_20260619.md)

## Outputs And Evidence

Accepted outputs:

- This accepted / archived MLF-8 evidence packet.
- A finite task cluster list with round caps.
- P1 inventory of reusable and missing lifecycle surfaces.
- A lifecycle contract that keeps MLF-8 diagnostics separate from reward and Pk
  authority.
- P3 focused implementation of diagnostics-only lifecycle event recording for
  detached parts and chain-linked terminal wreck facts.
- P4/P5 focused diagnostics and validation coverage for facade packet export,
  Python binding/contract shape, diagnostics probe rows, no-breakup behavior,
  single and multi-axis detached-part lifecycle rows, terminal wreck rows, and
  reward non-leakage.
- P6 broad smoke evidence:
  `ctest --test-dir build-workshop --output-on-failure` -> 6 passed;
  `PYTHONPATH=build-workshop:. pytest -q tests/runtime/air_combat tests/runtime/engagement`
  -> 386 passed.
- P7 acceptance package with exact accepted lifecycle claims and retained
  MLF-9/MLF-10 deferrals.
- Parent A2 and air-combat navigation updates plus archive registry sync.

## Acceptance Gate

This subproject is accepted for the diagnostics-only MLF-8 slice because:

- Detached-part and terminal-wreck lifecycle semantics are documented and tested.
- Runtime lifecycle facts are chain-linked to upstream structural/consequence
  evidence.
- Original entity active-state semantics remain correct after terminal loss.
- MLF-8 diagnostics do not create training reward terms by default.
- Parent indexes and archive registry boundaries remain synchronized.
- Pk, real debris throw, selected TP-21 output authority, and weapon-specific
  lethality remain explicitly refused.

## Residuals And Next Steps

Planned follow-ons:

- MLF-9: Pk/statistical trend projection.
- MLF-10: calibration gates for specific weapons/platforms and admitted debris
  evidence.

Held in MLF-8 until evidence exists:

- First-class debris physics beyond simple lifecycle representation.
- Debris-to-secondary-damage interactions.
- Visual debris rendering or particle systems.

## Archive

MLF-8 has been physically archived under the parent A2 local archive and
registered in [../../archive_registry.md](../../../../../../task/review/archive/phase3c_closeout_20260808/archive_registry.md). The
original active path now contains only a lightweight pointer. The local
[archive/](archive/README.md) directory remains only for future superseded
records within this archived evidence packet.
