# Missile Lethality Chain Event And Diagnostic Contract

Status: `2026-06-09` MLF-1 design record / runtime unchanged.

Language:

- Chinese main text: [missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- English companion: `missile_lethality_chain_contract_20260609.md`

Inputs:

- Subproject README: [README.md](README.md)
- Field inventory: [missile_lethality_field_inventory_20260609.md](missile_lethality_field_inventory_20260609.md)
- Contract structs: [../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../src/runtime/contracts/engagement_contracts.h)
- Recent event packet: [../../../../../src/core/engine/engagement_event_types.h](../../../../../src/core/engine/engagement_event_types.h)
- Event store: [../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- Debug entry: [../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp)
- Diagnostics export: [../../../../../tools/diagnostics/air_combat_stage0_process_probe.py](../../../../../tools/diagnostics/air_combat_stage0_process_probe.py)
- Training consumer: [../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)

## Decision

The chain should be standardized before adding higher-fidelity missile effects.
The current runtime can connect launch, effect, damage report, and training
consumption, but several physical stages are packed into a small number of large
records. That makes diagnosis depend on "last effect" and "last damage" rather
than a replayable shot history.

A small lethality-chain contract subdomain is useful, but the first extraction
should be contracts and diagnostic projection only. The event store should keep
recording and ordering events, weapon models should keep computing geometry,
fuze, warhead, and spatial coverage, damage systems should keep changing target
state, and flight dynamics should keep turning damage into flight consequences.

## Existing Surface

| Existing record | What it explains | Main gap |
| --- | --- | --- |
| `LaunchRequest` / `LaunchEvent` | request, acceptance, launcher, spawned munition | weak explicit link to later effects |
| `MunitionLifecyclePacket` | active state, guidance state, fuel, coarse fuze state | not enough to explain trigger/failure decisions |
| `EffectsEvent` | geometry, fuze, warhead, mechanism, component, evidence fields | too many physical stages in one record |
| `ComponentMechanismLoadRow` | per-component mechanism loads | no independent event identity |
| `DamageReport` | aggregate damage deltas, kill flags, loss state | not enough structured component before/after state |
| `DiagnosticsTrace` | chain/event references | references only, not stage reasons |
| Diagnostics probe | recent effect and damage fields | last-event oriented |
| Reward runtime | damage reports and ground-contact state | consumer only, not source of truth |

## Standard Event Sequence

Each munition should be replayable through this sequence. When a stage does not
occur, the chain should still record why it did not occur.

| Order | Event | Question answered | MLF-1 action |
| --- | --- | --- | --- |
| 1 | Launch event | Was the shot created, by whom, against what? | keep and require common header |
| 2 | Munition state | Is the munition still flying and guided? | keep as state, not as effect truth |
| 3 | Nearest approach event | Where did it pass and how close? | split from effect diagnostics |
| 4 | Fuze evaluation event | Did it arm, trigger, delay, or fail? | add explicit status and reason fields |
| 5 | Warhead mechanism event | What blast/fragment/cutting mechanisms exist? | add mechanism list and authority labels |
| 6 | Spatial coverage event | What space did the mechanisms cover? | separate from component damage |
| 7 | Component load event | Which components received what load? | stabilize current load rows |
| 8 | Component damage event | What changed on each component? | add before/after state and failure modes |
| 9 | Platform consequence event | What changed in control, engine, sensor, fuel, fire, or crew state? | make damage-system output visible |
| 10 | Structural breakup event | Did major parts detach or did the target break up? | reserve contract fields before MLF-6 |
| 11 | Lifecycle transition event | Is the target an aircraft, forced-landing body, wreck, or debris? | unify crash/wreck/debris semantics |
| 12 | Training projection event | How did training consume the facts? | projection only, not source of truth |

## Common Header

All lethality-chain events should share a common header:

| Field | Meaning |
| --- | --- |
| `schema_version` | event and export schema version |
| `chain_id` | one munition's chain |
| `event_id` | current event id |
| `parent_event_id` | upstream event reference |
| `stage` | `launch`, `nearest_approach`, `fuze`, `warhead`, `component_load`, and so on |
| `status` | `pass`, `miss`, `no_trigger`, `failed`, `not_evaluated`, and so on |
| `reason` | human-readable stage reason |
| `source_time_s` | simulation time |
| `source_frame` | source frame for same-time ordering |
| `munition` | munition entity reference |
| `shooter` | shooter entity reference |
| `target` | target entity reference |
| `producer_node_id` | producer system/node |
| `fidelity_mode` | low, medium, or high detail |
| `evidence_level` | official public, public, CMO-DB proxy, engineering assumption, training synthetic, or uncalibrated |
| `confidence` | diagnostic completeness confidence, not real-world kill probability |

## Source Annotation

The chain may use CMO-DB as a proxy data source. The CMO-DB page describes
itself as an unofficial viewer for Command: Modern Operations DB3000 data, so it
can provide engineering proxy parameters but should not be represented as
official test authority.

Fields sourced from CMO-DB should remain traceable:

| Annotation | Meaning |
| --- | --- |
| `evidence_level=cmo_db_proxy` | value comes from CMO-DB proxy data |
| `source_kind` | `cmo_db` |
| `source_version` | for example CMO Database v517 |
| `source_url` | CMO-DB entry or search-result URL |
| `source_entry_name` | CMO-DB entry name |
| `source_field_name` | original field name |
| `source_unit` | original unit |
| `accessed_on` | access date |
| `mapping_rule` | conversion from CMO-DB field to project field |
| `manual_adjustment_note` | reason for manual adjustment, if any |

These fields may directly seed defaults and proxy calibration. What is forbidden
is unmarked use, or describing them as true Pk, real fuze thresholds, classified
warhead fragmentation distributions, or other uncalibrated truths.

## Missing Contract Objects

| Object | Purpose |
| --- | --- |
| `LethalityChainHeader` | shared identity, status, reason, authority, and timing |
| `NearestApproachEvent` | closest point and aspect, even with no detonation |
| `FuzeEvaluationEvent` | arming, trigger, failure, delay, reliability, and sample |
| `WarheadMechanismEvent` | blast, fragment, rod/cutting, or mixed mechanism loads |
| `SpatialCoverageEvent` | orientation, sample count, pattern, and coverage strength |
| `ComponentLoadEvent` | stabilized per-component mechanism rows |
| `ComponentDamageEvent` | component before/after state and failure modes |
| `PlatformConsequenceEvent` | damage-system output to aircraft systems |
| `StructuralBreakupEvent` | severed parts, detachment, and breakup state |
| `LifecycleTransitionEvent` | aircraft, forced landing, crash, wreck, and debris transitions |
| `TrainingProjectionEvent` | reward/terminal consumption of existing facts |

## Module Boundary

| Layer | Recommendation | Avoid |
| --- | --- | --- |
| Contracts | Add `src/runtime/contracts/lethality_chain_contracts.h`, or first split sections inside `engagement_contracts.h` | physical calculations inside DTOs |
| Event store | Keep in `src/core/engine/*event_store*`; record, order, link, export | deciding whether an aircraft can still fly |
| Weapon model | Later use a `src/models/weapons/lethality/` style area for geometry, fuze, warhead, and spatial coverage | reward code back-filling hit effects |
| Damage system | Keep component/platform state changes in combat damage systems | HP-only or kill-flag-only outcomes |
| Flight/physics | Existing aero, propulsion, control, and ground-contact systems consume damage | a separate "can maintain flight" kill rule |
| Diagnostic projection | Add one shared flattening helper for probes, reward, and tests | each Python script inventing field meanings |

Short path:

1. Define event names and fields without changing behavior.
2. Migrate mixed `EffectsEvent` fields into staged diagnostics. Old fields are source inventory, not long-term exported aliases.
3. Split C++ DTOs or move files only after controlled probes can replay a shot.

## Acceptance Gate

MLF-1 can be accepted only when:

- A single munition can be traced from launch to nearest approach, fuze,
  mechanism, component load, damage report, and later state.
- Miss, no detonation, detonation with no damage, non-terminal damage, delayed
  crash, and breakup all have explicit recording positions.
- Diagnostics no longer depend only on `last_effect_*` and `last_damage_*`.
- Added values have authority labels and do not claim AIM-120C/MQ-9-specific
  official/test truth. CMO-DB values must use a `cmo_db_proxy`-style label.
- Legacy fields are listed for deletion or migration. Diagnostics and training
  consumers move to the standard fields; no long-term dual compatibility surface
  is maintained.

## Current Judgment

Create a small lethality-chain contract subdomain first. It is a stable ledger,
not a new simulator and not a new direct-kill rule. Without it, later
fragmentation or rod/cutting models would still be hard to diagnose because the
runtime could not clearly say where the missile passed, why the fuze fired, what
mechanism hit which component, and how the later flight or wreck outcome arose.
