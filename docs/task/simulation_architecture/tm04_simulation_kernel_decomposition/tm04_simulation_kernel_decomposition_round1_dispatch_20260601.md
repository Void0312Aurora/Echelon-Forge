# TM04 SimulationKernel Decomposition Round 1 Dispatch

Status: `2026-06-01` pass first-round dispatch record for
[TM04 SimulationKernel Decomposition](README.md).

This record opens the first execution round after TM04 documentation setup. It
does not prove full TM04 acceptance.

## Dispatch Set

| Dispatch | Cluster | Agent | Reasoning | Assignment | Write policy | Expected return |
| --- | --- | --- | --- | --- | --- | --- |
| `TM04-C1 release service migration` | `TM04-C` | `019e83cf-8961-78e3-9610-25ad528a5f75` / Laplace | xhigh | Move `SimulationKernelWeaponReleaseService` beyond pure `SimulationKernel&` forwarding in the first safe implementation slice. | May write only the TM04-C release-service scope named in the task-cluster plan. Must not touch A2/default-effects, forward docs, or unrelated dirty work. | Standard worker packet with status, touched files, commands/outcomes, remaining paths, behavior risks, and integration notes. |
| `TM04-D1 effects DTO diagnostics` | `TM04-D` | `019e83cf-b3ef-7a32-8739-15edb6c5c7ba` / Bacon | xhigh | Map DTO call paths, legacy overload usage, and a safe future write set for effects damage event recording. | Read-only. No file edits. | Source facts, recommended write set, parallel risks, validation, blockers. |
| `TM04-E1 naval damage bridge diagnostics` | `TM04-E` | `019e83cf-df72-7140-93e8-daf565b0f35a` / Jason | xhigh | Map naval deck-gun/CIWS damage coupling and decide whether a narrow damage bridge is needed. | Read-only. No file edits. | Source facts, minimal bridge recommendation, validation, parallel risks, blockers. |

## Result

| Dispatch | Result | Evidence | Residual |
| --- | --- | --- | --- |
| `TM04-C1 release service migration` | pass | `SimulationKernelWeaponReleaseService` now owns release decisions, launcher mutation, munition spawn, and launch-event recording behind explicit dependencies. Kernel weapon APIs are compatibility wrappers over `IWeaponReleaseService`. | Non-CIWS naval damage still uses an injected proximity-hit callback to existing debug damage behavior. |
| `TM04-D1 effects DTO diagnostics` | pass / diagnostics | Source facts show DTO coverage is currently narrow and the legacy overload remains used by `damage_system.h` and debug damage paths. | Schedule serialized DTO implementation after release-service integration. |
| `TM04-E1 naval damage bridge diagnostics` | pass / diagnostics | Source facts identify `fire_naval_weapon -> debug_apply_proximity_hit` as the remaining source-backed coupling and recommend a narrow release-damage bridge. | Implement or explicitly block the narrow bridge in `TM04-E`. |

## Integration Rule

Only `TM04-C1` may produce code in round 1. `TM04-D1` and `TM04-E1` may inform
the next implementation slice, but their findings do not authorize concurrent
edits to `simulation_kernel_weapon_api.cpp`.

## First-Round Close Condition

Round 1 closed when:

- `TM04-C1` returned pass with a worker packet;
- `TM04-D1` and `TM04-E1` returned source-fact diagnostics;
- the integration owner updated the task-cluster status, dispatch queue, and
  current-status residual map.

## Immediate Validation Target

The integration owner should prefer focused validation before broad build work:

```bash
git diff --check
cmake --build build --target ef_py -j2
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free tests/architecture/test_wp22_structural_guardrails.py::test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter
PYTHONPATH=build python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Observed outcomes:

- `git diff --check`: pass.
- `cmake --build build --target ef_py -j2`: pass.
- Focused structural guards: `2 passed`.
- Focused engagement/launch runtime suite: `29 passed`.
