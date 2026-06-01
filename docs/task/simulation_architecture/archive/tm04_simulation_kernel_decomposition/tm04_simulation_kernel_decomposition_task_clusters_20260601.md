# TM04 SimulationKernel Decomposition Task Clusters

Status: `2026-06-02` accepted finite task-cluster plan for
[TM04 SimulationKernel Decomposition](README.md).

## Boundary Decision

TM04 may move concrete ownership out of `SimulationKernel` only through bounded
service, store, interface, DTO, and focused test changes. It must preserve public
behavior while reducing direct kernel responsibility. It must not claim full P7
launch/fire-control redesign, raw-runtime retirement, broad damage-model
replacement, or backend/facade capability maturity.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TM04-A` | main thread | inherited / xhigh | Create the durable subproject surface and synchronize parent indexes. | `docs/task/simulation_architecture/tm04_simulation_kernel_decomposition/**`, `docs/task/simulation_architecture/README.md`, `docs/task/simulation_architecture/README.zh.md` | No code changes; no runtime pass claim. | `git diff --check` passed; link/path spot checks passed. | Required docs exist with standard sections and parent links. | Serial documentation foundation. | 1 | pass |
| `TM04-B` | integration owner | inherited / xhigh | Keep engagement event store extraction coherent and guarded. | `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/core/engine/engagement_event_types.h`, `src/core/interfaces/engagement_event_recorder.h`, `src/core/interfaces/engagement_launch_recorder.h`, focused tests, TM04 docs | No release-service migration; no effects-model rewrite. | Object builds for store/damage/weapon units; `python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py`; structural guard test. | Store owns buffers, IDs, damage snapshots, export sorting, pending launch ID, reset, and clear behavior; kernel does not reimplement them. | Completed before/with `TM04-C` and retained through final validation. | 2 | pass |
| `TM04-C` | implementation worker | inherited / xhigh | Replace `SimulationKernelWeaponReleaseService` forwarding with a real release service using explicit dependencies. | `src/core/engine/simulation_kernel_services.*`, possibly new `src/core/engine/simulation_kernel_weapon_release_service.*`, `src/core/engine/simulation_kernel_weapon_api.cpp`, `src/core/engine/simulation_kernel.h`, `CMakeLists.txt`, focused release tests | No P7 scheduler redesign; no public API removal; no damage-model rewrite. | Round 1 build/tests passed; final Windows validation used `cmake --build build-local-win --target ef_py -j2` plus focused structural/runtime tests. | Core release flow no longer forwards through `SimulationKernel&`; wrappers are compatibility-only and source-backed. | Round 1 implementation integrated; later bridge and DTO work are separate validated clusters. | 2 | pass |
| `TM04-D` | implementation continuation | inherited / xhigh | Complete DTO-shaped effects damage event recording. | `src/core/interfaces/engagement_event_recorder.h`, `src/core/interfaces/engagement_effects_event_builder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/core/engine/simulation_kernel_damage_debug_api.cpp`, `src/systems/combat/damage_system.h`, focused tests | Do not make `EffectsResult` the event DTO; do not move generated IDs or before/after derivation out of the store. | `cmake --build build-local-win --target ef_py -j2`; focused structural guards; focused engagement/launch runtime suite. | Primary call sites use `EngagementEffectsDamageEventRecord`; legacy long-argument public recorder overload is retired, and the private store helper residual was closed by TM05. | Serialized after `TM04-C`. | 2 | pass |
| `TM04-E` | implementation continuation | inherited / xhigh | Isolate naval deck-gun and CIWS release damage coupling behind a narrow bridge if required by `TM04-C`. | `src/core/interfaces/weapon_release_damage_bridge.h`, release-service files, `src/core/engine/simulation_kernel.cpp`, focused naval tests | No broad damage model redesign; no change to effects semantics beyond routing. | `cmake --build build-local-win --target ef_py -j2`; focused structural guards; focused engagement/launch runtime suite. | Remaining non-CIWS damage coupling is behind a named `IWeaponReleaseDamageBridge` interface. | Serialized after `TM04-C`. | 2 | pass |
| `TM04-F` | integration owner | inherited / xhigh | Integrate code slices and run maintained validation. | Build/test scripts, focused docs, any touched C++/test files needed for integration | No new feature work after validation starts. | `git diff --check`; `cmake --build build-local-win --target ef_py -j2`; focused structural guards; focused engagement/launch runtime suite. | Validation matrix records pass state with command outputs. | Serial after implementation clusters. | 1 | pass |
| `TM04-G` | integration/docs owner | inherited / xhigh | Publish acceptance, blocked, or held closeout and update indexes/archive. | TM04 docs, parent simulation architecture indexes, archive README if historical records exist | No implementation. | `git diff --check`; docs link/path spot check; validation evidence copied from `TM04-F`. | Parent indexes, acceptance document, and residual map agree on final accepted state. | Serial after `TM04-F`. | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Use `reasoning_effort: xhigh` when dispatching TM04 subagents, unless a later
  owner instruction explicitly changes the reasoning setting.
- Keep one integration owner for shared C++ surfaces and all acceptance wording.
- Do not let two workers edit `simulation_kernel_weapon_api.cpp`,
  `engagement_event_recorder.h`, normative task tables, or final status lines at
  the same time.
- Stop and re-scope if a cluster exceeds its round cap.
- Follow the
  [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

Every delegated result must return:

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

A `blocked` result must name the blocker, owner, replacement condition,
validation gap, and forced review trigger. A `partial` result does not unlock
closure.

## Validation Plan

Run from the repository root unless explicitly stated otherwise:

```bash
git diff --check
cmake --build build-local-win --target ef_py -j2
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free tests/architecture/test_wp22_structural_guardrails.py::test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter
PYTHONPATH=build-local-win python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
```

The final Windows validation used the existing `build-local-win` directory.

## Acceptance Criteria

- `SimulationKernel` remains free of public release/event-recorder inheritance.
- Engagement event buffers, IDs, pending launch state, sorting, reset, clear,
  and damage snapshots stay in `SimulationKernelEngagementEventStore`.
- The weapon-release service core flow no longer depends on `SimulationKernel&`
  for release decisions, launcher mutation, munition spawn, or launch-event
  recording.
- Effects damage recording has a maintained DTO path with the legacy
  long-argument overload retired or explicitly contained.
- Focused C++ object builds and architecture/runtime tests pass, with unrelated
  blockers recorded by source file and failing command.
- Parent indexes and TM04 acceptance/current-status documents match the final
  state.

## Residual Map

Accepted:

- `SimulationKernelWeaponReleaseService` is a real service with explicit
  dependencies.
- Effects damage recording uses DTO-shaped call sites; TM05 later removed the
  private legacy-shaped store helper.
- Naval release damage uses a named bridge interface for the remaining
  compatibility path.

Follow-on:

- Closed by TM05: the private store helper was inlined behind the DTO path.
- Broaden structural guards only under a later structural-maintenance lane.

Deferred:

- Full P7 launch/fire-control redesign.
- Public raw-runtime or compatibility retirement.
- Broad damage-model and default-effects-model refactors.
- Backend, facade, GPU, resident-state, training, or evaluation maturity claims.
