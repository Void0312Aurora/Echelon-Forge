# A2 MLF-5 Current Status

Status: `2026-06-11` accepted / archived. MLF-5 is closed as a separate target
component vulnerability and failure subproject; `MLF-5A-X1 Boundary And
Inventory`, `MLF-5B-W1 Component Damage Event Surface`, `MLF-5C-W1 Generic
Vulnerability Probability`, `MLF-5D-W1 Component State Handoff`, `MLF-5E-W1
Diagnostics And Gates`, and `MLF-5F-C1 Acceptance And Archive Prep` are
accepted. Helmholtz returned partial, then the main thread repaired the gate so
`ComponentDamageEvent` is exported only when the sample triggers; 5D connects
`integrity_before` / `integrity_after` to the same load row's real before/after
state write; 5E connects component-damage facts to diagnostics; 5F moves this
evidence package into archive and syncs parent indexes.

Chinese main text: [missile_lethality_component_failure_current_status_20260611.zh.md](missile_lethality_component_failure_current_status_20260611.zh.md)

## What Changed

- Created an MLF-5 work surface separate from archived MLF-3 and MLF-4.
- Defined the fifth phase as consuming component-load and cut-exposure facts, then outputting component failure probability, failure mode, and state change.
- Stated that flight-performance, control, propulsion, sensor, and similar consequences must propagate through existing damage/flight systems rather than a separate MLF-5 death rule.
- Kept structural breakup, debris/wreck, Pk, training win/loss, and real weapon calibration outside this phase.
- Accepted the 5A read-only inventory: [missile_lethality_component_failure_inventory_20260611.md](missile_lethality_component_failure_inventory_20260611.md). It confirms a rich candidate implementation surface, but the standard `ComponentDamageEvent` writer / probe / focused tests are not closed yet.
- Dispatched 5B to close the same-chain standard component-damage event surface without entering probability-model, diagnostics, flight-dynamics, or higher-level lethality claims.
- Accepted the 5B standard event surface: added `EngagementComponentDamageEventRecord` / `record_component_damage_event`; the event store exports same-chain `ComponentDamageEvent`; focused tests cover sampled trigger, no-detonation, no component load, and Python bindings.
- Main-thread gate repair: positive probability alone no longer exports a component damage event; only `failure_sample <= failure_probability` does. This avoids recording "risk exists" as "failure occurred."
- Accepted 5C locally on the main thread: added `test_component_failure_probability_surface.py` to prove the generic failure probability varies with load, continuous-rod cut margin, redundancy/criticality, prior damage, and authorized evidence rows; unauthorized or unmatched evidence rows fail closed to the generic uncalibrated estimate.
- Added a 5C proximity-miss magnitude repair: the generic fragment/blast near-miss channel lifts the primary exposed component to an about one-third probability scale for ideal near-miss exposure; continuous-rod grazing exposure also remains observable, while farther/weaker loads remain much lower and the result stays explicitly uncalibrated.
- Repaired debug-hit sampling seeds: `debug_apply_*proximity_hit*` no longer uses constant `123456789` for the synthetic missile RNG seed, so multi-seed scenario statistics now reflect actual sampling changes.
- Accepted 5D locally on the main thread: `ComponentMechanismLoadRow` records before/after component integrity and redundancy-group availability, and `ComponentDamageEvent` copies `integrity_before` / `integrity_after` from the same row; tests prove the event no longer exports empty default `1.0 -> 1.0` values.
- Accepted 5E locally on the main thread: diagnostics-chain schema is now v2, with a `component_damage` stage and summary fields for failure probability, sample, mode, and before/after integrity; tests prove standard `ComponentDamageEvent` is preferred, old `EffectsEvent` rows project only when the sample triggers, and untriggered samples create no false component-damage row.
- Accepted 5F locally on the main thread: added the acceptance closeout, moved the detailed evidence package into archive, and synced the MLF-5 top README, archive index, A2 pointer, and MLF-4 follow-on pointer.

## Maturity Matrix

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Subproject docs | accepted / archived | README, task clusters, current status, dispatch queue, archive index, acceptance closeout | Accepts only the MLF-5 component-failure fact chain |
| MLF-3 component load | accepted / archived | [../../../missile_lethality_warhead_effects/README.md](../../../missile_lethality_warhead_effects/README.md) | Does not decide component failure |
| MLF-4 cut exposure | accepted / archived | [../../../missile_lethality_continuous_rod/README.md](../../../missile_lethality_continuous_rod/README.md) | Does not decide whether a component failed |
| MLF-5A inventory | accepted | [missile_lethality_component_failure_inventory_20260611.md](missile_lethality_component_failure_inventory_20260611.md) | Accepts fields, candidate implementation, historical tests, and gaps only |
| MLF-5B event surface | accepted | `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `tests/runtime/air_combat/test_component_damage_event_surface.py` | Does not modify probability model, diagnostics, flight dynamics, structural breakup, debris/wreck, Pk, or training outcome |
| MLF-5C probability surface | accepted | `tests/runtime/air_combat/test_component_failure_probability_surface.py`, [default_effects_system_effect_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc) | Generic, uncalibrated, and replaceable; not real weapon Pk |
| MLF-5D state before/after | accepted | [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h), `src/models/weapons/detail/default_effects_component_damage_detail.inc`, `tests/runtime/air_combat/test_component_damage_event_surface.py` | Exposes existing state changes only; does not independently claim crash or breakup |
| MLF-5E diagnostics and forbidden-claim gates | accepted | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`, `tests/runtime/air_combat/test_diagnostics_probe_contracts.py` | Explains component damage without claiming crash, breakup, debris/wreck, Pk, or training win/loss |
| MLF-5F archive closeout | accepted | [missile_lethality_component_failure_acceptance_20260611.md](missile_lethality_component_failure_acceptance_20260611.md), archive index, A2/MLF-4 pointers | Syncs acceptance/archive boundaries only; adds no runtime lethality rule |
| `ComponentDamageEvent` | accepted writer/diagnostics surface | [engagement_contracts.h](../../../../../../../src/runtime/contracts/engagement_contracts.h) and 5B/5D writer/export/focused tests; 5E diagnostics tests | Not a crash or breakup conclusion |
| Candidate failure probability fields | accepted generic surface | [effects_model.h](../../../../../../../src/core/interfaces/effects_model.h), [default_effects_system_effect_detail.inc](../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc) | Cannot be treated as real AIM-120C/MQ-9 calibration |
| Damage propagation system | active maintained runtime | [damage_system_air.h](../../../../../../../src/systems/combat/damage_system_air.h) | MLF-5 only hands over component state; it does not rewrite flight dynamics |

## Residual Register

- 5B closed live writer / export / binding / focused tests so sampled component damage facts move from candidate effects rows into the standard event surface.
- 5C accepted the generic probability surface and now includes the proximity-miss magnitude repair; the distance/aspect probe with a 35 m setting shows blast/fragmentation leaving projection after about 15.75 m and continuous rod after about 11 m, with good beam-side exposure clearly above edge/outside cases. Multi-seed sweeps now show ideal near-miss any-component trigger rates from `0.527344` to `0.644531`, while edge/outside cases stay low or zero. The expanded matrix shows non-direct continuous-rod axial grazing is much weaker than beam/top/bottom exposure. It remains an engineering estimate plus authorized evidence-row override mechanism, not Pk or weapon-specific calibration.
- 5D reliably captures before/after integrity from the actual component state write, without fabricating before/after values after the fact.
- 5E connects component damage to the diagnostics probe: standard events are preferred, while old effects rows are projected only when the sample triggers.
- Historical `weapon_guidance_realism` component-damage/vulnerability tests have been partially split into focused MLF-5 evidence; tests not split into this phase's focused evidence remain scaffold only.
- The earlier broad selected test shutdown leak warning is closed: nanobind default objects were removed from the binding/helper defaults, and the collect-only plus runtime reruns no longer print leak warnings.

## Recommended Action Order

1. MLF-5 is closed and has no further dispatch.
2. Structural breakup, wreck/debris, and Pk remain later phases.
3. Open a later subproject for real weapon/target calibration if needed.

## Overclaim Refusals

- Do not claim a component failed merely because failure probability is positive unless a sample/state-change fact exists.
- Do not claim target crash merely because a component failed.
- Do not claim flight loss merely because integrity decreased.
- Do not claim structural breakup or airframe rupture before MLF-6.
- Do not claim debris/wreck before MLF-8.
- Do not claim Pk or real AIM-120C/MQ-9 lethality before a later calibration gate.
