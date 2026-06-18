# A2 MLF-3 Dispatch Queue

Status: `2026-06-10` MLF-3 standard load-chain focused accepted. `MLF-3A-X1` is accepted, and `MLF-3B-W1/W2` writers/live gate, `MLF-3C-W1/X2` generic load variation gate and read-only audit, `MLF-3D-W1` spatial/component projection gate, `MLF-3E-W1/W2` diagnostics standard-event priority, `MLF-3F-W1` no-detonation no-load gate, and `MLF-3G-C1` closeout record have focused validation.

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
| `MLF-3B-W1` | `MLF-3B Standard Event Writers` | main thread | recorder/event-store/bindings/tests after X1 | Write standard warhead, spatial coverage, and component-load events. | focused pass |
| `MLF-3B-W2` | `MLF-3B Standard Event Writers` | Pauli / accepted by main thread | live detonation path test | Prove real launch detonation paths export same-chain warhead / spatial / component-load standard events. | accepted |
| `MLF-3C-W1` | `MLF-3C Generic Blast-Fragmentation Loads` | Planck / accepted by main thread | focused standard-event tests | Pin generic uncalibrated fragment/blast loads changing with range / direction / family. | accepted |
| `MLF-3C-X2` | `MLF-3C Generic Blast-Fragmentation Loads` | Heisenberg / accepted by main thread | read-only audit | Audit 3C inputs/test entrypoints and metadata boundaries; confirm DTOs lack full per-default metadata. | accepted |
| `MLF-3D-W1` | `MLF-3D Spatial Coverage And Component Load` | Euclid read-only audit + Fermat worker / accepted by main thread | spatial projection/component load tests | Project loads onto target components and write standard load facts. | focused pass |
| `MLF-3E-W1` | `MLF-3E Diagnostics Projection` | main thread | process probe + diagnostics tests | Make diagnostics prefer standard events, with old `EffectsEvent` as fallback only. | focused pass |
| `MLF-3E-W2` | `MLF-3E Diagnostics Projection` | Raman / accepted by main thread | diagnostics guard test | Prove standard events suppress only same-chain `EffectsEvent` fallback, while other chains can still fall back. | accepted |
| `MLF-3F-W1` | `MLF-3F Runtime Handoff Gate` | Pasteur + main thread integration | event-store gate + focused gate test | Pin no-detonation/no-load and detonation/one-load-chain behavior. | accepted after integration fix |
| `MLF-3G-C1` | `MLF-3G Acceptance And Archive Prep` | main thread | docs/archive/index | Summarize acceptance evidence and follow-on residuals. | focused pass |

## Current Dispatch Recommendation

No MLF-3 worker is currently running. Future work should create MLF-4/5/6/8/9 phases for continuous rod, component failure probability, structural breakup, debris/wreck, and Pk; still do not treat MLF-3 standard load facts as type-specific kill conclusions.

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
- 3D acceptance: Euclid `MLF-3D-W1` read-only audit passed; Fermat `MLF-3D-W1` focused test passed. Main-thread revalidation passed, with a retained boundary: standard `ComponentLoadEvent` does not yet expose per-component spatial weight explicitly; spatial influence is read through `effect_scale` and mechanism loads.
- 3G acceptance: main-thread closeout record synced README, current status, task clusters, dispatch queue, and archive index; high-fidelity lethality residuals remain held.
- 3C acceptance: Planck `MLF-3C-W1` passed; Heisenberg `MLF-3C-X2` passed. Main-thread revalidation passed, with a retained metadata gap: current DTOs/headers do not carry per-default source category / scope / unit / uncertainty / replacement-rule metadata.
- This acceptance round: Pauli `MLF-3B-W2` passed, Raman `MLF-3E-W2` passed, and Pasteur `MLF-3F-W1` first exposed the runtime gap where no-detonation still projected warhead/spatial standard events; the main thread added the event-store gate and revalidated it.
