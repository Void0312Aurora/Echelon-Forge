# A2 Missile Lethality Model Foundation

Status: `2026-06-09` archived / MLF-1A-E accepted, `MLF-1 Chain Contract` accepted. Geometry, fuze, fragmentation, continuous-rod, and structural-breakup models are not continued inside this subproject.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- Current MLF pointer: [../../README.md](../../README.md)
- A2 pointer: [../../../README.md](../../../README.md)
- Archived A2 package: [../../../../archive/a2_high_fidelity_damage_model/README.md](../../../../archive/a2_high_fidelity_damage_model/README.md)
- A8 damage-effect chain: [../../../../a8_damage_effect_chain/README.md](../../../../a8_damage_effect_chain/README.md)
- A2 damage-consequence reward surface: [../../../damage_consequence_reward_surface/README.md](../../../damage_consequence_reward_surface/README.md)
- MLF-1 contract: [missile_lethality_chain_contract_20260609.md](missile_lethality_chain_contract_20260609.md)
- MLF-1A field inventory: [missile_lethality_field_inventory_20260609.md](missile_lethality_field_inventory_20260609.md)
- Task clusters: [missile_lethality_model_foundation_task_clusters_20260609.md](missile_lethality_model_foundation_task_clusters_20260609.md)
- CMO-DB proxy source: <https://www.cmo-db.com/en/>

## Purpose

This subproject defines and closes the `MLF-1 Chain Contract` slice before
returning to specific weapon/target claims such as AIM-120C versus MQ-9.

The current runtime can connect launch, detonation, effects, damage reports,
damage consequences, and delayed ground-crash terminal handling. That is not yet
a high-fidelity missile lethality model. This subproject standardizes the event,
diagnostic, and training-consumer boundary for the model layers; it does not
carry the MLF-2+ implementation waves.

After MLF-1 acceptance, this subproject should be archived instead of extended
with MLF-2 work. MLF-2 must be created as a separate task subproject under the
`docs/agent` subproject standard, with its own goal, scope, task clusters, and
acceptance gate before controlled probes or runtime edits start.

## Boundaries

In scope:

- Model responsibilities, inputs, outputs, and acceptance order.
- Generic pre-calibrated or uncalibrated model scaffolds.
- Evidence/authority labels for official/public evidence, CMO-DB proxy data,
  engineering assumptions, training-synthetic data, and uncalibrated values.
- A high-fidelity chain that produces concrete damage before training consumes
  the result.

Out of scope:

- Presenting CMO-DB, public web pages, forum posts, or training results as
  official test data, classified values, or unmarked real-world authority.
- Replacing the damage chain with direct crash/delete rules.
- Treating Pk as a substitute for high-fidelity damage.
- Further tuning AIM-120C/MQ-9 breakup before the generic foundation exists.

## Proxy Data Sources

CMO-DB may be used as a high-value proxy source under public-data constraints.
It exposes searchable Command: Modern Operations DB3000 equipment data and can
fill many details that are otherwise unavailable in open sources.

Usage rules:

- It may directly provide default parameters, order-of-magnitude constraints,
  category mappings, and relative differences: platform size/speed/altitude,
  weapon range class, seeker/fuze category, warhead category, sensor category,
  and loadout relationships.
- It may seed weapon/target-specific proxy calibration, but the value must be
  labeled with `evidence_level=cmo_db_proxy` or an equivalent authority tag.
- Every mapping must record CMO-DB version, entry name or URL, field name, unit,
  access date, mapping rule, and any manual adjustment.
- Conflicts with official manuals, manufacturer material, or official game
  database notes should be retained and escalated for review.
- CMO-DB values must not be described as real test values, classified
  parameters, or official kill probability. They are usable engineering proxy
  parameters, not unmarked truth.

So the corrected rule is: CMO-DB data can and often should fill missing values.
The restriction is annotation and provenance, not a ban on direct use.

## Ordered Model Stack

| Order | Model | Main output | Status |
| --- | --- | --- | --- |
| 0 | Evidence and authority model | authority labels | must come first |
| 1 | Kill-chain contract | standardized events and diagnostics | must come first |
| 2 | Encounter geometry | miss distance, aspect, local point, closure | future separate MLF-2 subproject |
| 3 | Fuze model | trigger reason, delay, reliability, failure state | future separate MLF-2 subproject |
| 4 | Warhead mechanism model | blast, fragment, continuous-rod/cutting loads | missing generic scaffold |
| 5 | Spatial coverage model | exposure and mechanism load per component | needs directionality |
| 6 | Target geometry/component model | hitbox and component map | partial |
| 7 | Vulnerability/failure model | failure modes and severities | partial, needs authority labels |
| 8 | Structural failure model | breakup, severed parts, detached engines | major gap |
| 9 | Secondary consequences | fire, leak, control, engine consequences | partial |
| 10 | Flight-dynamics coupling | aero/propulsion/control/mass modifiers | must use existing dynamics |
| 11 | Wreck/debris lifecycle | wreck and debris entities | major gap |
| 12 | Pk/statistical layer | low-fidelity mode and trend checks | later |
| 13 | Diagnostics/replay | probes and replay summaries | needed at every stage |

## Work Order

The table below is the overall roadmap for the generic missile lethality model.
It does not mean this subproject continues into MLF-2 implementation. The
current `missile_lethality_model_foundation/` subproject is limited to `MLF-1
Chain Contract` standardization: fields, diagnostics, consumers, and module
boundaries. After MLF-1 is accepted, this folder should move toward archive
closure. `MLF-2 Geometry And Fuze` and later stages must be created as separate
subprojects under the `docs/agent` subproject standard.

| Stage | Goal | Exit condition |
| --- | --- | --- |
| `MLF-0 Boundary` | Freeze scope and forbidden claims | this README and A2 pointer exist |
| `MLF-1 Chain Contract` | Define event and diagnostic fields | chain field map exists |
| `MLF-2 Geometry And Fuze` | Split encounter geometry from fuze behavior | controlled probes explain trigger state |
| `MLF-3 Generic Fragmentation` | Add a generic uncalibrated fragmentation model | distance/aspect changes component exposure |
| `MLF-4 Continuous-Rod / Cutting` | Add a generic cutting mechanism | wing/tail/fuselage cuts are expressible |
| `MLF-5 Target Vulnerability` | Standardize component maps and vulnerability rows | rows are machine-readable and authority-labeled |
| `MLF-6 Structural Failure` | Support breakup and major part separation | high-severity hits can produce non-whole-airframe outcomes |
| `MLF-7 Secondary Consequence Coupling` | Route damage through fire/fuel/control/engine dynamics | consequences flow through maintained runtime |
| `MLF-8 Debris And Wreck Lifecycle` | Represent post-breakup objects | wreck/debris semantics are observable |
| `MLF-9 Statistical Layer` | Add low-fidelity Pk/trend checks | Pk does not override high-fidelity events |
| `MLF-10 Calibration Gates` | Return to specific weapon/target cases | values retain evidence labels |

## Future MLF-2 Subproject Objective Draft

This section records the future subproject objective only. It does not start
MLF-2 inside the current subproject and does not authorize runtime, probe, or
parameter edits here.

The future MLF-2 objective should be to split "the missile reached the target
area" into two explainable steps: reproduce nearest-approach geometry first, then
explain fuze evaluation. Given range, aspect, altitude offset, closure, and
target attitude, diagnostics should explain why the fuze triggered, did not
trigger, triggered late, or failed. The result is handed to later warhead-effect
models; MLF-2 should not decide target destruction by itself.

Suggested scope:

- Build controlled geometry scenarios or fixtures across range, aspect, speed,
  and target attitude.
- Emit stable `NearestApproachEvent` and `FuzeEvaluationEvent` rows that separate
  contact, proximity, not-armed, missed-window, delay, and failure cases.
- Label every default range, radius, delay, reliability, or signature assumption
  with source, evidence grade, and applicability.
- Pass detonation state to later warhead-effect models without creating
  fragmentation, continuous-rod, structural-breakup, or training-win conclusions.

Non-goals:

- No real AIM-120C/MQ-9 Pk or case conclusion.
- No fragmentation, continuous-rod, structural-breakup, wreck/debris, or Pk
  statistical layer implementation.
- No new reward rule that replaces event-chain conclusions.

Entry conditions:

- The current MLF-1 subproject has been archived, and the parent A2 navigation
  says MLF-1 is complete while MLF-2 is a separate subproject.
- The new MLF-2 directory follows the `docs/agent` standard: README, finite task
  clusters, current status, acceptance gates, and archive boundary.
- Diagnostic fields and controlled scenario design are accepted before runtime
  edits begin.

Exit conditions:

- Different range, aspect, speed, and attitude cases produce explainable trigger,
  no-trigger, delay, or failure results.
- No-detonation cases still report a reason instead of disappearing silently.
- Contact and proximity decisions are recorded separately, and old
  `last_effect_*` fields are not expanded into a long-term compatibility surface.

## MLF-1E Module-Boundary Acceptance

`MLF-1E` result: pass. Do not split out `src/runtime/contracts/lethality_chain_contracts.h` yet; keep the lethality-chain DTOs as a distinct section inside `src/runtime/contracts/engagement_contracts.h`. MLF-1 is still a field-contract and consumer-migration slice, and `RecentEngagementEvents`, facade packets, and Python bindings already use the current contract header. Moving the file now would mainly create include and binding churn. Reconsider the split after standard DTO event-store writers land, or when later standalone MLF-2/MLF-3 subprojects create clear independent ownership for geometry, fuze, warhead, and component-load contracts.

Accepted responsibility boundaries:

- Contracts contain only data structures and headers, not physics calculations or kill decisions.
- The event store records, orders, links, and exports events only. Standard `PlatformConsequenceEvent` / `LifecycleTransitionEvent` writers remain future implementation work, not MLF-1E physics logic.
- Diagnostics only project rows keyed by `chain_id + event_id + stage`; existing `EffectsEvent` / `DamageReport` rows are explicitly transitional projections.
- Reward and terminal logic only consume fact projections. They prefer standard platform-consequence and lifecycle events; old `DamageReport.platform_damage_state_delta` parsing remains confined to the transitional fallback.
- Geometry, fuze, fragmentation, continuous-rod, structural breakup, wreck/debris entities, and AIM-120C/MQ-9-specific tuning are out of MLF-1E.

Legacy deletion conditions are clear enough: once the runtime event store writes `PlatformConsequenceEvent` and `LifecycleTransitionEvent` for live scenarios, delete the `DamageReport` fallback and `platform_damage_state_delta` parsing path. Until then, `DamageReport` may remain as source inventory or a transitional projection, but it is not a long-term compatibility promise.

## Next Step

The next step for this subproject is accepted/archive closure, not MLF-2 work.
MLF-2 must be created later as a separate subproject under the `docs/agent`
subproject standard; controlled approach-geometry and fuze probes belong there.
Legacy fields are not a maintained compatibility surface. Do not write further
weapon-specific, geometry/fuze, or kill-threshold implementation in this
subproject.
