# A2 MLF-5 Target Component Vulnerability And Failure

Status: `2026-06-11` MLF-5 target component vulnerability and failure fact
chain accepted / archived. MLF-5A inventory, MLF-5B standard component damage
event surface, MLF-5C generic component failure probability, MLF-5D component
state handoff, MLF-5E diagnostics/gates, and MLF-5F closeout/archive prep are
accepted. This evidence package does not claim structural breakup, crash,
debris/wreck, Pk, or weapon-specific lethality.

Language:

- Chinese main text: [README.zh.md](README.zh.md)
- English companion: `README.md`

Inputs:

- A2 pointer: [../../../README.md](../../../README.md)
- MLF-1 chain contract archive: [../../../missile_lethality_model_foundation/README.md](../../../missile_lethality_model_foundation/README.md)
- MLF-3 warhead-load archive: [../../../missile_lethality_warhead_effects/README.md](../../../missile_lethality_warhead_effects/README.md)
- MLF-4 continuous-rod/cutting fact archive: [../../../missile_lethality_continuous_rod/README.md](../../../missile_lethality_continuous_rod/README.md)
- Event contract entry: [engagement_contracts.h](../../../../../../../../src/runtime/contracts/engagement_contracts.h)
- Effects result entry: [effects_model.h](../../../../../../../../src/core/interfaces/effects_model.h)
- Default component-failure candidate implementation: [default_effects_system_effect_detail.inc](../../../../../../../../src/models/weapons/detail/default_effects_system_effect_detail.inc)
- Air damage propagation entry: [damage_system_air.h](../../../../../../../../src/systems/combat/damage_system_air.h)

## Purpose

MLF-5 answers "after a component receives load or cut exposure, is that component damaged, how did it fail, and how much did its state change?" It consumes MLF-3 component-load facts and MLF-4 rod/cut facts, then emits component-level failure probability, random sample, failure mode, severity, before/after integrity, and evidence source.

This phase does not independently decide whether an aircraft can keep flying. If engine, hydraulic, control, sensor, fuel, or fire-suppression components are damaged, the effect should propagate through existing `ComponentDamageState`, `AircraftDamageState`, flight dynamics, propulsion, and sensor systems. MLF-5 does not write direct crash rules or turn one component failure into entity deletion.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| MLF-3 component load | accepted / archived | MLF-3 evidence package | Says what load reached components, not whether they failed |
| MLF-4 cut exposure | accepted / archived | MLF-4 evidence package | Says what cut exposure exists, not whether components failed |
| `ComponentDamageEvent` | accepted writer and diagnostics surface | `engagement_contracts.h` defines component before/after, failure mode, probability/sample; 5B closed writer/export/focused tests; 5D connects before/after to the real component-load row; 5E adds diagnostics-chain projection | Does not output crash, breakup, debris/wreck, or Pk |
| Current effects model | accepted MLF-5C/5D surface | `EffectsResult`, `ComponentMechanismLoadRow`, and default-effects details carry failure probability, sample, evidence, primary integrity, redundancy, and before/after fields | Still not a structural-breakup, crash, wreck/debris, or Pk model |
| Damage propagation | active maintained runtime | `damage_system_air.h` propagates component/aircraft damage into control, hydraulics, propulsion, sensors, fuel, and flight performance | MLF-5 hands component failure state over; it does not redefine flight dynamics |
| Historical tests | retained scaffold | `weapon_guidance_realism/component_damage.py`, `vulnerability_authority.py`, `vulnerability_scaffold.py` | Historical tests not split into this phase's focused tests remain scaffold only |
| MLF-5A inventory | accepted | [missile_lethality_component_failure_inventory_20260611.md](missile_lethality_component_failure_inventory_20260611.md) | Accepts field/candidate/gap inventory only, not runtime behavior |
| MLF-5B event surface | accepted | `ComponentDamageEvent` recorder / store / export; `test_component_damage_event_surface.py` | Exports component damage events only when the probability sample triggers; does not change probability model, state handoff, or diagnostics |
| MLF-5C generic failure probability | accepted | `test_component_failure_probability_surface.py`; `default_effects_system_effect_detail.inc` | Generic, uncalibrated, and replaceable; not real weapon Pk |
| MLF-5D state before/after | accepted | `ComponentMechanismLoadRow` before/after fields; `test_component_damage_event_surface.py` | Exposes existing state-write results; does not independently decide whether the aircraft crashes |
| MLF-5E diagnostics and gates | accepted | `air_combat_weapon_employment_process_probe.py`; `test_diagnostics_probe_contracts.py` | Explains component-damage facts; does not promote component damage to crash/breakup/Pk |

## Scope

In scope:

- Inventory existing component failure probability, failure mode, evidence, redundancy, and integrity fields.
- Stabilize `ComponentDamageEvent` or an equivalent standard event surface with per-component before/after state.
- Convert MLF-3/MLF-4 load facts into generic, uncalibrated, replaceable component failure probability.
- Record failure modes such as control, hydraulic, propulsion, sensor, fuel, fire/smoke, and local structural weakening at component level.
- Write component state into the existing damage state so maintained flight and system models propagate consequences.
- Preserve evidence labels for generic engineering assumptions, test-synthetic data, public/proxy data, and uncalibrated data.

Out of scope:

- No structural breakup, airframe rupture, or airborne fragmentation. Those belong in MLF-6.
- No debris/wreck or fragment lifecycle. Those belong in MLF-8.
- No Pk, training win/loss, or entity deletion. Those belong in later statistical/consumer layers.
- No real AIM-120C/MQ-9 or other weapon/target-specific calibration.
- No shortcut rule such as "if this component fails, crash immediately."

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `MLF-5A Boundary And Inventory` | Freeze scope and inventory existing fields, candidate implementation, historical tests, and gaps | MLF-4 archived | Current status records reusable fields and gaps | accepted |
| `MLF-5B Component Damage Event Surface` | Stabilize standard component damage events | 5A accepted | Live path emits same-chain `ComponentDamageEvent` or equivalent standard rows | accepted |
| `MLF-5C Generic Vulnerability Probability` | Build generic component failure probability model and evidence labels | 5B accepted | Probability varies with load, cut exposure, component vulnerability, redundancy, and aspect | accepted |
| `MLF-5D Component State Handoff` | Write component failure into existing damage state | 5C accepted | Standard events export real `integrity_before` / `integrity_after` and preserve existing damage-state propagation | accepted |
| `MLF-5E Diagnostics And Gates` | Explain component failure in diagnostics and preserve forbidden-claim gates | 5B-D pass | Probe emits component damage rows without crash/breakup/Pk claims | accepted |
| `MLF-5F Acceptance And Archive Prep` | Summarize accepted/held state and sync indexes | 5B-E pass | README/status/task cluster/dispatch/archive agree | accepted |

## Task Clusters

- Task cluster plan: [missile_lethality_component_failure_task_clusters_20260611.md](missile_lethality_component_failure_task_clusters_20260611.md)
- Current status: [missile_lethality_component_failure_current_status_20260611.md](missile_lethality_component_failure_current_status_20260611.md)
- Dispatch queue: [missile_lethality_component_failure_dispatch_queue_20260611.md](missile_lethality_component_failure_dispatch_queue_20260611.md)
- Acceptance closeout: [missile_lethality_component_failure_acceptance_20260611.md](missile_lethality_component_failure_acceptance_20260611.md)
- Expanded aspect/distance matrix: [missile_lethality_component_failure_expanded_matrix_20260611.md](missile_lethality_component_failure_expanded_matrix_20260611.md)

## Outputs And Evidence

Expected outputs:

- An accepted read-only inventory of reusable fields, candidate implementation, and historical tests that cannot be promoted directly.
- Standard component damage facts: component name, system, redundancy group, before/after integrity, failure probability, sample, failure mode, severity, and evidence source.
- A generic component failure probability model whose inputs come from MLF-3/MLF-4 load and cut facts rather than one health subtraction.
- Integration evidence showing component state changes propagate through maintained damage and flight/system models.
- Diagnostic rows that explain which component failed and why, without directly claiming crash or breakup.

## Acceptance Gate

This subproject can be marked accepted only when:

- post-detonation component-load / rod-cut facts can produce same-chain component damage facts;
- component damage facts include probability, sample, failure mode, before/after integrity, and evidence labels;
- no-load, no-detonation, or no-positive-load paths do not synthesize false component failures;
- component state is handed to existing damage/flight systems instead of MLF-5 deciding whether flight can be maintained;
- structural breakup, debris/wreck, Pk, training win/loss, and real weapon-specific lethality remain held.

## Residuals And Next Steps

- MLF-5B has closed the standard component-damage event surface; 5C/5D/5E were advanced and accepted locally on the main thread.
- 5C now includes a generic proximity-miss probability retune: the primary component in an ideal near-miss enters an about one-third probability scale, while farther/weaker loads remain much lower; continuous-rod grazing exposure also stays observable instead of collapsing to near zero. This remains uncalibrated scaffold evidence, not Pk or real weapon data.
- Boundary observation with a 35 m radius setting: blast/fragmentation projects to about 15.75 m, while continuous rod projects to about 11 m. With good beam-side exposure, blast/fragmentation y=6 m is `0.351680`, y=10 m is `0.006144`, and y=22 m has no projection; continuous rod y=6 m is `0.347818`, y=12 m is `0.015949`, and y=16 m has no projection. Direct hits remain much stronger, for example continuous rod y=4.1 m is `0.555924`.
- Multi-seed scenario statistics are now covered: before the repair, the debug hit API used a constant synthetic missile RNG seed, creating the false pattern "theoretical probability changes, actual sampling does not." After the repair, a 256-seed sweep gives continuous-rod direct right-wing trigger rate `0.546875`, good beam-side near-miss any-component trigger rate `0.527344`, mid beam-side `0.359375`, edge `0.015625`, and outside `0.000000`. Blast/fragmentation good beam-side near-miss any-component trigger rate is `0.644531`, mid beam-side `0.128906`, edge `0.015625`, and outside `0.000000`.
- The expanded aspect/distance matrix is now probed: blast/fragmentation responds on nose, tail, top, and bottom aspects and falls with distance; continuous rod is more sensitive to beam, vertical, and diagonal exposure, while non-direct axial grazing is near ineffective. For example, continuous rod nose 8 m is `0.000003`, tail 8 m is `0.037570`, top 6 m is `0.351680`, and right-high 8 m is `0.262566`. This confirms the surface varies with aspect and distance instead of applying one distance-only probability. Gray heatmap cells mean not configured/not applicable, not zero; `D` marks direct hits that should not be read as the same curve as ordinary proximity points.
- The heatmap anomalies have focused coverage: continuous-rod nose 4 m is non-direct grazing with `0.000000` trigger rate, while nose 6 m is direct hit with `1.000000` trigger rate, so the jump is not a geometry penetration bug. Blast/fragmentation tail 6 m direct hit previously looked weaker than tail 8 m proximity; the direct-hit load floor now gives tail 6 m primary probability `0.686314` and any-component trigger rate `0.703125`, no longer below tail 8 m proximity.
- 5D now captures exact `integrity_before` / `integrity_after` from the same component-load row's actual state write, without fabricating before/after values.
- 5E adds `component_damage` to diagnostics-chain schema v2 and verifies that untriggered samples do not create false component-damage stages.
- 5F completed closeout/archive prep; the current [../../README.md](../../README.md) is only a lightweight archive pointer.
- MLF-6 consumes MLF-5 component failure output for structural breakup / airframe rupture.
- MLF-8 consumes MLF-6 structural outcomes for wreck/debris lifecycle.
- MLF-9 consumes replayable high-detail chains for Pk/statistical trends.

## Archive

Archive index: [../README.md](../README.md)

This evidence package proves only the target component vulnerability and failure
fact chain; it does not prove structural breakup, wreck/debris, Pk, crash, or
weapon-specific lethality.
