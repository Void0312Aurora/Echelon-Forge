# A2 Missile Lethality Model Foundation

Status: `2026-06-09` MLF-1A-D accepted; MLF-1E module-boundary acceptance is pending; geometry, fuze, fragmentation, continuous-rod, and structural-breakup models are not implemented yet.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- A2 pointer: [../README.md](../README.md)
- Archived A2 package: [../../archive/a2_high_fidelity_damage_model/README.md](../../archive/a2_high_fidelity_damage_model/README.md)
- A8 damage-effect chain: [../../a8_damage_effect_chain/README.md](../../a8_damage_effect_chain/README.md)
- A2 damage-consequence reward surface: [../damage_consequence_reward_surface/README.md](../damage_consequence_reward_surface/README.md)
- MLF-1 contract: [missile_lethality_chain_contract_20260609.md](missile_lethality_chain_contract_20260609.md)
- MLF-1A field inventory: [missile_lethality_field_inventory_20260609.md](missile_lethality_field_inventory_20260609.md)
- Task clusters: [missile_lethality_model_foundation_task_clusters_20260609.md](missile_lethality_model_foundation_task_clusters_20260609.md)
- CMO-DB proxy source: <https://www.cmo-db.com/en/>

## Purpose

This subproject defines the missing generic missile lethality model stack before
returning to specific weapon/target claims such as AIM-120C versus MQ-9.

The current runtime can connect launch, detonation, effects, damage reports,
damage consequences, and delayed ground-crash terminal handling. That is not yet
a high-fidelity missile lethality model. The next work should standardize the
model layers first, then implement them in order.

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
| 2 | Encounter geometry | miss distance, aspect, local point, closure | partial, needs standardization |
| 3 | Fuze model | trigger reason, delay, reliability, failure state | too coarse |
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

## Next Step

Start with [MLF-1 Chain Contract](missile_lethality_chain_contract_20260609.md):
dispatch field inventory, common header, diagnostic projection, and
consumer-migration tasks. Legacy fields are not a maintained compatibility
surface. Do not tune a specific missile or target until the generic chain
contract and geometry/fuze probe exist.
