# A2 MLF-4 Continuous-Rod Task Clusters

Status: `2026-06-11` finite task-cluster plan for [README.md](README.md). MLF-4 has accepted 4A inventory, 4B standard event-surface, 4C generic-geometry, and 4D component-projection slices; full MLF-4 acceptance is not claimed.

Chinese main text: [missile_lethality_continuous_rod_task_clusters_20260610.zh.md](missile_lethality_continuous_rod_task_clusters_20260610.zh.md)

Parent links:

- A2 pointer: [../README.md](../README.md)
- MLF-3 pointer: [../missile_lethality_warhead_effects/README.md](../missile_lethality_warhead_effects/README.md)
- Current README: [README.md](README.md)
- Current status: [missile_lethality_continuous_rod_current_status_20260610.md](missile_lethality_continuous_rod_current_status_20260610.md)
- Dispatch queue: [missile_lethality_continuous_rod_dispatch_queue_20260610.md](missile_lethality_continuous_rod_dispatch_queue_20260610.md)

## Boundary Decision

MLF-4 may standardize and validate continuous-rod/cutting facts after detonation. It may modify rod-related event fields, default effects rod geometry, component cut-load projection, diagnostics rows, and focused tests.

MLF-4 must not output component failure, structural breakup, debris/wreck, crash, training win/loss, entity deletion, Pk, or real weapon-specific conclusions.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-4A-X1 Boundary And Inventory` | read-only worker | `gpt-5.4-mini` / `xhigh` | Inventory existing rod fields, continuous_rod branches, historical tests, and event gaps | this subproject docs; read-only source/test audit packet | runtime edits, parameter tuning, real weapon calibration | docs diff check; cited source/test inventory | current status names reusable fields and gaps | first, serial | 1 | accepted |
| `MLF-4B-W1 Standard Rod Event Surface` | current-session worker | inherited / `high` | Stabilize standard rod/cut fields in warhead and component-load events | focused test only after failed broad worker attempt | new failure states, structural breakup, kill | `ef_py` focused test; engagement contract shape tests | continuous_rod detonation emits same-chain positive rod facts; non-rod and no-detonation emit no positive rod facts | after 4A | 2 | accepted |
| `MLF-4C-W1 Generic Rod Geometry` | current-session worker | inherited / `high` | Build or verify generic cut corridor/orientation projection | focused tests only; no source changes | true rod count/velocity for a real missile; Pk | focused range/aspect/orientation tests | rod cut margin changes with range, side/aspect, and orientation | after 4B | 2 | accepted |
| `MLF-4D-W1 Component Cut Projection` | current-session worker | inherited / `high` | Project rod cut exposure onto hitboxes/components | focused component projection test only; no source changes | component failure probability or integrity changes | focused left/right/component projection tests | component rows expose rod cut margin and cut source without failure | after 4C | 2 | accepted |
| `MLF-4E-W1 Diagnostics And Gates` | future worker | n/a | Make diagnostics prefer standard rod facts and guard no-detonation/non-rod paths | `tools/diagnostics/air_combat_stage0_process_probe.py`; diagnostics tests; no-detonation tests | reward semantics, training win/loss, entity deletion | diagnostics tests plus no-detonation/non-rod gates | probe rows explain rod/cut facts without false rod rows | after 4D | 2 | ready |
| `MLF-4F-C1 Acceptance And Archive Prep` | main thread | n/a | Summarize accepted/held state and sync indexes | this README/status/task cluster/dispatch/archive; A2 README; MLF-3 pointer if needed | overclaiming failure, breakup, Pk, or real weapon conclusions | docs diff check + referenced tests | accepted/held state matches evidence | after 4B-E | 1 | planned |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not allow two workers to edit event contracts, event-store writers, default effects rod fragments, diagnostics projection, or status lines concurrently.
- Do not create a new conversation thread; subagents, if used, must stay inside the current controlled workflow.
- Keep acceptance/closure serial.
- If a cluster exceeds its round cap, stop and re-scope before adding a new wave.
- Preserve the gates: no detonation means no rod/cut fact; non-rod families must not emit positive rod/cut facts.

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
- Whether no-detonation and non-rod paths still have no positive rod/cut facts.
- Whether component failure, structural breakup, crash, entity deletion, Pk, and training win/loss rules were avoided.
- Whether any existing historical Phase 3 test was promoted, rewritten, or left as retained scaffold only.

## Validation Plan

Planning validation:

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_continuous_rod \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects/README.zh.md
```

After runtime changes, add validation by write set:

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_engagement_contract_shape.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_live_engagement_event_capture.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat -q -k "mlf4 or continuous_rod or rod_cut"
```

## Acceptance Criteria

- `continuous_rod` detonations produce same-chain rod/cut facts.
- Non-rod and no-detonation paths produce no positive rod/cut facts.
- Rod/cut facts vary with range, side/aspect, orientation, and component projection.
- Diagnostics can explain rod/cut facts from standard events.
- Component rows expose cut exposure without claiming component failure or structural breakup.

## Residual Map

Immediate:

- Lock the standard-event semantics of existing `rod_cut_margin` fields in 4B; 4A recommends reusing existing fields first.
- Separate accepted MLF-4 tests from historical Phase 3 retained scaffold tests.

Follow-on:

- MLF-5 consumes cut facts for component failure probability.
- MLF-6 consumes component failure for structural breakup.

Deferred:

- Real weapon rod parameters, Pk, wreck/debris, and AIM-120C/MQ-9 calibration.
