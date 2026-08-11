# A2 MLF-5A-X1 Component Failure Boundary And Inventory

Status: `2026-06-11` pass / inventory packet. Chinese main text: [missile_lethality_component_failure_inventory_20260611.zh.md](missile_lethality_component_failure_inventory_20260611.zh.md).

This pass performed a read-only audit of the requested source, tests, and MLF-3/MLF-4 archived evidence. It produced documentation only and did not modify runtime, tests, README, current status, dispatch queue, or task clusters. The main finding is that MLF-5 already has a strong candidate implementation surface, but it does not yet have an accepted standard fact surface. `ComponentDamageEvent` is a contract scaffold; the richer probability, evidence, failure-mode, integrity, redundancy, and state handoff data currently live mostly in `EffectsResult` / `EffectsEvent` / `ComponentMechanismLoadRow` and `ComponentDamageState`. The diagnostics probe does not yet expose a standard component-failure stage.

## Audit Scope

- `src/runtime/contracts/engagement_contracts.h`
- `src/core/interfaces/effects_model.h`
- `src/models/weapons/detail/default_effects_system_effect_detail.inc`
- `src/models/weapons/detail/default_effects_state_detail.inc`
- `src/models/weapons/detail/default_effects_spatial_projection_detail.inc`
- `src/systems/combat/damage_system_air.h`
- `src/components/domains/air/combat/damage_air.h`
- `tools/diagnostics/air_combat_stage0_process_probe.py`: deleted in the current worktree, so this audit read the HEAD version only and did not restore or edit it.
- `tests/runtime/air_combat/weapon_guidance_realism/component_damage.py`
- `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_authority.py`
- `tests/runtime/air_combat/weapon_guidance_realism/vulnerability_scaffold.py`
- MLF-3/MLF-4 archived README and acceptance files.

Read-only dependency context: this audit also opened `src/components/combat/common/damage_common.h`, `src/models/weapons/detail/default_effects_component_damage_detail.inc`, and `src/models/weapons/detail/default_effects_result_detail.inc` to describe `ComponentDamageState` and the candidate implementation accurately. They are direct dependencies of the requested audit entry points and were not modified.

## Boundary Finding

MLF-5A can be recorded as pass, but the current runtime should not be called MLF-5 accepted.

- MLF-3 accepts post-detonation mechanism load, spatial coverage, and component-load facts. It does not prove component failure.
- MLF-4 accepts continuous-rod cutting exposure facts. It does not prove component failure probability.
- MLF-5 must turn upstream facts into component failure probability, sample, failure mode, integrity before/after, redundancy state, and state handoff facts.
- The candidate implementation already computes many of those fields, but the standard `ComponentDamageEvent` writer, diagnostics rows, and focused acceptance tests are not closed.
- A positive probability is not a realized sampled failure. The candidate path triggers failure-mode/impulse logic only when `failure_sample <= failure_probability`. It also accumulates component integrity loss from probability/load, so future work must keep damage accumulation separate from sampled failure-mode trigger.

## Field Inventory

| Surface | Existing fields | Reuse | MLF-5 gap |
| --- | --- | --- | --- |
| `ComponentDamageEvent` | `component_name`, `component_system`, `component_redundancy_group_id`, `integrity_before`, `integrity_after`, `failure_mode`, `failure_severity`, `failure_probability`, `failure_sample` | Good 5B standard-event skeleton | No probability source/evidence, no mode list, no group availability/count, no mechanism-load context, no accepted live writer/probe |
| `ComponentLoadEvent` | component identity, direct hit, distance, effect scale, fragment/blast/rod/surface incidence, `load_source` | Accepted MLF-3/MLF-4 input fact | No probability, sample, mode, or integrity change |
| `ComponentMechanismLoadRow` | identity, mechanism loads, dependency fields, probability/source/calibrated/evidence/sample/authority, component-specific and bucket fields, mode list, primary mode/severity | Richest current candidate surface for 5B/5C | Not a standard event; mode authority is false; before/after integrity is incomplete; folded through `EffectsEvent` |
| `EffectsResult` / `EffectsEvent` | aggregate probability/source/evidence/sample/count, primary component, primary integrity, primary mechanism load, redundancy availability/member/failed count, vulnerability metadata | Useful writer input and historical-test anchor | Aggregate/primary oriented; cannot replace per-component damage facts |
| `ComponentDamageState` | component integrity, redundancy maps, mode severity, primary mode, group availability/counts, pending dependency effects | Core 5D handoff container | No accepted event captures before/after yet |
| `AircraftDamageState` handoff | flight/control/hydraulic/propulsion/fuel/avionics/crew/fire/smoke/overstress state | Existing consumer of component state | MLF-5 should only record handoff, not make higher-level conclusions |

## Probability, Source, Evidence, Sample

The candidate probability path is reusable but not accepted:

- Default source is `synthetic_sigmoid`, driven by severity, mechanism scale, component scale, direct hit, mechanism load, system fragility, dependency complexity, previous integrity, and redundancy state.
- With a valid `AircraftVulnerabilityProfile` and a row selected under `component_failure_probability_authority`, source can become `vulnerability_evidence_row`.
- Evidence-row selection can use weapon family, aspect, closure, miss-distance, component name/system/redundancy group, and mechanism-load buckets.
- Mechanism-load gates already cover fragment energy, fragment areal density, penetration margin, blast overpressure, blast impulse, blast scaled distance, rod cut margin, and surface incidence.
- `component_failure_sample` comes from component RNG; sampled failure-mode/impulse logic uses `failure_sample <= failure_probability`.
- `component_failure_probability_authority == true` should mean only row-level probability authority, not Pk, type-specific calibration, or any higher-level outcome.

MLF-5C can reuse `synthetic_sigmoid` as a generic, uncalibrated, replaceable baseline only if source category, scope, unit, uncertainty/replacement rule, and evidence limits are documented and surfaced.

## Failure Modes

Existing candidate modes:

- `puncture`
- `cut`
- `blast_deformation`
- `fuel_leak`
- `hydraulic_pressure_loss`
- `electrical_loss`
- `data_loss`
- `fire_source`
- `structural_weakening`

The mode source is either explicit component `failure_mode_weights` or `synthetic_inferred_part_failure_modes`. Current `component_failure_mode_authority` is false, so these modes are suitable as generic engineering candidates and test fixtures, not authoritative MLF-5 acceptance by themselves.

## Integrity And Redundancy

Reusable fields:

- Component identity: `component_name`, `component_system`, `component_redundancy_group_id`.
- Current export: `component_primary_integrity`, `component_redundancy_group_availability`, `component_redundancy_group_member_count`, `component_redundancy_group_failed_count`.
- State container: `ComponentDamageState.component_integrity`, `component_redundancy_group`, `component_redundancy_weight`, and `redundancy_group_availability`.

Gaps:

- `ComponentDamageEvent` has `integrity_before` / `integrity_after`, but no accepted writer captures them around the state update.
- `EffectsEvent` mainly exposes the primary component's after-like integrity and group availability; it cannot represent every loaded component's before/after.
- 5D must decide whether each fact records single-component integrity, group availability, or both.

## State Handoff

The existing handoff path is reusable:

- `apply_component_damage_state` writes component integrity and redundancy group availability into `ComponentDamageState` and syncs `SystemHealth`.
- `apply_part_failure_mode_state` writes mode severity and primary mode after the sampled trigger and can apply candidate aircraft/platform impulses.
- `derive_aircraft_damage_from_component_state` maps component/group availability into aircraft damage state fields.
- `register_aircraft_damage_system` lets existing flight, propulsion, sensor, fuel leak, fire/smoke, and cascade systems consume `AircraftDamageState`.

5D should stop at "component state was handed to maintained damage/flight systems." It should not make a standalone flight-outcome judgment.

## Diagnostics Gap

The HEAD version of `tools/diagnostics/air_combat_stage0_process_probe.py` has stages for `nearest_approach`, `fuze`, `warhead_mechanism`, `spatial_coverage`, `component_load`, `platform_consequence`, and `lifecycle`. It has no `component_damage` / `component_failure` stage. Row fields also lack probability/source/evidence/sample, failure mode, integrity before/after, and redundancy availability.

5E should add an equivalent component damage/failure projection with:

- component identity and load source/event id;
- probability, probability source, calibrated flag, evidence dataset/row/source/provenance;
- failure sample and sampled-failure bool;
- mode list, primary mode, and mode severity;
- integrity before/after;
- redundancy group availability/member/failed count.

No-detonation and no-load paths must not synthesize component-failure rows. No-positive-rod-cut must block continuous-rod cut-sourced failure only; it must not accidentally block valid blast/fragmentation positive-load paths.

## Historical Test Reuse

Reusable:

- `component_damage.py`: primary component identity, component threshold, probability trend, sample range, failure mode list, redundancy availability, and ComponentDamageState -> AircraftDamageState handoff.
- `vulnerability_authority.py`: row authority, provenance metadata, component-specific override, mechanism-load bucket, rod-cut / fragment-density / surface-incidence gates.
- `vulnerability_scaffold.py`: non-authoritative scaffold remains below authority; runtime-aligned descriptor can drive component probability without granting Pk/fuze authority.
- MLF-4 diagnostics tests provide upstream gate semantics for non-rod zero cut and no-detonation no rod rows.

Not directly promotable to MLF-5 accepted:

- Most tests still live in the historical `weapon_guidance_realism` suite and are named Phase 3 / Phase 5 / A8 rather than current MLF-5 focused acceptance.
- Most evidence rows are unit-test or `fixture://` rows. They prove selector mechanics, not project data authority.
- Tests mostly read `EffectsEvent` aggregate or `component_mechanism_load_rows`, not a standard `ComponentDamageEvent` live writer/probe.
- Existing tests do not close the full no-detonation, no-load, no-positive-rod-cut, and component-failure diagnostics gate matrix.

## Follow-On Recommendations

### MLF-5B Component Damage Event Surface

Use `ComponentDamageEvent` as the skeleton, keep same-chain parentage from component-load/effects facts, and prefer a per-component standard event or row rather than only primary-component aggregation. Decide whether to expand the event with probability evidence and redundancy fields or keep a slim event plus diagnostics companion. The risk is contract/binding churn and losing `integrity_before` if the writer runs after state mutation.

### MLF-5C Generic Vulnerability Probability

Reuse `synthetic_sigmoid` only as a generic, uncalibrated baseline with explicit replaceability labels. Preserve the evidence-row authority gate: calibrated descriptor, authoritative source kind, row metadata, and `component_failure_probability_authority` must all be present before using `vulnerability_evidence_row`. Focus tests should cover rod cut margin, fragment density, blast scaled distance, surface incidence, component-specific rows, redundancy, and pre-damage state.

### MLF-5D Component State Handoff

Capture integrity/group availability before and after state updates. Keep damage accumulation separate from sampled failure-mode trigger. Focus tests should validate `ComponentDamageState`, `AircraftDamageState`, and `SystemHealth` handoff while stopping at state changes.

### MLF-5E Diagnostics And Gates

Add component damage/failure diagnostics in the current active diagnostics entry point. If `air_combat_stage0_process_probe.py` has been replaced, implement in the successor probe rather than restoring the deleted file. Add schema fields for probability/evidence/sample/mode/integrity/redundancy and focused tests for no-detonation, no-load, no-positive-rod-cut, non-authoritative scaffold, authorized evidence row, and component-specific row.

## Worker Packet

status: pass

touched files:

- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/missile_lethality_component_failure_inventory_20260611.zh.md`
- `docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure/missile_lethality_component_failure_inventory_20260611.md`

commands/outcomes:

- `git diff --check -- docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure`: passed in the worker return and main-thread acceptance, no output.
- `rg -n "[[:blank:]]$" docs/systems/effects/reviews/a2_high_fidelity_damage_model_20260602/missile_lethality_evidence_20260619/missile_lethality_component_failure`: no matches in main-thread acceptance.

remaining paths:

- 5B: standard `ComponentDamageEvent` writer / bindings / export / focused tests.
- 5C: generic probability baseline and evidence-authority focused tests.
- 5D: before/after integrity, redundancy before/after, and state handoff tests.
- 5E: component damage/failure diagnostics stage and no-detonation/no-load/no-positive-rod-cut gates.

behavior risks:

- The candidate implementation changes component integrity, but accepted event/probe output does not capture before/after yet.
- `EffectsEvent` is aggregate-oriented and cannot replace per-component damage facts.
- Historical tests prove mechanics, not current MLF-5 acceptance.

integration notes:

- Standard event fields were not changed.
- No default constants were added.
- No-detonation and no-load paths should remain free of synthetic component failure. No-positive-rod-cut should block cut-sourced continuous-rod failure only, not other positive-load mechanisms.
- This packet avoids structural breakup, crash, debris/wreck, Pk, training outcome, entity deletion, and real AIM-120C/MQ-9 lethality conclusions.
