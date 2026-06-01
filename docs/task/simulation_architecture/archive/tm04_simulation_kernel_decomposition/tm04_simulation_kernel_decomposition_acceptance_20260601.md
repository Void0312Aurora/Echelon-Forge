# TM04 SimulationKernel Decomposition Acceptance Gate

Status: `2026-06-02` accepted bounded decomposition slice.

Parent: [TM04 SimulationKernel Decomposition](README.md).

## Accepted Scope Target

TM04 can accept only the bounded `SimulationKernel` decomposition slice covering
engagement-event ownership, weapon-release service ownership, DTO-shaped effects
recording, focused damage bridge decisions, and synchronized validation records.

## Current Acceptance State

| Gate | State | Evidence | Required before acceptance |
| --- | --- | --- | --- |
| Public service inheritance removed from `SimulationKernel` | pass | [simulation_kernel.h](../../../../../src/core/engine/simulation_kernel.h) | Keep structural guards green. |
| Engagement event store extracted | pass | [simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Keep event ownership out of kernel implementation files. |
| Weapon release service is independent | pass | [simulation_kernel_weapon_release_service.cpp](../../../../../src/core/engine/simulation_kernel_weapon_release_service.cpp) owns release decisions and release-side state mutation behind explicit dependencies; [simulation_kernel_weapon_api.cpp](../../../../../src/core/engine/simulation_kernel_weapon_api.cpp) is now a compatibility wrapper. | Keep focused service guard green. |
| Effects damage recorder is DTO-shaped | pass / contained at TM04 acceptance; closed by TM05 | [engagement_event_recorder.h](../../../../../src/core/interfaces/engagement_event_recorder.h) exposes the DTO path only; [damage_system.h](../../../../../src/systems/combat/damage_system.h) and [simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp) build `EngagementEffectsDamageEventRecord` before recording. | No TM04 acceptance blocker; the private store helper was contained at TM04 acceptance and was later removed by TM05. |
| Naval/damage coupling is bounded | pass | [weapon_release_damage_bridge.h](../../../../../src/core/interfaces/weapon_release_damage_bridge.h) names the remaining bridge from release service to compatibility debug damage behavior. | Keep broader damage-model changes out of TM04. |
| Validation matrix is current | pass / final | `git diff --check`, `cmake --build build-local-win --target ef_py -j2`, focused structural guards, and focused engagement/launch runtime suite passed during final acceptance. | Re-run only if this slice changes again. |
| Parent indexes synchronized | pass | [../README.md](../../README.md) and [../README.zh.md](../../README.zh.md) link the TM04 entry, task clusters, status, dispatch queue, and acceptance gate. | Parent status rows now mark TM04 accepted. |

## Required Validation Evidence

Final acceptance observed:

```powershell
git diff --check
cmake --build build-local-win --target ef_py -j2
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free tests/architecture/test_wp22_structural_guardrails.py::test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter
$env:PYTHONPATH='build-local-win'; python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

Outcomes: `git diff --check` passed with Windows line-ending warnings only,
`ef_py` build passed, focused structural guards reported `2 passed`, and the
focused engagement/launch runtime suite reported `27 passed, 2 skipped`.

## Forbidden Acceptance Claims

- Do not mark TM04 accepted for full `SimulationKernel` decomposition; this is
  only the bounded engagement/release/effects slice.
- Do not count docs-only setup as runtime validation.
- Do not claim P7 launch/fire-control closure, damage-model maturity, raw-runtime
  retirement, backend support, or facade maturity.
- Do not treat the private store helper that existed at TM04 acceptance as a
  public recorder overload; TM05 later removed that helper.

## Closeout Requirement

TM04 is accepted for the bounded slice above. Any full P7 fire-control,
raw-runtime retirement, or broad damage-model work requires a new task lane.
