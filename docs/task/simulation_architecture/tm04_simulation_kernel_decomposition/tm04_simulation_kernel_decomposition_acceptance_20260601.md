# TM04 SimulationKernel Decomposition Acceptance Gate

Status: `2026-06-01` active acceptance gate; TM04 is not yet accepted.

Parent: [TM04 SimulationKernel Decomposition](README.md).

## Accepted Scope Target

TM04 can accept only the bounded `SimulationKernel` decomposition slice covering
engagement-event ownership, weapon-release service ownership, DTO-shaped effects
recording, focused damage bridge decisions, and synchronized validation records.

## Current Acceptance State

| Gate | State | Evidence | Required before acceptance |
| --- | --- | --- | --- |
| Public service inheritance removed from `SimulationKernel` | pass | [simulation_kernel.h](../../../../src/core/engine/simulation_kernel.h) | Keep structural guards green. |
| Engagement event store extracted | pass | [simulation_kernel_engagement_event_store.cpp](../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Keep event ownership out of kernel implementation files. |
| Weapon release service is independent | pass | [simulation_kernel_weapon_release_service.cpp](../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) owns release decisions and release-side state mutation behind explicit dependencies; [simulation_kernel_weapon_api.cpp](../../../../src/core/engine/simulation_kernel_weapon_api.cpp) is now a compatibility wrapper. | Keep focused service guard green. |
| Effects damage recorder is DTO-shaped | partial | [engagement_event_recorder.h](../../../../src/core/interfaces/engagement_event_recorder.h) contains both DTO and legacy long-argument overloads. | Complete `TM04-D`. |
| Naval/damage coupling is bounded | partial | Non-CIWS naval damage is explicit as an injected proximity-hit callback from the release service to existing debug damage behavior. | Add a narrow bridge or record a named blocker in `TM04-E`. |
| Validation matrix is current | pass / round 1 | `git diff --check`, `cmake --build build --target ef_py -j2`, focused structural guards, and focused engagement/launch runtime suite passed during Round 1 acceptance. | Re-run after `TM04-D` / `TM04-E` implementation. |
| Parent indexes synchronized | pass | [../README.md](../README.md) and [../README.zh.md](../README.zh.md) link the TM04 entry, task clusters, status, dispatch queue, and acceptance gate. | Re-sync after final state changes. |

## Required Validation Evidence

Round 1 observed:

```bash
git diff --check
cmake --build build --target ef_py -j2
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free tests/architecture/test_wp22_structural_guardrails.py::test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter
PYTHONPATH=build python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes: `git diff --check` passed, `ef_py` build passed, focused structural
guards reported `2 passed`, and the focused engagement/launch runtime suite
reported `29 passed`.

## Forbidden Acceptance Claims

- Do not mark TM04 accepted for full `SimulationKernel` decomposition while
  `SimulationKernelWeaponReleaseService` still forwards the core release flow
  through `SimulationKernel&`.
- Do not count docs-only setup as runtime validation.
- Do not claim P7 launch/fire-control closure, damage-model maturity, raw-runtime
  retirement, backend support, or facade maturity.
- Do not mark TM04 fully accepted until `TM04-D` and `TM04-E` either pass
  implementation gates or are explicitly closed as named residuals/blockers.

## Closeout Requirement

Before TM04 can move to `accepted` or `closed`, this file must be updated with
the final command outcomes, residual map, forbidden-claim check, and parent
index synchronization state.
