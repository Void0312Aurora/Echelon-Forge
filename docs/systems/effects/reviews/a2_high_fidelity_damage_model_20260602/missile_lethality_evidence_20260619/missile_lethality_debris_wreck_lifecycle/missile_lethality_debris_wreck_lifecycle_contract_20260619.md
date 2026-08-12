# MLF-8 Lifecycle Contract

Status: `2026-06-19` P2 contract-pass for the base MLF-8 lifecycle slice. This
accepts the contract for the next implementation step, but it does not accept
runtime behavior yet.

Chinese companion:
[missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_contract_20260619.zh.md).

## Contract Boundary

MLF-8 may turn accepted structural breakup and terminal lifecycle facts into
diagnostic lifecycle records. It must not turn those records into calibrated
debris physics, Pk, or reward authority by default.

The base slice is intentionally thin: use `LifecycleTransitionEvent`, write no
first-class wreck/debris ECS entities, and keep all MLF-8 rows
`diagnostics_only` until a later authority-promotion explicitly changes
consumer visibility.

## P2 Decisions

| Decision | Accepted answer | Reason |
| --- | --- | --- |
| Event carrier | Use existing `LifecycleTransitionEvent` for the base slice. | DTO, Python bindings, facade packets, and recent-event packet storage already exist. |
| New ECS debris/wreck component | Do not add one in the base slice. | MLF-8 starts as lifecycle bookkeeping, not first-class debris physics. |
| Detached-part representation | Emit one aggregate lifecycle row per new `StructuralBreakupEvent`. | MLF-6 emits one structural event per newly detached group; that parent event carries `detached_part_ref`. |
| Detached-part label location | Do not duplicate `detached_part_ref` in lifecycle fields. Resolve it through `parent_event_id` to the structural event. | Avoid overloading lifecycle strings with pseudo-physics. |
| Terminal wreck scope | Base MLF-8 emits terminal wreck lifecycle rows only when the target has chain-linked missile structural/consequence evidence. Plain landing/crash ground contact remains existing ground lifecycle behavior. | Keeps MLF-8 in missile lethality scope and avoids taking over general ground-contact authority. |
| Writer ownership | Add lifecycle write support to the maintained engagement event recorder/store, then call it from the accepted structural/ground transition points. | Reuses existing chain-header and recent-event infrastructure. |
| Reward visibility | All base MLF-8 rows use `diagnostics_only`; reward must ignore diagnostics-only lifecycle rows before any writer is enabled. | P1 found reward already consumes lifecycle events unless guarded. |
| First-class wreck entity | Forbidden in the base slice; `wreck_entity` stays zero. | No maintained non-combat wreck entity identity exists yet. |
| Debris physics | Forbidden in the base slice. | No selected debris-output evidence is admitted. |

## Accepted Lifecycle Rows

| Row | Producer input | Lifecycle output | Header / visibility | Acceptance note |
| --- | --- | --- | --- | --- |
| Detached-part debris fact | New `StructuralBreakupEvent` with non-empty `detached_part_ref` or `detached_part_count > 0` | `lifecycle_from=attached_airframe_part`, `lifecycle_to=detached_part_debris_fact`, `ground_lifecycle=unknown`, `debris_count=detached_part_count`, `terminal=false`, `terminal_projection_id=<structural_event_id>` | `stage=lifecycle`, `parent_event_id=<structural_event_id>`, `consumer_visibility=diagnostics_only` | Parent structural event remains the source of the detached-part label and cause chain. |
| Airframe breakup debris summary | `StructuralBreakupEvent.airframe_breakup == true` | Same lifecycle row shape as detached-part debris fact, with cumulative `debris_count` from the structural event | `diagnostics_only` | This summarizes breakup bookkeeping only; it is not a direct crash/delete rule. |
| Terminal original-airframe wreck fact | Chain-linked `PlatformConsequenceEvent` / structural evidence plus transition to `GroundImpactLifecycle::CrashedWreck` or `DebrisFragmentResidue` | `lifecycle_from=lost_airframe_observable`, `lifecycle_to=ground_crashed_wreck`, `ground_lifecycle=crashed_wreck`, `debris_count=0`, `terminal=true`, `terminal_projection_id=<parent consequence or structural event id>` | `stage=lifecycle`, `consumer_visibility=diagnostics_only` | Original entity liveness still follows `is_alive()`; the lifecycle row is a diagnostic fact, not a replacement entity. |

## Explicitly Held Rows

| Held row | Destination | Reason |
| --- | --- | --- |
| Per-fragment rows | Future MLF-8 extension | Base evidence has group labels and cumulative counts, not fragment inventory. |
| First-class wreck entity | Future MLF-8 extension after entity contract | No non-combat wreck identity, targeting restrictions, or lifecycle owner exists. |
| Debris-to-secondary-damage interaction | Future MLF-8 extension or later calibration gate | Would imply physics and damage authority not present in the base slice. |
| General non-missile ground crash lifecycle | Separate ground-contact lifecycle work | Not all crashes are MLF missile-lethality facts. |
| Pk/statistical projection | MLF-9 | Requires a separate trend/probability contract. |
| Calibrated debris throw or selected debris-output authority | MLF-10 or later evidence gate | TP-21 selected outputs remain fail-closed. |

## Runtime Requirements For P3

- Add a recorder/store path for `LifecycleTransitionEvent`.
- Complete headers with `stage=lifecycle`, chain id, parent event id, target ref,
  producer id, observation mode, and `diagnostics_only` visibility.
- Cap and sort lifecycle rows in recent-event export.
- Emit detached-part lifecycle facts exactly once for each accepted structural
  breakup event.
- Emit terminal wreck lifecycle facts exactly once for a chain-linked original
  aircraft when ground lifecycle first reaches crashed-wreck/residue state.
- Keep `wreck_entity` zero and do not spawn entities.
- Ensure reward ignores diagnostics-only lifecycle rows before enabling any
  MLF-8 writer.

## Required Tests

P3/P5 must prove:

- no-breakup inputs produce no lifecycle rows;
- a single wing/tail/engine/fuselage detachment produces one diagnostics-only
  detached-part lifecycle row linked to the structural event;
- multi-axis / airframe breakup produces a bounded aggregate lifecycle row;
- terminal ground wreck after chain-linked structural/consequence evidence
  produces one diagnostics-only terminal row;
- diagnostics-only lifecycle rows do not neutralize reward terminal state and do
  not add reward terms;
- promoted non-diagnostics lifecycle rows keep the existing reward behavior, if
  that future path is intentionally exercised;
- `is_unit_active()` remains the liveness authority for the original entity.

## Forbidden Outputs

- Reward terms from MLF-8 diagnostics.
- Pk, casualty, or real-world damage probability.
- Selected TP-21 debris output authority before evidence admission.
- Weapon-specific or aircraft-specific debris calibration.
- Reopening archived MLF-6/7 implementation without a fact bug.
