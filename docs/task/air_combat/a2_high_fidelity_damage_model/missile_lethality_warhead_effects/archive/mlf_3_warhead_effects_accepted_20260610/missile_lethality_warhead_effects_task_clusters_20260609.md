# A2 MLF-3 Warhead Effects Task Clusters

Status: `2026-06-10` MLF-3 standard load-chain focused accepted for [README.md](README.md). `MLF-3A-G` have closed the standard load-fact chain for this phase; real-weapon calibration, structural breakup, debris/wreck, and Pk remain future phases.

Chinese main text: [missile_lethality_warhead_effects_task_clusters_20260609.zh.md](missile_lethality_warhead_effects_task_clusters_20260609.zh.md)

Parent links:

- Current MLF-3 pointer: [../../README.md](../../README.md)
- A2 pointer: [../../../README.md](../../../README.md)
- MLF-2 archive: [../../../missile_lethality_geometry_fuze/README.md](../../../missile_lethality_geometry_fuze/README.md)
- Archived package README: [README.md](README.md)
- Current status: [missile_lethality_warhead_effects_current_status_20260609.md](missile_lethality_warhead_effects_current_status_20260609.md)
- Dispatch queue: [missile_lethality_warhead_effects_dispatch_queue_20260609.md](missile_lethality_warhead_effects_dispatch_queue_20260609.md)

## Boundary Decision

MLF-3 only handles post-detonation generic warhead effects and load facts. It may modify warhead-mechanism events, spatial-coverage events, component-load events, standard-event output from the current effects model, diagnostics projection, and focused tests.

MLF-3 does not output "kill". It outputs mechanism family, mechanism load, spatial coverage, and component load for later vulnerability, structure, and debris phases.

Data enters under the research rule only: generic, uncalibrated, and replaceable. Type-specific data may have reserved fields and replacement paths, but it must not land in this phase as true weapon or target parameters.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-3A Boundary And Inventory` | Sartre / current session subagent | n/a | Inventory current warhead/spatial/component fields, tests, and live-writer gaps | this subproject docs; read-only source/test audit record | runtime edits, parameter tuning, real weapon calibration | docs diff check; read-only audit packet | gaps and reusable entries can be resumed by a future worker | first, serial | 1 | accepted |
| `MLF-3B Standard Event Writers` | main thread | n/a | Add warhead/spatial/component recorder and event-store writers | `src/core/interfaces/engagement_event_recorder.h`; `src/core/engine/simulation_kernel_engagement_event_store.*`; related bindings/tests | effects physics, damage/reward semantics | `ef_py` build; engagement event capture tests | detonation exports standard events with MLF-2-aligned parent/chain ids | after 3A | 2 | live gate focused pass |
| `MLF-3C Generic Blast-Fragmentation Loads` | Planck + Heisenberg read-only audit / accepted by main thread | inherited | Implement generic uncalibrated fragment/blast mechanism loads | focused standard-event tests; read-only audit of `default_effects_warhead_detail.inc` | real AIM-120C parameters, continuous rod, Pk | family/range/aspect focused tests | loads change with distance, direction, and family | after 3B | 2 | focused pass |
| `MLF-3D Spatial Coverage And Component Load` | Euclid read-only audit + Fermat worker / accepted by main thread | n/a | Project mechanism loads onto hitboxes/components and write standard load events | `default_effects_spatial_projection_detail.inc`; `tests/runtime/air_combat/test_mlf3_spatial_component_projection.py` | calibrated component failure probability, structural breakup | focused projection tests | spatial coverage and component load are readable from standard events | after 3C | 2 | focused pass |
| `MLF-3E Diagnostics Projection` | main thread | n/a | Make diagnostics prioritize standard warhead/spatial/component events | `tools/diagnostics/air_combat_stage0_process_probe.py`; diagnostics tests | reward semantics, effects physics | process probe tests | old `EffectsEvent` is same-chain fallback only | after 3B-D | 2 | focused pass |
| `MLF-3F Runtime Handoff Gate` | main thread / future worker | n/a | Pin no-detonation/no-load and detonation/one-load-chain behavior | focused fuze/warhead tests | direct kill, direct crash, entity deletion | gate tests | no-detonation path has no warhead/spatial/component standard events | after 3E | 1 | focused pass |
| `MLF-3G Acceptance And Archive Prep` | main thread | n/a | Summarize accepted/held state and archive | this README/status/task cluster/dispatch/archive; A2 README | overclaiming breakup, Pk, or real weapon conclusions | docs diff check + referenced tests | accepted/held state matches evidence | after 3D | 1 | focused pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not let two workers edit the recorder interface, event-store writer, effects-model core fragments, or status line concurrently.
- Do not create a new conversation thread; subagents, if used, must stay inside the current controlled workflow.
- No runtime writes before MLF-3B; MLF-3A is read-only.
- Every implementation must preserve "no detonation means no warhead load".

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
- Whether new defaults were added; if yes, source and evidence level.
- If data is involved, whether it preserves the generic research rule and keeps source category, scope, unit, uncertainty, and replacement rule.
- Whether no-detonation paths still have no warhead/spatial/component events.
- Whether direct kill, direct crash, and entity-deletion rules were avoided.

## Validation Plan

Planning validation:

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_warhead_effects \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md
```

After code changes, add validation by write set:

```bash
cmake --build build-workshop --target ef_py -j2
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/engagement/test_live_engagement_event_capture.py -q
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_weapon_guidance_realism_guards.py -q -k "warhead or fuze"
PYTHONPATH=build-workshop ./.venv/bin/python -m pytest tests/runtime/air_combat/test_diagnostics_probe_contracts.py -q
```

## Acceptance Criteria

- Detonation emits same-chain warhead/spatial/component standard events.
- No-detonation paths have no warhead-load events.
- Fragment/blast loads vary with range, aspect, family, and spatial coverage.
- Diagnostics explain component load without claiming kill.
- Defaults carry evidence level and applicability.

## Residual Map

| Residual | Owner | Release condition |
| --- | --- | --- |
| Continuous-rod cutting | future MLF-4 | MLF-3 blast-fragmentation standard load chain accepted |
| Target vulnerability/failure probability | future MLF-5 | ComponentLoadEvent is stable |
| Structural breakup and debris/wreck | future MLF-6/MLF-8 | Component failure and structure models accepted |
| Pk/statistical layer | future MLF-9 | High-detail chain is replayable |
| AIM-120C/MQ-9 case | future calibration gate | Geometry, fuze, warhead, vulnerability, and structure models have traceable evidence |
