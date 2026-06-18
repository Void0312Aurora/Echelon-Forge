# A2 MLF-5 Component Failure Task Clusters

Status: `2026-06-11` accepted / archived finite task-cluster record for
[README.md](README.md). MLF-5A inventory, 5B standard component-damage event
surface, 5C generic failure probability, 5D state handoff, 5E diagnostics/gates,
and 5F closeout/archive prep are accepted.

Chinese main text: [missile_lethality_component_failure_task_clusters_20260611.zh.md](missile_lethality_component_failure_task_clusters_20260611.zh.md)

Parent links:

- A2 pointer: [../../../README.md](../../../README.md)
- MLF-3 pointer: [../../../missile_lethality_warhead_effects/README.md](../../../missile_lethality_warhead_effects/README.md)
- MLF-4 pointer: [../../../missile_lethality_continuous_rod/README.md](../../../missile_lethality_continuous_rod/README.md)
- Current README: [README.md](README.md)
- Current status: [missile_lethality_component_failure_current_status_20260611.md](missile_lethality_component_failure_current_status_20260611.md)
- Dispatch queue: [missile_lethality_component_failure_dispatch_queue_20260611.md](missile_lethality_component_failure_dispatch_queue_20260611.md)
- Acceptance closeout: [missile_lethality_component_failure_acceptance_20260611.md](missile_lethality_component_failure_acceptance_20260611.md)

## Boundary Decision

MLF-5 may standardize and validate component failure facts: component before/after integrity, failure probability, probability sample, failure mode, severity, evidence source, and handoff to existing damage state.

MLF-5 must not output structural breakup, airborne fragmentation, crash, debris/wreck, training win/loss, entity deletion, Pk, or real weapon-specific conclusions. It also must not independently define whether flight can be maintained; flight consequences must propagate through existing damage, dynamics, propulsion, sensor, and ground-contact systems.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-5A-X1 Boundary And Inventory` | read-only worker `019eb545-f28c-7723-8e9a-07c16138ebe0` / Herschel | inherited / inherited | Inventory ComponentDamageEvent, failure probability, failure mode, integrity, redundancy, historical tests, and gaps | this subproject docs; read-only source/test audit packet | runtime edits, parameter tuning, real weapon calibration | docs diff check; cited source/test inventory | current status names reusable fields and gaps | first, serial | 1 | accepted |
| `MLF-5B-W1 Component Damage Event Surface` | current-session worker `019eb555-8c9b-78e3-8d02-4b6b05f56b14` / Helmholtz + main-thread repair | inherited / inherited | Stabilize same-chain standard component damage events and binding/export | `src/runtime/contracts/**`, event-store, bindings, focused tests | probability model rewrite, structural breakup, crash | contract shape tests + focused live event tests | sampled trigger writes component damage rows; no-detonation/no-load/untriggered samples have no false rows | after 5A | 2 | accepted |
| `MLF-5C-W1 Generic Vulnerability Probability` | main thread local continuation | inherited / inherited | Build generic, uncalibrated, replaceable component failure probability model | default effects vulnerability/probability focused tests | specific AIM-120C/MQ-9 calibration, Pk authority | probability trend tests + evidence-label checks | probability varies with load, cut exposure, component vulnerability, redundancy, and aspect | after 5B | 1 | accepted |
| `MLF-5D-W1 Component State Handoff` | main thread local continuation | inherited / inherited | Write component failure samples and integrity changes into existing damage state and export before/after values | contracts, default effects state sample, bindings, focused tests | independent flight-maintainability definition, direct crash/kill | state-before/after tests + maintained-system handoff evidence | standard events copy actual before/after state-write values and existing damage state continues propagation | after 5C | 1 | accepted |
| `MLF-5E-W1 Diagnostics And Gates` | main thread local continuation | inherited / inherited | Make diagnostics explain component damage facts and preserve forbidden-claim gates | `tools/diagnostics/air_combat_weapon_employment_process_probe.py`, diagnostics tests | reward semantics, training win/loss, entity deletion | diagnostics tests + no-load/no-detonation gates | probe rows explain component damage without false failure/crash rows | after 5B-D | 1 | accepted |
| `MLF-5F-C1 Acceptance And Archive Prep` | main thread | n/a | Summarize accepted/held state and sync indexes | this README/status/task cluster/dispatch/archive; A2 README; MLF-4 pointer | overclaiming breakup, crash, debris, Pk, or real weapon conclusions | docs diff check + referenced tests | accepted/held state matches evidence | after 5B-E | 1 | accepted |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit event contracts, event-store writers, default probability model, damage-state handoff, diagnostics projection, or status lines concurrently.
- Do not create a new conversation thread; subagents, if used, must stay inside the current controlled workflow.
- 5F was closed locally on the main thread and is not dispatched; 5C/5D/5E were advanced serially on the main thread and do not count as new worker dispatch.
- Keep acceptance/closure serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a new wave.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Each returned packet must also state:

- Whether standard event fields changed.
- Whether new default constants were added; if yes, source category, scope, unit, uncertainty, and replacement rule.
- Whether no-detonation, no-load, and no-positive-cut paths still have no false component failure.
- Whether structural breakup, crash, debris/wreck, entity deletion, Pk, and training win/loss rules were avoided.
- Whether any historical Phase 5 / `weapon_guidance_realism` test was promoted, rewritten, or retained.

## Validation Plan

Executed 5C/5D/5E runtime validation:

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_component_damage_event_surface.py tests/runtime/air_combat/test_component_failure_probability_surface.py tests/runtime/air_combat/test_warhead_spatial_component_projection.py tests/runtime/air_combat/test_live_detonation_event_surface.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
```

Result after the binding-default cleanup, proximity distance/aspect probe, and
debug sampling seed repair: combined regression `42 passed`; 5E diagnostics
`26 passed`; broad selected run `41 passed, 282 deselected, 7 subtests passed`.
The previous nanobind shutdown leak warning no longer appears in the
collect-only or runtime closeout reruns.

Planning validation:

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_component_failure \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod/README.zh.md
```

Closeout validation by write set:

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "component_damage or vulnerability or component_failure"
```

## Acceptance Criteria

- Post-detonation component load / cut exposure can produce same-chain component damage facts.
- Component damage facts include probability, sample, failure mode, before/after integrity, and evidence labels.
- No-detonation, no-load, or no-positive-cut paths produce no false component failure.
- Component state enters existing damage and flight/system models instead of MLF-5 deciding whether the target crashes.
- Diagnostics explain component damage facts but do not claim structural breakup, debris/wreck, Pk, or weapon-specific lethality.

## Residual Map

Immediate:

- Keep `MLF-5A-F` accepted and do not dispatch further tasks.
- MLF-5 is archived; structural breakup, wreck/debris, Pk, or weapon-specific calibration need follow-on subprojects.

Follow-on:

- MLF-6 consumes component failure for structural breakup.
- MLF-8 consumes structural outcomes for wreck/debris object lifecycle.

Deferred:

- Real weapon/target calibration, Pk, training win/loss, and entity deletion.
