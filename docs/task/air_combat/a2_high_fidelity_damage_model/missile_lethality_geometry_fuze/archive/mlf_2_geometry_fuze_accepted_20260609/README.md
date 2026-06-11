# A2 MLF-2 Missile Approach Geometry And Fuze Evaluation

Status: `2026-06-09` archived / MLF-2 accepted. MLF-2B controlled geometry, MLF-2C nearest-approach events, MLF-2D fuze-evaluation events, MLF-2E diagnostics projection, MLF-2F runtime handoff gate, and MLF-2G closeout are accepted.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- Current MLF-2 pointer: [../../README.md](../../README.md)
- A2 pointer: [../../../README.md](../../../README.md)
- MLF-1 archived pointer: [../../../missile_lethality_model_foundation/README.md](../../../missile_lethality_model_foundation/README.md)
- MLF-1 accepted evidence package: [../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md](../../../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md)
- Archived A2 package: [../../../../archive/a2_high_fidelity_damage_model/README.md](../../../../archive/a2_high_fidelity_damage_model/README.md)
- Weapon lifecycle entry: [simulation_kernel_weapon_release_service.cpp](../../../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp)
- Weapon/fuze parameters: [weapon.h](../../../../../../../src/components/combat/weapon.h)
- Event contracts: [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)
- Event store: [simulation_kernel_engagement_event_store.cpp](../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- Diagnostics probe: [air_combat_weapon_employment_process_probe.py](../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)

## Purpose

MLF-2 splits "what happened when the missile reached the target area" into two explainable steps: nearest-approach geometry first, then fuze evaluation. Given range, aspect, closure, altitude offset, and target attitude, the system should explain why the fuze triggered, did not trigger, triggered late, or failed.

This subproject does not answer whether an AIM-120C would shred an MQ-9, and it does not produce a kill result. It passes detonation state, detonation position, trigger reason, and failure reason to later warhead-effect models. Fragmentation, continuous rod, structural breakup, debris/wreck objects, Pk, and weapon-specific calibration are later standalone subprojects.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-1 kill-chain contract | accepted / archived | MLF-1 evidence package is archived | Defines chain and consumer boundaries only; no geometry/fuze physics |
| Current proximity behavior | active legacy surface | Weapon lifecycle and effects events already carry proximity/direct-hit fields | Still does not fully explain no-trigger, delay, failure, or contact/proximity differences |
| MLF-2 subproject | accepted / archived | This README, task clusters, status, dispatch queue, `MLF-2B`/`MLF-2C`/`MLF-2D`/`MLF-2E`/`MLF-2F` focused tests, and `MLF-2G` closeout | Nearest-approach, fuze-evaluation, diagnostics projection, and runtime handoff gate are accepted; warhead effects are out of scope |

## Scope

In scope:

- Build controlled approach scenarios or fixtures that can fix range, aspect, closure, altitude offset, and target attitude.
- Standardize `NearestApproachEvent`: nearest time, distance, target-local coordinates, relative speed, aspect, confidence, and failure reason.
- Standardize `FuzeEvaluationEvent`: armed state, trigger type, trigger time, trigger/no-trigger/delay/failure reason, contact decision, and proximity decision.
- Make diagnostics distinguish "no detonation with reason" from "no event exists".
- Keep source, evidence grade, and applicability for default fuze radius, delay, reliability, target signature, and similar assumptions.

Out of scope:

- No fragmentation, continuous rod, blast load, structural breakup, debris/wreck, or Pk layer.
- No conversion from fuze trigger directly to target kill.
- No AIM-120C/MQ-9-specific lethality threshold tuning.
- No new reward rule replacing event-chain facts.
- No long-term compatibility surface for old `last_effect_*` fields.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `MLF-2A Boundary` | Freeze objective, forbidden claims, and task clusters | MLF-1 is archived | README, status, task clusters, and parent navigation exist | pass |
| `MLF-2B Geometry Fixtures` | Design controlled approach scenarios | MLF-2A | Tests can vary range, aspect, speed, and attitude | pass |
| `MLF-2C Nearest Approach` | Write nearest-approach events | MLF-2B | No-detonation cases still record nearest approach and reason | pass |
| `MLF-2D Fuze Evaluation` | Write fuze-evaluation events | MLF-2C | Contact, proximity, not-armed, missed-window, delay, and failure are separate | pass |
| `MLF-2E Diagnostics` | Export readable diagnostics | MLF-2C/2D | Probe can emit geometry and fuze rows per munition | pass |
| `MLF-2F Runtime Gate` | Wire into the existing launch/effects chain | MLF-2D/2E | Detonation state reaches later effects model; no-trigger cases do not silently disappear | pass |
| `MLF-2G Closure` | Accept and sync parent navigation | MLF-2B-F pass | Current status, residuals, and archive boundary agree | pass |

## Task Clusters

- Task cluster plan: [missile_lethality_geometry_fuze_task_clusters_20260609.md](missile_lethality_geometry_fuze_task_clusters_20260609.md)
- Current status: [missile_lethality_geometry_fuze_current_status_20260609.md](missile_lethality_geometry_fuze_current_status_20260609.md)
- Dispatch queue: [missile_lethality_geometry_fuze_dispatch_queue_20260609.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.md)

## Outputs And Evidence

Accepted runtime and diagnostics evidence:

- This README fixes goals and boundaries.
- The task-cluster document limits the work packages.
- The current-status document records that MLF-2B through MLF-2G are accepted.
- The dispatch queue records completed `MLF-2G-C1` and no remaining active packets.
- Controlled geometry tests can vary range, closure, aspect, and altitude offset.
- Nearest-approach events are live-written; no-detonation and miss paths record nearest point and reason.
- Nearest-point time now comes from the nearest-point update moment instead of the later terminal decision frame.
- Fuze-evaluation events now record armed/triggered, no-trigger, and failure reasons, and link to the same munition's nearest-approach event.
- The diagnostics probe prioritizes standard nearest-approach and fuze-evaluation events; old `EffectsEvent` projection is fallback only.
- Runtime handoff gate behavior is covered by focused tests: triggered paths produce existing effects/damage records, contact near-miss has no effects/damage record, and reliability failure has only a zero-damage transitional record.

Held items retained by this package:

- Timed-fuze standard event coverage is still not implemented.
- Max-flight-time / guidance expiry still lacks recorder access.
- Zero-damage transitional `EffectsEvent` / `DamageReport` records remain until downstream consumers migrate.
- Controlled geometry tests can still be extended for delay and more target-attitude paths.

## Acceptance Gate

This subproject is marked accepted under these conditions:

- Launch, nearest approach, fuze evaluation, and later effects events for the same munition can be linked by stable ids.
- Range, aspect, speed, and attitude changes affect trigger/no-trigger/delay/failure outcomes, and diagnostics explain why.
- Contact hit and proximity trigger decisions are recorded separately.
- No-detonation cases still have readable reasons instead of merely lacking effects events.
- Detonation state is handed to later warhead-effect models and does not directly produce breakup, crash, or training win/loss.
- Evidence grades and default-parameter sources are traceable.

## Residuals And Next Steps

- MLF-2 is archived; no further dispatch continues in this folder.
- Fragmentation, continuous rod, structural breakup, debris/wreck, and Pk remain MLF-3+ work.
- Specific AIM-120C/MQ-9 conclusions should wait until MLF-2 and at least one later warhead-effect model pass.

## Archive

Archive index: [../README.md](../README.md)

The current [../../README.md](../../README.md) remains a lightweight pointer
only. This evidence package only proves that missile approach geometry and fuze
evaluation are observable, diagnosable, and accepted; it does not prove warhead
effects, target fragmentation, crash, Pk, or weapon-specific lethality.
