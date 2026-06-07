# A8 Damage Effect Chain Task Clusters

Status: `2026-06-07` finite task-cluster plan for
[README.md](README.md).

## Boundary Decision

A8 may standardize and implement the damage-effect path after detonation:
detonation record, warhead action, affected aircraft part, part damage type,
functional change, and later aircraft response through existing propulsion,
fuel, sensor, fire, and flight consumers. A8 must not add a direct crash rule,
an independent "can fly" verdict, a special MQ-9 kill rule, real-world
probability of kill, deterministic fuze truth, or stock AIM-120C lethality
claims.

The selected path is:

```text
fuze/detonation
-> warhead action
-> affected part
-> concrete part damage
-> function change
-> existing aircraft simulation response
-> observed outcome
```

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `A8-DEC-A Boundary` | main thread | n/a | Create A8 docs, parent links, current status, task clusters, and archive boundary. | `docs/task/air_combat/a8_damage_effect_chain/**`, `docs/task/air_combat/README.md`, `docs/task/air_combat/README.zh.md` | Runtime implementation, new physics claims | `git diff --check -- docs/task/air_combat` | Standard files exist and parent README links A8. | first, serial | 1 | pass |
| `A8-DEC-B Structure Evidence` | current-session explorers, main-thread integration | inherited model / read-only | Confirm the current fuze/effects, component state, flight/propulsion, and MQ-9/AIM-120C test structures. | A8 current-status updates only | Code edits before structure is agreed | Read-only scans plus local link check | Findings name entry points, gaps, and safe implementation write sets. | after A; parallel by code area | 1 + 1 repair | pass |
| `A8-DEC-C Shot Effect Record` | current-session worker | high reasoning | Define a per-shot record that exposes fuze, detonation, warhead action, affected parts, damage types, and later consequences. | `src/core/interfaces/**`, `src/core/engine/*damage*`, `src/models/weapons/detail/default_effects_result_detail.inc`, tests under `tests/runtime/air_combat/weapon_guidance_realism/**` | Changing aircraft physics or claiming real lethality | Contract tests and runtime guidance guards | Tests can explain why a shot damaged, missed, or had no detonation. | after B; serial with D/E public fields | 2 | pass: public mode rows |
| `A8-DEC-D Part Effect Vocabulary` | current-session worker | high reasoning | Add concrete damage modes and map warhead loads to those modes for structured aircraft parts. | `src/components/combat/damage.h`, `src/content/unit_definition_loader.cpp`, `src/models/weapons/detail/default_effects_*`, MQ-9/F-16 damage JSON as needed, focused tests | Calibrated vulnerability, broad data rewrite | Component-damage tests and loader tests | Component damage records name physical or functional damage instead of only an integrity number. | after C record shape; parallel with F only through disjoint tests | 2 | pass: synthetic public rows |
| `A8-DEC-E Consumer Integration` | current-session diagnostics workers | high reasoning | Route concrete damage into propulsion, fuel/mass, sensors, fire, and flight/aerodynamic behavior. | `src/systems/combat/damage_system.h`, `src/systems/physics/aerodynamics_system.h`, `src/systems/physics/propulsion_system.h`, related physics tests | Direct crash rule, independent flight verdict | Focused runtime tests and flight-dynamics guards | Engine, fuel, sensor, wing/control, and structural damage are consumed by maintained systems. | after D; serial with physics write set | 2 | partial: scout evidence only |
| `A8-DEC-F MQ-9 / AIM-120C Validation` | current-session worker | medium/high reasoning | Build fixed cases that prove rear-engine, wing/control, fuel/fire, and sensor/data-link outcomes. | `tests/runtime/air_combat/**`, optional test-only fixtures under examples/scenarios | Treating one smoke run as real-world probability | `python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py` plus new focused tests | Tests check both immediate records and later aircraft response. | after C/D/E; can prepare fixture plan after B | 2 | partial pass: fixtures and guards |
| `A8-DEC-G Acceptance And Index Sync` | main thread | n/a | Decide accepted or held, sync parent README/status, and record residuals. | A8 README/status/acceptance, parent air-combat README, archive index if needed | Marking docs-only work as runtime pass | docs link check plus accepted validation commands | Capability statement is evidence-backed and overclaims remain refused. | last, serial | 1 | partial pass: first wave only |

## Dispatch Rules

- First implementation dispatch queue:
  [a8_damage_effect_chain_dispatch_queue_20260607.md](a8_damage_effect_chain_dispatch_queue_20260607.md)
- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit the same public record fields, component schema,
  aircraft config section, physics consumer, or status line concurrently.
- No new conversation threads may be created. Current-session subagents may be
  used only as bounded workers inside the cluster write sets.
- Keep boundary, acceptance, and parent-index synchronization serial.
- If a cluster exceeds its round cap, stop and re-scope before adding another
  follow-up wave.
- Follow [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Initial docs-only validation:

```bash
git diff --check -- docs/task/air_combat
```

Expected focused implementation validation, refined after `A8-DEC-B/C`:

```bash
cmake --build build-workshop -j 8
python -m pytest -q tests/runtime/air_combat/test_weapon_guidance_realism_guards.py
python -m pytest -q tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
python -m pytest -q tests/runtime/air_combat/test_flight_dynamics_realism_guards.py
```

New tests must inspect the process record and a later aircraft response, not
only the final health or alive/dead state.

## Acceptance Criteria

- Shot records explain fuze result, detonation geometry, warhead action,
  affected parts, concrete damage modes, and downstream aircraft response.
- Structured aircraft keep health as compatibility output, not the main damage
  explanation.
- Engine or propeller damage reaches propulsion thrust.
- Wing/control damage reaches roll, pitch, yaw, asymmetry, or aerodynamic
  behavior through maintained flight systems.
- Fuel damage reaches leak, mass, supply, fire risk, or fire spread behavior.
- Sensor/data-link damage can produce a mission or sensing consequence without
  pretending the aircraft must crash.
- MQ-9 / AIM-120C cases include rear, wing/control, fuel/fire, and sensor/data
  examples with deterministic checks.
- Documentation still refuses real-world probability of kill, deterministic fuze
  truth, and stock AIM-120C/MQ-9 lethality claims.

## Residual Map

Immediate:

- Use the integrated read-only findings to freeze the shot effect record shape
  before changing component or physics consumers.
- Keep the first runtime cut at mechanism-load to concrete part-failure records,
  before widening aerodynamic or control-model changes.

Follow-on:

- Add calibrated vulnerability or warhead evidence only through a separate data
  admission package.
- Add platform-family-specific aircraft consumers after fixed-wing MQ-9/F-16
  cases are coherent.

Deferred:

- Real-world kill probability.
- Deterministic fuze truth.
- Classified or stock weapon data.
- Broad multi-aircraft vulnerability calibration.
