# A2 MLF-2 Missile Approach Geometry And Fuze Evaluation Task Clusters

Status: `2026-06-09` finite task-cluster plan for [README.md](README.md). MLF-2B, MLF-2C, MLF-2D, MLF-2E, and MLF-2F are accepted; MLF-2G acceptance closeout is next.

Chinese main text: [missile_lethality_geometry_fuze_task_clusters_20260609.zh.md](missile_lethality_geometry_fuze_task_clusters_20260609.zh.md)

Parent links:

- A2 pointer: [../README.md](../README.md)
- Current README: [README.md](README.md)
- Current status: [missile_lethality_geometry_fuze_current_status_20260609.md](missile_lethality_geometry_fuze_current_status_20260609.md)
- Dispatch queue: [missile_lethality_geometry_fuze_dispatch_queue_20260609.md](missile_lethality_geometry_fuze_dispatch_queue_20260609.md)
- MLF-1 evidence package: [../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md](../missile_lethality_model_foundation/archive/mlf_1_chain_contract_accepted_20260609/README.md)

## Boundary Decision

This subproject advances MLF-2 only: approach geometry and fuze evaluation. It may modify controlled scenarios, event contracts, event recording, diagnostic export, and focused tests. It must not implement fragmentation, continuous rod, structural breakup, debris/wreck objects, Pk, or weapon/target-specific lethality conclusions.

MLF-2 does not output "kill". It outputs nearest-approach geometry, armed state, trigger state, trigger type, trigger/no-trigger/delay/failure reason, and detonation state for later warhead-effect models.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `MLF-2A Boundary And Index` | main thread | n/a | Create independent MLF-2 subproject and freeze goal, boundary, phases, and parent navigation | this subproject README/status/task cluster/dispatch queue/archive index; A2 parent README; MLF-1 pointer README | runtime edits, probe implementation, parameter tuning, worker dispatch | `git diff --check -- docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_geometry_fuze docs/task/air_combat/a2_high_fidelity_damage_model/README*.md` | future agents can resume the subproject independently, and MLF-2 does not continue in the MLF-1 folder | first, serial | 1 | pass |
| `MLF-2B Controlled Geometry Fixtures` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | n/a | Design or implement controlled fixtures for range, aspect, closure, altitude offset, and target attitude | `tests/runtime/air_combat/weapon_guidance_realism/geometry_fixtures.py`; `tests/runtime/air_combat/test_weapon_guidance_realism_guards.py` | fuze physics, warhead effects, kill thresholds, real weapon calibration | worker packet + focused fixture/probe tests; JSON or py_compile checks | the same fixture can reliably generate different geometry inputs without relying on learned firing behavior | after 2A; serial before event writers | 2 | pass |
| `MLF-2C NearestApproachEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` | n/a | Let live or controlled scenarios write nearest-approach events | `src/components/combat/weapon.h`; `src/core/interfaces/engagement_event_recorder.h`; `src/core/engine/simulation_kernel_engagement_event_store.h`; `src/core/engine/simulation_kernel_engagement_event_store.cpp`; `src/core/engine/simulation_kernel_weapon_release_service.cpp`; `src/interfaces/python/bindings_core.cpp`; `src/systems/combat/damage_system.h`; related geometry/fuze tests | fuze trigger decision, effects loads, reward consumption | `ef_py` build; 3 missile geometry/fuze focused tests; 7 engagement event capture regressions; diff check | misses and no-detonation cases still have nearest-approach records and reasons; nearest-point time comes from the point update moment | after 2B; serial before FuzeEvaluationEvent | 2 | pass |
| `MLF-2D FuzeEvaluationEvent Writer` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / future fuze worker | n/a | Write armed/contact/proximity/delay/no-trigger/failure reasons | `src/core/interfaces/engagement_event_recorder.h`; `src/core/engine/simulation_kernel_engagement_event_store.h`; `src/core/engine/simulation_kernel_engagement_event_store.cpp`; `src/systems/combat/damage_system.h`; related geometry/fuze tests | fragmentation/rod, structural breakup, direct kill, real fuze authority | `ef_py` build; 4 missile geometry/fuze focused tests; 7 engagement event capture regressions; diff check | contact and proximity decisions are separate; no-trigger cases include reason | after 2C field ids; can parallel with 2E after APIs freeze | 2 | pass |
| `MLF-2E Diagnostics Projection` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / main thread | n/a | Make process probe emit geometry/fuze stage rows and summary per munition | `tools/diagnostics/air_combat_stage0_process_probe.py`; `tests/diagnostics/test_air_combat_process_probe.py`; this subproject evidence record | reward semantics, runtime physics decision, long-term legacy aliases | `tests/diagnostics/test_air_combat_process_probe.py -q` | trigger reason does not depend on `last_effect_*`; no-detonation cases report reasons | after 2C/2D API names freeze | 2 | pass |
| `MLF-2F Runtime Handoff Gate` | Sartre `019eac6a-0546-7cc0-ab6b-9c914dcb4c24` / main thread | n/a | Hand detonation state to existing effects model; no-trigger path explicitly produces no physical effect | `tests/runtime/air_combat/weapon_guidance_realism/fuze.py`; this subproject evidence record | warhead mechanism, target breakup, training win/loss, entity deletion | 3 focused fuze gate tests | only detonation enters later effects; no-trigger/failure/not-armed cases do not silently disappear | after 2C/2D/2E | 2 | pass |
| `MLF-2G Acceptance And Archive Prep` | main thread | n/a | Summarize evidence and update status, parent navigation, and residual map | this subproject README/status/task cluster/dispatch queue/archive index; A2 README | overclaiming real AIM-120C/MQ-9, Pk, or breakup authority | docs diff check + referenced focused tests | accepted/held state matches evidence and MLF-3+ residuals are explicit | last, serial | 1 | planned / ready |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Do not let two workers edit the same event-field table, runtime decision block, or status line concurrently.
- `MLF-2B` must precede runtime writers because trigger differences cannot be accepted without controlled geometry input.
- `MLF-2E` can be dispatched only after `MLF-2C` and `MLF-2D` field names freeze.
- `MLF-2F` must wait until geometry/fuze events are observable.
- Do not create a new conversation thread; subagents, if used, must stay inside the current controlled workflow.

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

Every returned packet must also state:

- Whether event field names or meanings changed.
- Whether new default parameters were added; if yes, their source and evidence grade.
- Whether no-trigger/failure path evidence exists.
- Whether direct-kill, direct-crash, and entity-delete rules were avoided.

## Validation Plan

Planning-stage validation:

```bash
git diff --check -- \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_geometry_fuze \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/README.zh.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_model_foundation/README.md \
  docs/task/air_combat/a2_high_fidelity_damage_model/missile_lethality_model_foundation/README.zh.md
```

After code work starts, add commands matching the touched surface at minimum:

```bash
python -m py_compile tools/diagnostics/air_combat_stage0_process_probe.py tests/diagnostics/test_air_combat_process_probe.py
python -m pytest tests/diagnostics/test_air_combat_process_probe.py -q
python -m pytest tests/runtime/air_combat/test_air_combat_reward_surface.py -q
```

If new C++ contract or event-store tests are added, include the relevant build/CTest target.

## Acceptance Criteria

- Every missile has a stable chain id linking launch, nearest approach, fuze evaluation, and later effects events.
- Controlled range, aspect, speed, altitude offset, and attitude changes produce explainable differences.
- No-detonation cases report a reason.
- Contact, proximity, not-armed, missed-window, delay, and failure are not collapsed into one vague state.
- Detonation state only feeds later effects models and does not directly produce kill, breakup, crash, or reward conclusions.
- Old `last_effect_*` fields are not expanded into long-term interfaces.

## Residual Map

| Residual | Owner | Release condition |
| --- | --- | --- |
| Fragmentation / continuous-rod model missing | future MLF-3/MLF-4 | MLF-2 only produces detonation state; later models own mechanism effects |
| Structural breakup and debris/wreck objects missing | future MLF-6/MLF-8 | component loads and structural failure models pass |
| Pk/statistical layer missing | future MLF-9 | high-detail chain runs before trend checks are added |
| AIM-120C/MQ-9 case remains unresolved | future calibration gate | geometry, fuze, warhead, target vulnerability, and structural models have traceable evidence |
