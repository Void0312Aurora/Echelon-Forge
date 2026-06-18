# MLF-1A Missile Lethality Field Inventory

Status: `2026-06-09` MLF-1A documentation complete / no runtime logic changes.

Languages:

- Chinese primary: [missile_lethality_field_inventory_20260609.zh.md](missile_lethality_field_inventory_20260609.zh.md)
- English companion: `missile_lethality_field_inventory_20260609.md`

Reviewed local inputs:

- [README.zh.md](README.zh.md)
- [missile_lethality_chain_contract_20260609.zh.md](missile_lethality_chain_contract_20260609.zh.md)
- [missile_lethality_model_foundation_task_clusters_20260609.zh.md](missile_lethality_model_foundation_task_clusters_20260609.zh.md)
- [../../../../../src/runtime/contracts/engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- [../../../../../src/core/engine/engagement_event_types.h](../../../../../../../../src/core/engine/engagement_event_types.h)
- [../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp](../../../../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp)
- [../../../../../src/interfaces/python/bindings_runtime.cpp](../../../../../../../../src/interfaces/python/bindings_runtime.cpp)
- [../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py](../../../../../../../../tools/diagnostics/air_combat_weapon_employment_process_probe.py)
- [../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py](../../../../../../../../gym_envs/scenario_loader/reward_runtime/air_combat.py)

## Summary

The current repository already connects launch, effects, damage reports, diagnostics export, and reward consumption. It does not yet provide the staged MLF-1 lethality-chain contract.

The main boundary issue is that `EffectsEvent` currently mixes nearest approach, detonation geometry, fuze data, warhead mechanism fields, spatial coverage, component loads, vulnerability evidence, and component summaries. `DamageReport` has structured kill/loss flags, but still exposes `hp_delta`, aggregate `system_health_delta`, and string-formatted `platform_damage_state_delta`. Python bindings expose most C++ contract fields; diagnostics mostly flatten the last effect/damage event; rewards consume damage reports plus aircraft/ground debug state.

Legacy fields are not long-term compatibility commitments. Any short transition must be tied to MLF-1C/1D migration and an explicit removal point.

## Stage Inventory

| Stage | Current fields | Source | Structured now | Mixed in `EffectsEvent` | Python binding | Diagnostics | Reward | Migration direction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Launch | `LaunchRequest.*`, `LaunchEvent.*` | `engagement_contracts.h`, event store | Yes | No | Yes | Indirect release counters/action columns | Release shaping via missile count/action state | Keep and add shared chain header |
| Missile state | `MunitionLifecyclePacket.*` including seeker, fuel, burnout, `fuze_state` | `engagement_contracts.h` | Yes, but not in `RecentEngagementEvents` | No | Yes | Not directly consumed | Not directly consumed | Keep as low-frequency state snapshot |
| Nearest approach / hit geometry | `nearest_approach_time_s`, `miss_distance_m`, `detonation_local_*`, attitude, closure, missile axis, quality/confidence | `EffectsEvent` | Fields are structured; stage is not | Yes | Yes | `last_effect_miss_distance_m`, `last_effect_detonation_local_*` | No | Move to `NearestApproachEvent`; report non-detonation misses too |
| Fuze | `trigger_type`, `outcome_state`, `detonation_time_s`, `fuze_*`, contact and direct-hitbox fields | `EffectsEvent` | Partial; lacks explicit armed/triggered/failure reason/sample | Yes | Yes | `last_effect_fuze_type`, `last_effect_direct_hitbox_intersection` | No | Move to `FuzeEvaluationEvent` |
| Warhead mechanism | `effect_family`, warhead mass/radius/synthetic flags, fragment/blast/rod/mechanism scale fields | `EffectsEvent`, plus row-level mechanism fields | Structured but event-level and row-level loads are mixed | Yes | Yes | Not currently flattened | No | Move to `WarheadMechanismEvent`; keep row-level loads in component events |
| Spatial coverage | `projected_hitbox_count`, `spatial_effect_scale`, `warhead_spatial_*`, `warhead_orientation_*` | `EffectsEvent` | Structured, not staged | Yes | Yes | `last_effect_projected_hitbox_count` | No | Move to `SpatialCoverageEvent` |
| Component loads | `component_mechanism_load_rows` with component identity, direct hit, distance, mechanism loads, dependency propagation, probabilities, evidence, failure modes | `ComponentMechanismLoadRow` inside `EffectsEvent` | Row-structured | Embedded in `EffectsEvent` | Yes | Only `last_effect_component_hit_count` | No | Promote to `ComponentLoadEvent` with chain header and parent id |
| Component/platform damage | `component_*`, `component_primary_*`, `vulnerability_*`; `DamageReport.hp_delta`, `system_health_delta`, `platform_damage_state_delta`, kill flags, loss states | `EffectsEvent`, `DamageReport`, event store | Partial | Component/vulnerability fields are in `EffectsEvent`; reports are separate | Yes | `last_damage_*` summaries | Consumes reports and parses string delta | Split component damage, platform consequence, and lifecycle projection |
| Structural failure | No dedicated breakup/detached-part event; aircraft debug state has structural integrity, overstress, flutter exposure | Reward debug state | Partial state only | No | Not engagement-bound | Not currently flattened | Consequence shaping can read debug state deltas | Add `StructuralBreakupEvent` before MLF-6 |
| Lifecycle | `loss_state_from/to`, `destroyed`; ground debug state `lifecycle`, impact, gear fields | `DamageReport`, ground debug API | Partial | No | Damage report yes; ground debug outside engagement binding | `last_damage_loss_state`, `last_damage_destroyed` | Terminal and consequence shaping consume loss/ground state | Add `LifecycleTransitionEvent`; rewards only consume projection |
| Training projection | Reward terms, release/C2 ROE shaping, damage shaping, terminal helper state | `air_combat.py`, diagnostics rows | Consumer-side projection | No | n/a | CSV reward/action/C2/last summaries | Produces reward terms | Standardize as `TrainingProjectionEvent`; never create lethality facts in reward code |

## Legacy Migration Candidates

| Candidate | Current consumer | Risk | Target | Removal point | Owner |
| --- | --- | --- | --- | --- | --- |
| `last_effect_*` diagnostics columns | Stage0 process probe | Last-event summaries cannot reconstruct a missile chain | Per-stage rows keyed by `chain_id + stage` | After MLF-1C staged projection lands | `MLF-1C` |
| `last_damage_*` diagnostics columns | Stage0 process probe | Last damage report hides chain identity and lifecycle cause | Platform/lifecycle stage rows | After MLF-1C/1D projection migration | `MLF-1C`, `MLF-1D` |
| `DamageReport.hp_delta` | Python binding / potential external use | HP delta is not high-fidelity damage evidence | Component/platform before-after state | After reward consumers stop depending on it | `MLF-1D`, `MLF-1E` |
| `DamageReport.system_health_delta` | Probe and reward shaping | Aggregate scalar hides subsystem identity | Structured capability before/after/delta fields | After reward migration | `MLF-1D` |
| String `DamageReport.platform_damage_state_delta` | Reward `_parse_platform_damage_delta()` | String parsing is unstable and ambiguous | Structured mission/mobility/sensor/survivability deltas | After MLF-1D reward migration | `MLF-1D` |
| `DamageReport.destroyed` as the only terminal fact | Probe and terminal helper | Conflates entity removal, lost state, ground wreck, and breakup | `LifecycleTransitionEvent` plus structural breakup fields | Keep only as short projection until lifecycle events exist | `MLF-1D`, `MLF-8` |
| `EffectsEvent.component_primary_*` | Binding / potential diagnostics | Hides multi-component loads and redundancy propagation | Expanded component load/damage rows | After component row projection | `MLF-1C` |
| `EffectsEvent.vulnerability_*` in effects output | Binding / potential diagnostics | Mixes evidence/profile authority with a runtime effect event | Vulnerability profile/evidence object referenced by event ids | After MLF-1B DTO design and MLF-1E review | `MLF-1B`, `MLF-1E` |

## Acceptance Note

This inventory covers launch, missile state, nearest approach/hit geometry, fuze, warhead mechanism, spatial coverage, component loads, component/platform damage, structural failure, lifecycle, and training projection. It identifies source files, structure state, `EffectsEvent` mixing, binding exposure, diagnostics use, and reward use. It does not tune AIM-120C/MQ-9 and does not change runtime behavior.
