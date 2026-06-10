# G6-C Route-Move Boundary Cluster

Status: `2026-05-24` accepted for guardrails. Route movement remains held.

Cluster:

- `G6-C Route-Move Boundary Guardrails`

Round cap:

- one implementation round plus at most one repair round.

## Decision

G6-C does not release a movement scenario. It closes the next boundary step
needed before `G2 flat route move` can be considered.

Accepted boundary:

- Current G0/G1 ground scenarios remain compatibility-shell fixtures.
- Unknown explicit tasking profile hints fail closed instead of silently
  falling back to air.
- Ground runtime code must use the shared tasking bridge rather than importing
  private ground profile modules directly.
- G1 fixtures cannot claim movement, terrain, sensing, fires, damage, native
  ground platform behavior, observation export, or combat evidence.

Held:

- `ground_platoon_flat_route_move_v1`;
- runtime-loadable native ground platform schema;
- movement dynamics, terrain traversal, sensing, fires, damage, and contact
  reports.

## Task Cluster

| Stream | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Parallel / dependency | Round cap | Status |
|--------|-------|-------------------|------|-----------|-----------|------------|--------------|-----------------------|-----------|--------|
| `G6-C Route-Move Boundary Guardrails` | main-thread integration | current main thread | Record and enforce the first route-move release boundary without releasing movement behavior. | `docs/task/ground/g6_route_move_boundary/**`, `python/rl/tasking/bridge.py`, `tests/leader/test_tasking_profile_contracts.py`, `tests/architecture/ground/test_realism_gradient_guardrails.py`, ground README/queue/progress sync | scenario files, native ground platform schema, C++ DTOs, runtime movement, terrain, sensing, fires, damage, observation export | focused pytest, ground contract runner, `git diff --check` | unknown explicit profiles fail closed, ground scenarios stay G0/G1, runtime path has no private ground profile imports, route movement remains held | 1 implementation round plus at most 1 repair round | accepted |

## Implementation Notes

Profile inference:

- `tasking_profile_for_loader()` now treats explicit unknown
  `tasking_profile` or `service_profile` hints as a configuration error.
- The legacy air default remains only when no profile hint is present.

Guardrails:

- `tests/architecture/ground/test_realism_gradient_guardrails.py` checks that
  current ground scenarios keep the `Aircraft` compatibility spawn shell
  explicit and defer native ground runtime plus G2+ realism.
- The same test checks that runtime paths do not import
  `python.rl.profile.ground_profile` or `python.rl.tasking.ground_adapter`
  directly.

## Verification

Passed:

```bash
PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/leader/test_tasking_profile_contracts.py tests/architecture/ground/test_realism_gradient_guardrails.py
# 14 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python -m pytest -q tests/runtime/ground/test_ground_realism_gradient_mvp_scenarios.py tests/runtime/ground/test_ground_mvp_scenario.py tests/runtime/mission/test_ground_runtime_lifecycle_bridge.py tests/leader/test_tasking_profile_contracts.py
# 17 passed

PYTHONPATH=build-workshop:. CMO_BUILD_DIR=build-workshop ./.venv/bin/python tools/runners/run_scenario_contract.py --spec tests/contracts/unit/ground/task_order_ground_profile_defaults.json tests/contracts/unit/ground/task_order_ground_minimal_structures.json tests/contracts/unit/ground/task_order_ground_support_relationships.json
# PASS x3
```

Known unrelated workspace caveat:

- `tests/runtime/mission/test_naval_mission_command_mapping.py` currently fails
  in this workspace because the active `ef_py.MissionCommand` binding lacks
  `threat_state`. This was observed during a wider mixed-domain check and is
  not part of the G6-C ground boundary change.

## Residual Map

Next release decision:

- choose native ground platform schema first, or document an explicit movement
  compatibility boundary before adding `ground_platoon_flat_route_move_v1`.

Still deferred:

- terrain traversal and terrain masking;
- sensing, track fusion, and observation export;
- direct fire, indirect fire, effects, damage, suppression, and combat;
- broad ground command vocabulary beyond the current compatibility mission
  command shell.
