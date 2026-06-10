# A2 MLF-3 Warhead Effects And Generic Blast-Fragment Loads

Status: `2026-06-10` MLF-3 standard load chain focused accepted; the high-fidelity missile lethality model remains incomplete. MLF-2 is archived; this subproject opens the third phase separately and must not continue inside archived MLF-1 or MLF-2 folders.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- Current MLF-3 pointer: [../../README.md](../../README.md)
- A2 pointer: [../../../README.md](../../../README.md)
- MLF-1 chain-contract archive: [../../../missile_lethality_model_foundation/README.md](../../../missile_lethality_model_foundation/README.md)
- MLF-2 approach/fuze archive: [../../../missile_lethality_geometry_fuze/README.md](../../../missile_lethality_geometry_fuze/README.md)
- Historical A2 research package: [../../../../archive/a2_high_fidelity_damage_model/README.md](../../../../archive/a2_high_fidelity_damage_model/README.md)
- Warhead parameter entry: [weapon_common.h](../../../../../../../src/components/combat/common/weapon_common.h)
- Event contracts: [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h)
- Current effects model: [default_effects_model.cpp](../../../../../../../src/models/weapons/default_effects_model.cpp)
- Warhead/spatial fragments: [default_effects_warhead_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc), [default_effects_spatial_projection_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)
- Diagnostics probe: [air_combat_stage0_process_probe.py](../../../../../../../tools/diagnostics/air_combat_stage0_process_probe.py)

## Purpose

MLF-3 answers "after the fuze detonates, what load did the warhead apply to the target?" It turns detonation facts into explainable mechanism loads: fragment energy, fragment areal density, blast overpressure, impulse, scaled distance, orientation weighting, spatial coverage, and component load.

This phase does not decide whether the target is killed, fragmented, crashed, or a real AIM-120C outcome. It provides upstream facts for later target vulnerability, component failure, structural breakup, debris, and training consumers.

## Research Data Rule

MLF-3 only admits generic, uncalibrated, replaceable research data. Default models may use public methods, generic blast/fragment formulas, engineering-order values, and category hints from proxy sources such as CMO-DB, but those values must not be written as true AIM-120C, MQ-9, or other type-specific parameters.

Every default parameter must keep a replacement path: source category, evidence level, scope, unit, confidence or uncertainty, replacement rule, and whether it is only for tests or research. Without those labels, a value remains a documentation candidate or test fixture and must not become runtime default authority.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-2 detonation input | accepted / archived | [MLF-2 archive](../../../missile_lethality_geometry_fuze/README.md) | Only proves nearest approach, fuze evaluation, and detonation handoff |
| Warhead profile data | active scaffold | `WarheadProfile`, `WarheadEffectProfile`, `WarheadSpatialProjectionProfile` | Not real warhead-parameter authority |
| Standard event DTOs | live writer / diagnostics / no-detonation gate focused pass | `WarheadMechanismEvent`, `SpatialCoverageEvent`, and `ComponentLoadEvent` exist in contracts, bindings, event-store writers, real detonation-path tests, and diagnostics projection | Parameters are not calibrated; no kill conclusion is emitted |
| Current effects model | generic load-shape + spatial-component projection focused pass | `default_effects_model` has mechanism / spatial / component fields; `test_mlf3_generic_blast_fragmentation_loads.py` pins range / direction / family changes in standard load facts; `test_mlf3_spatial_component_projection.py` pins spatial coverage changing standard component-load facts | Still folded mainly into `EffectsEvent`; default constants do not carry full source category / scope / unit / uncertainty / replacement-rule runtime metadata |
| Historical Phase 3 tests | retained scaffold evidence | `tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py` | Not accepted MLF-3 evidence |

## Scope

In scope:

- Inventory current warhead, spatial projection, and component-load fields and decide which ones move to standard events.
- Write `WarheadMechanismEvent` after detonation.
- Write `SpatialCoverageEvent` for proximity coverage, including sample count, hit fraction, energy/pattern weights, and projected hitbox count.
- Write `ComponentLoadEvent` so later vulnerability and structure models consume load facts.
- Build a generic uncalibrated blast-fragmentation preset and tag all defaults with evidence levels.
- Make diagnostics emit warhead / spatial_coverage / component_load rows per munition.

Out of scope:

- No continuous-rod cutting model; that belongs in MLF-4.
- No structural breakup, airframe fragmentation, or wreck/debris objects; those belong in MLF-6/MLF-8.
- No AIM-120C/MQ-9 or other weapon/target-specific calibration.
- No direct conversion from mechanism load to kill, crash, combat win, or entity deletion.
- No promotion of the historical A2 blast-fragmentation candidate package to stock authority.
- No writing generic research parameters as type-specific truth; type-specific supplements can enter later only with explicit source, evidence level, and replacement records.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `MLF-3A Boundary And Inventory` | Freeze MLF-3 scope and inventory legacy fields/live gaps | MLF-2 archived | README, status, task clusters, dispatch queue, and readable field/gap inventory exist | accepted |
| `MLF-3B Event Writers` | Write standard warhead/spatial/component events | MLF-3A | Detonation emits standard events and parents them to same-chain fuze/effects facts | live gate focused pass |
| `MLF-3C Generic Blast-Fragmentation` | Build generic uncalibrated blast/fragment mechanism loads | MLF-3B | Range, aspect, and family change mechanism loads | focused pass |
| `MLF-3D Spatial Coverage` | Project mechanism load onto hitboxes/components | MLF-3C | Spatial coverage and component load are diagnosable from standard events | focused pass |
| `MLF-3E Diagnostics Projection` | Emit warhead/spatial/component rows from the probe | MLF-3B-D | Mechanism reasons can be read without old `EffectsEvent` projection | focused pass |
| `MLF-3F Runtime Handoff Gate` | Ensure only detonation enters warhead effects | MLF-3B-E | No-detonation has no warhead load; detonation has one standard load chain | focused pass |
| `MLF-3G Acceptance And Archive Prep` | Summarize evidence, residuals, and follow-on phases | MLF-3B-F pass | accepted/held state matches evidence | focused pass |

## Task Clusters

- Task cluster plan: [missile_lethality_warhead_effects_task_clusters_20260609.md](missile_lethality_warhead_effects_task_clusters_20260609.md)
- Current status: [missile_lethality_warhead_effects_current_status_20260609.md](missile_lethality_warhead_effects_current_status_20260609.md)
- Dispatch queue: [missile_lethality_warhead_effects_dispatch_queue_20260609.md](missile_lethality_warhead_effects_dispatch_queue_20260609.md)
- Inventory acceptance: [missile_lethality_warhead_effects_inventory_20260609.md](missile_lethality_warhead_effects_inventory_20260609.md)
- Closeout acceptance: [missile_lethality_warhead_effects_acceptance_20260610.md](missile_lethality_warhead_effects_acceptance_20260610.md)

## Outputs And Evidence

Expected outputs:

- Standard warhead-mechanism event after detonation.
- Standard spatial-coverage event.
- Standard component-load event.
- Generic blast-fragmentation defaults with evidence levels.
- Diagnostics rows for warhead / spatial_coverage / component_load.
- Focused tests showing that distance, aspect, or family changes alter mechanism load and coverage.
- Focused tests showing that spatial coverage / local projection changes standard component-load facts.

## Acceptance Gate

This subproject can be marked accepted only when:

- No-detonation paths do not create warhead effects.
- Detonation paths write same-chain warhead, spatial_coverage, and component_load standard events.
- Fragment/blast loads vary with range, direction, spatial coverage, and family instead of acting as one damage scalar.
- Diagnostics explain which components received which loads without calling that a kill.
- All defaults carry evidence levels such as `synthetic`, `engineering_assumption`, `cmo_db_proxy`, or `public_method_reference`.
- Structural breakup, debris/wreck, Pk, and weapon-specific calibration remain held.

## Residuals And Next Steps

- MLF-4: continuous-rod / cutting mechanism.
- MLF-5: target vulnerability and component failure probabilities.
- MLF-6: structural breakup and airframe fragmentation.
- MLF-8: wreck/debris lifecycle.
- MLF-9: Pk/statistical trend layer.

## Archive

Archive index: [../README.md](../README.md)

The current [../../README.md](../../README.md) remains a lightweight pointer
only. This evidence package only proves generic post-detonation load facts; it
does not prove component failure, structural breakup, debris/wreck, Pk, crash,
or weapon-specific lethality.
