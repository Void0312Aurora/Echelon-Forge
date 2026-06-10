# A2 MLF-4 Continuous-Rod Cutting Mechanism

Status: `2026-06-10` active planning / `MLF-4A-X1` read-only inventory accepted. This subproject plans the continuous-rod and cutting-mechanism fact chain; it must not claim component failure, structural breakup, debris, Pk, or weapon-specific lethality.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- A2 pointer: [../README.md](../README.md)
- MLF-2 fuze handoff pointer: [../missile_lethality_geometry_fuze/README.md](../missile_lethality_geometry_fuze/README.md)
- MLF-3 warhead-load pointer: [../missile_lethality_warhead_effects/README.md](../missile_lethality_warhead_effects/README.md)
- MLF-3 accepted evidence package: [../missile_lethality_warhead_effects/archive/mlf_3_warhead_effects_accepted_20260610/README.md](../missile_lethality_warhead_effects/archive/mlf_3_warhead_effects_accepted_20260610/README.md)
- Warhead parameter entry: [weapon_common.h](../../../../../src/components/combat/common/weapon_common.h)
- Event contracts: [engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)
- Current effects model: [default_effects_model.cpp](../../../../../src/models/weapons/default_effects_model.cpp)
- Current rod/cut implementation fragments: [default_effects_warhead_detail.inc](../../../../../src/models/weapons/detail/default_effects_warhead_detail.inc), [default_effects_spatial_projection_detail.inc](../../../../../src/models/weapons/detail/default_effects_spatial_projection_detail.inc)
- Historical rod tests: [warhead_effects.py](../../../../../tests/runtime/air_combat/weapon_guidance_realism/warhead_effects.py)

## Purpose

MLF-4 answers "if the detonated warhead is a continuous-rod or cutting-family mechanism, what cut exposure did it create?" It turns MLF-2 detonation geometry and MLF-3 load facts into explainable cutting facts: rod/cut family, cut margin, orientation weighting, projected cut corridor, component cut exposure, and diagnosable rod fields.

This phase does not decide that a wing, control line, engine, or airframe failed. It only produces upstream cutting facts for later target vulnerability, component failure, structural breakup, debris, and training consumers.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-2 detonation input | accepted / archived | MLF-2 pointer | Only proves nearest approach, fuze evaluation, and detonation handoff |
| MLF-3 load facts | accepted / archived | MLF-3 pointer and accepted package | Provides generic warhead/spatial/component load facts, not failure |
| MLF-4A inventory | accepted slice | [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md) | Accepts read-only inventory only, not runtime behavior |
| Rod fields | reusable scaffold | `WarheadMechanismEvent::rod_cut_margin`, `ComponentLoadEvent::rod_cut_margin`, `EffectsEvent::mechanism_rod_cut_margin`, component primary rod fields | Fields exist, but later work still needs to accept semantics and coverage |
| Continuous-rod runtime branch | candidate scaffold | `continuous_rod` branches in the default effects model and historical Phase 3 tests | Not accepted as current MLF-4 runtime evidence |
| Data authority | held | Public/proxy sources may identify broad mechanism families only | No real AIM-120C or other weapon-specific rod parameters |

## Scope

In scope:

- Inventory and standardize the existing continuous-rod branches and `rod_cut_margin` fields.
- Define whether MLF-4 can reuse `WarheadMechanismEvent` and `ComponentLoadEvent` rod fields, or whether a new standard event is required.
- Model a generic, uncalibrated continuous-rod cut exposure from detonation geometry, orientation axis, range, and spatial coverage.
- Project cut exposure onto hitboxes/components as component-load facts.
- Make diagnostics show rod/cutting rows without converting them into kill or crash claims.
- Preserve no-detonation and non-rod gates: no detonation means no rod cut; non-rod warheads should not emit positive rod-cut facts.

Out of scope:

- No component failure probability. That belongs in MLF-5.
- No structural breakup, airframe slicing conclusion, debris, or wreck objects. Those belong in later structure/debris phases.
- No Pk, training win/loss projection, or direct entity deletion.
- No real weapon/target calibration, including AIM-120C/MQ-9 conclusions.
- No promotion of historical Phase 3 rod tests to accepted evidence without new MLF-4 validation.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `MLF-4A Boundary And Inventory` | Freeze scope and inventory existing rod fields/branches/tests | MLF-3 archived | Current status records reusable fields and gaps | accepted |
| `MLF-4B Standard Rod Event Surface` | Decide and stabilize standard rod/cut fields | 4A accepted | Detonation with `continuous_rod` emits same-chain positive rod facts; non-rod has zero rod facts | planned |
| `MLF-4C Generic Rod Geometry` | Add or verify generic cut corridor/orientation projection | 4B | Range, side/aspect, and orientation change rod cut margin predictably | planned |
| `MLF-4D Component Cut Projection` | Project rod cut exposure onto components | 4C | Component load rows identify affected components and rod cut margin without failure | planned |
| `MLF-4E Diagnostics And Gates` | Make diagnostics prefer standard rod facts and guard no-detonation/non-rod paths | 4D | Probe rows explain rod/cut facts and no false rod rows appear | planned |
| `MLF-4F Acceptance And Archive Prep` | Summarize accepted/held state and sync indexes | 4B-E pass | README/status/task cluster/dispatch/archive agree | planned |

## Task Clusters

- Task cluster plan: [missile_lethality_continuous_rod_task_clusters_20260610.md](missile_lethality_continuous_rod_task_clusters_20260610.md)
- Current status: [missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)
- Dispatch queue: [missile_lethality_continuous_rod_dispatch_queue_20260610.md](missile_lethality_continuous_rod_dispatch_queue_20260610.md)
- MLF-4A inventory packet: [missile_lethality_continuous_rod_inventory_20260610.md](missile_lethality_continuous_rod_inventory_20260610.md)

## Outputs And Evidence

Expected outputs:

- A read-only inventory of existing rod fields, branch behavior, and historical tests.
- Standard rod/cutting facts for `continuous_rod` detonations.
- Focused tests showing range, side/aspect, orientation, and family change rod/cut facts.
- Component-load rows that expose rod cut margin per affected component.
- Diagnostics rows that explain rod/cut facts without declaring failure.

## Acceptance Gate

This subproject can be marked accepted only when:

- `continuous_rod` detonations produce same-chain, diagnosable rod/cut facts.
- Non-rod warheads and no-detonation paths do not produce positive rod/cut facts.
- Rod/cut facts vary with range, side/aspect, orientation, and component projection.
- Component rows expose cut exposure but do not claim failure, breakup, crash, or entity deletion.
- All default rod constants remain generic research assumptions with evidence labels and replacement paths.

## Residuals And Next Steps

- MLF-5 consumes rod/cut facts when modeling component failure probability.
- MLF-6 consumes component failure outputs when modeling structural breakup.
- MLF-8 consumes breakup outputs when modeling wreck/debris lifecycle.
- MLF-9 consumes replayable high-detail chains for Pk/statistical trend work.

## Archive

Archive index: [archive/README.md](archive/README.md)

Superseded or accepted evidence records move to archive only after a replacement current-status or closeout surface exists.
