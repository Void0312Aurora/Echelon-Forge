# A2 MLF-3 Dispatch Queue

Status: `2026-06-09` MLF-3B/3E focused pass; `MLF-3A-X1` is accepted, and `MLF-3B-W1` writers plus `MLF-3E-W1` diagnostics standard-event priority have focused validation.

Chinese main text: [missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md](missile_lethality_warhead_effects_dispatch_queue_20260609.zh.md)

Parent task clusters: [missile_lethality_warhead_effects_task_clusters_20260609.md](missile_lethality_warhead_effects_task_clusters_20260609.md)

## Boundary

This queue is only for MLF-3 warhead effects and generic fragment/blast loads. Dispatches must not create a new conversation thread and must not enter continuous rod, structural breakup, debris/wreck, Pk, AIM-120C/MQ-9 case calibration, or direct-kill rules.

Data boundary: this phase uses only generic, uncalibrated, replaceable research data and methods. It may reserve future type-specific supplement slots, but CMO-DB, public webpages, historical tests, and engineering assumptions must not be written as true AIM-120C/MQ-9 parameters.

## Pending Packets

| Packet | Cluster | Assignee | Write set | Required output | Status |
| --- | --- | --- | --- | --- | --- |
| `MLF-3A-X1` | `MLF-3A Boundary And Inventory` | Sartre / current session subagent | read-only inspection; optional status note only | Inventory current warhead/spatial/component fields, writer gaps, diagnostics projection, and reusable test entries; do not edit runtime. | accepted |
| `MLF-3B-X1` | `MLF-3B Standard Event Writers` | Sartre / current session subagent | read-only writer-path audit | Find the minimum producer/recorder path for `WarheadMechanismEvent`, `SpatialCoverageEvent`, and `ComponentLoadEvent`. | accepted via 3A |
| `MLF-3B-W1` | `MLF-3B Standard Event Writers` | main thread | recorder/event-store/bindings/tests after X1 | Write standard warhead, spatial coverage, and component-load events. | focused pass / wider live gate pending |
| `MLF-3C-W1` | `MLF-3C Generic Blast-Fragmentation Loads` | future worker | effects warhead detail + focused tests | Build generic uncalibrated fragment/blast loads with evidence levels. | planned |
| `MLF-3D-W1` | `MLF-3D Spatial Coverage And Component Load` | future worker | spatial projection/component load tests | Project loads onto target components and write standard load facts. | planned |
| `MLF-3E-W1` | `MLF-3E Diagnostics Projection` | main thread | process probe + diagnostics tests | Make diagnostics prefer standard events, with old `EffectsEvent` as fallback only. | focused pass |
| `MLF-3F-W1` | `MLF-3F Runtime Handoff Gate` | main thread / future worker | focused gate tests | Pin no-detonation/no-load and detonation/one-load-chain behavior. | planned |
| `MLF-3G-C1` | `MLF-3G Acceptance And Archive Prep` | main thread | docs/archive/index | Summarize acceptance evidence and follow-on residuals. | planned |

## Current Dispatch Recommendation

Next, add broader live geometry/fuze gates: prove real launch detonation paths export standard events and no-detonation paths do not emit warhead / spatial / component-load standard events. Then continue into `MLF-3C/3D` generic blast/fragment loads and spatial/component projection parameter surfaces.

## Worker Packet Contract

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Returned packets must state:

- Whether a standard-event live writer exists.
- Which fields still exist only in `EffectsEvent` or debug/projection paths.
- Which tests can be reused and which are only historical scaffolding.
- Whether any path risks creating load for no-detonation cases.

## Integration Notes

- Main thread owns returned-packet acceptance and status updates.
- Currently running: none.
- `MLF-3B` still needs broader live geometry/fuze gates; current evidence is focused pass only.
