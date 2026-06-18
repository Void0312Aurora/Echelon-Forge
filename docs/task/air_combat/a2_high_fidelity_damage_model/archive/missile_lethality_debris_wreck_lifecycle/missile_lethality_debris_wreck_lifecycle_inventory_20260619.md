# MLF-8 Debris And Wreck Lifecycle Inventory

Status: `2026-06-19` P1 inventory pass. This is a read-only source inventory;
it does not accept any runtime behavior change.

Chinese companion:
[missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md](missile_lethality_debris_wreck_lifecycle_inventory_20260619.zh.md).

## Summary

MLF-8 does not need a second aircraft-damage model. MLF-6 already writes
detached-part structural facts, and MLF-7 already projects those facts into
aircraft/platform consequence state. The remaining gap is narrower: no runtime
owner currently writes chain-linked `LifecycleTransitionEvent` rows for terminal
wrecks or detached-part debris, and reward/runtime consumers are not yet safe
for diagnostics-only MLF-8 lifecycle rows.

## Inventory Table

| Surface | Current owner | Current capability | Reusable for MLF-8 | Gap / guard before runtime |
| --- | --- | --- | --- | --- |
| Structural breakup state | [structural_failure.h](../../../../../../src/components/combat/structural_failure.h) | `StructuralBreakupState` stores breakup phase, active break modes, active structural groups, detached part count, airframe breakup, and last breakup event id. | Yes. It is the state input for detached-part lifecycle facts. | It has counts and group masks, not per-fragment mass, velocity, or world identity. |
| Structural breakup event writer | [structural_failure_system.h](../../../../../../src/systems/combat/structural_failure_system.h) | Emits `StructuralBreakupEvent` with `break_mode`, `detached_part_ref`, `detached_part_count`, `airframe_breakup`, cause linkage, and chain header. | Yes. This is the parent event source for MLF-8 debris facts. | MLF-8 must not reinterpret labels as calibrated debris physics. |
| Structural consequence bridge | [structural_consequence_system.h](../../../../../../src/systems/combat/structural_consequence_system.h) | Applies wing/tail/engine/fuselage/multi-axis consequences through maintained aircraft/platform damage state and records diagnostics-only `PlatformConsequenceEvent`. | Yes. It proves aircraft-body consequence handling already belongs to MLF-7. | Do not duplicate consequence logic in MLF-8. |
| Lifecycle event contract | [engagement_contracts.h](../../../../../../src/runtime/contracts/engagement_contracts.h) | Defines canonical `lifecycle` stage and `LifecycleTransitionEvent` with from/to state, ground lifecycle, wreck entity, debris count, terminal flag, and terminal projection id. | Yes. This is the likely base event shape. | It is only a DTO today; no recorder/write path owns it. |
| Event packet storage | [engagement_event_types.h](../../../../../../src/core/engine/engagement_event_types.h) | `RecentEngagementEvents` already contains `lifecycle_transition_events`. | Yes. Existing packets can carry MLF-8 rows. | Event store has no lifecycle record API, cap, or sort path yet. |
| Event recorder interface | [engagement_event_recorder.h](../../../../../../src/core/interfaces/engagement_event_recorder.h) | Recorder owns damage, component, structural, and platform-consequence event writes. | Partial. Pattern exists. | No `EngagementLifecycleTransitionEventRecord` and no `record_lifecycle_transition_event`. |
| Event store implementation | [simulation_kernel_engagement_event_store.cpp](../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Completes headers and chain linkage for structural and platform consequence events. | Partial. Existing helper style can be reused. | No lifecycle writer; sorted export does not currently sort lifecycle rows because none are written. |
| Ground impact lifecycle | [logistics.h](../../../../../../src/components/systems/logistics.h), [ground_contact_system.h](../../../../../../src/systems/physics/ground_contact_system.h) | `GroundImpactLifecycle` distinguishes `None`, `LandedAirframe`, `CrashedWreck`, and `DebrisFragmentResidue`; ground contact records impact speed, sink rate, and severity. | Yes for terminal-wreck facts. | It describes original entity ground state, not detached debris entities. |
| Active-state API | [simulation_kernel_observation_api.cpp](../../../../../../src/core/engine/simulation_kernel_observation_api.cpp) | `is_unit_active()` follows Flecs liveness via `is_alive()`. | Yes. It is the active-state truth source after terminal retirement. | MLF-8 must not make a dead original entity look active through a wreck fact. |
| Ground debug API | [simulation_kernel_observation_api.cpp](../../../../../../src/core/engine/simulation_kernel_observation_api.cpp), [bindings_core.cpp](../../../../../../src/interfaces/python/bindings_core.cpp) | `debug_get_ground_contact_state()` exports lifecycle and impact fields to Python. | Yes for tests and diagnostics. | It is debug state, not an event-chain record. |
| Runtime facade | [runtime_facade_types.h](../../../../../../src/runtime/facade/runtime_facade_types.h), [runtime_facade_packet.cpp](../../../../../../src/runtime/facade/runtime_facade_packet.cpp) | Facade packets include lifecycle transition events and assign world index for headers and `wreck_entity`. | Yes. Existing facade path can expose MLF-8 facts. | No producer currently fills these rows. |
| Python bindings | [bindings_runtime.cpp](../../../../../../src/interfaces/python/bindings_runtime.cpp), [bindings_core.cpp](../../../../../../src/interfaces/python/bindings_core.cpp) | `LifecycleTransitionEvent` and `lifecycle_transition_events` are public to Python. | Yes. P4 can focus on tests and diagnostics rather than new binding shape. | Shape tests should be extended to cover `terminal` and `terminal_projection_id` if P2 keeps them normative. |
| Structural diagnostics | [structural_breakup_export.py](../../../../../../tools/diagnostics/structural_breakup_export.py) | Exports structural breakup rows and explicitly marks wreck/debris lifecycle as false. | Yes as the upstream structural source. | Needs a separate MLF-8 lifecycle export/probe if lifecycle rows become runtime facts. |
| Reward standard facts | [air_combat.py](../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py) | Skips diagnostics-only `PlatformConsequenceEvent`, but consumes all `LifecycleTransitionEvent` rows as standard damage facts and terminal-state facts. | No, not until guarded. | P2/P3 must add a diagnostics-only guard or specify a non-reward event shape before runtime emits MLF-8 diagnostics. |
| Ground reward shaping | [air_combat.py](../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py), [test_air_combat_reward_surface.py](../../../../../../tests/runtime/air_combat/test_air_combat_reward_surface.py) | Direct ground state can already drive `ground_crashed_wreck` terminal state and reward shaping. | Useful as existing behavior evidence. | MLF-8 lifecycle facts must not double-count or silently add reward authority. |
| Existing no-lifecycle tests | [test_continuous_rod_surface.py](../../../../../../tests/runtime/air_combat/test_continuous_rod_surface.py), [test_warhead_component_event_surface.py](../../../../../../tests/runtime/air_combat/test_warhead_component_event_surface.py) | Earlier MLF tests assert lifecycle events remain empty. | Yes as non-regression checks. | P3 must update or preserve these expectations only with explicit MLF-8 contract evidence. |
| External debris evidence | [test_benchmark_evidence_admission.py](../../../../../../tests/architecture/damage_model/test_benchmark_evidence_admission.py) | TP-21 selected debris outputs remain fail-closed / hash-gated. | Boundary evidence only. | No calibrated debris output may enter MLF-8 without a later evidence gate. |

## Accepted P1 Conclusions

1. MLF-8 should be a thin lifecycle-event layer first, not a new damage or
   aerodynamics model.
2. `LifecycleTransitionEvent` is the best initial carrier, but it lacks a
   runtime writer and chain-linking policy.
3. Detached-part facts should consume `StructuralBreakupEvent.detached_part_ref`
   and `detached_part_count`; they should not create first-class ECS entities in
   the base slice.
4. Terminal-wreck facts should consume original entity ground lifecycle and
   active-state semantics; they should not replace the original entity liveness
   rule.
5. The reward path is the main pre-runtime guard: lifecycle events are not
   currently filtered by `diagnostics_only`.

## P2 Contract Inputs

P2 must decide:

- whether base MLF-8 uses only `LifecycleTransitionEvent`;
- whether to emit one aggregate detached-part row or per-detached-part rows;
- how to set `consumer_visibility` so diagnostics-only rows do not enter reward;
- how to chain lifecycle rows to `StructuralBreakupEvent` and/or
  `PlatformConsequenceEvent`;
- whether terminal ground contact without structural breakup belongs in MLF-8;
- which tests prove no reward leakage and no false positives.

## Runtime Blockers

- Add or explicitly reject a lifecycle event recorder API.
- Add event-store cap/sort/header completion for lifecycle rows if a writer is
  accepted.
- Add reward non-leakage behavior before diagnostics-only lifecycle facts are
  emitted.
- Add focused tests for no-breakup, detached-part, terminal wreck,
  diagnostics-only filtering, and active-state semantics.
