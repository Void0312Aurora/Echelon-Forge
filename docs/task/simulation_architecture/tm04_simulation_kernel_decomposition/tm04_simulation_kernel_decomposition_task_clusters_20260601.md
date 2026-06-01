# TM04 SimulationKernel Decomposition Task Clusters

Status: `2026-06-01` finite task-cluster plan for
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
| `TM04-B` | integration owner | inherited / xhigh | Keep engagement event store extraction coherent and guarded. | `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/core/engine/engagement_event_types.h`, `src/core/interfaces/engagement_event_recorder.h`, `src/core/interfaces/engagement_launch_recorder.h`, focused tests, TM04 docs | No release-service migration; no effects-model rewrite. | Object builds for store/damage/weapon units; `python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py`; structural guard test. | Store owns buffers, IDs, damage snapshots, export sorting, pending launch ID, reset, and clear behavior; kernel does not reimplement them. | Can run before or beside `TM04-C` if write scopes stay disjoint. | 2 | partial |
| `TM04-C` | future worker | inherited / xhigh | Replace `SimulationKernelWeaponReleaseService` forwarding with a real release service using explicit dependencies. | `src/core/engine/simulation_kernel_services.*`, possibly new `src/core/engine/simulation_kernel_weapon_release_service.*`, `src/core/engine/simulation_kernel_weapon_api.cpp`, `src/core/engine/simulation_kernel.h`, `CMakeLists.txt`, focused release tests | No P7 scheduler redesign; no public API removal; no damage-model rewrite. | Relevant object builds; `python -m pytest -q tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py`; structural guards. | Core release flow no longer forwards through `SimulationKernel&`; wrappers are compatibility-only and source-backed. | Depends on `TM04-A`; coordinate with `TM04-E` before changing damage call paths. | 2 | planned |
| `TM04-D` | future worker | inherited / xhigh | Complete DTO-shaped effects damage event recording. | `src/core/interfaces/engagement_event_recorder.h`, `src/core/engine/simulation_kernel_engagement_event_store.*`, `src/core/engine/simulation_kernel_damage_debug_api.cpp`, `src/core/engine/simulation_kernel_weapon_api.cpp`, focused tests | Do not make `EffectsResult` the event DTO; do not move generated IDs or before/after derivation out of the store. | Object builds for damage/weapon/store units; `python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_munition_damage_adapter.py`; structural guards. | Primary call sites use `EngagementEffectsDamageEventRecord`; legacy long-argument overload is retired or explicitly contained. | Can run in parallel with `TM04-C` only if `simulation_kernel_weapon_api.cpp` ownership is scheduled serially. | 2 | planned |
| `TM04-E` | future worker | inherited / xhigh | Isolate naval deck-gun and CIWS release damage coupling behind a narrow bridge if required by `TM04-C`. | Candidate interface under `src/core/interfaces/`, release-service files, `src/core/engine/simulation_kernel_weapon_api.cpp`, focused naval tests | No broad damage model redesign; no change to effects semantics beyond routing. | Object builds; `python -m pytest -q tests/runtime/engagement/test_naval_launch_adapter.py`; naval CIWS mission-command runtime tests. | Remaining damage coupling is either behind a narrow interface or recorded as a named blocker. | Depends on `TM04-C` source facts; cannot edit same weapon API slice concurrently with `TM04-D`. | 2 | planned |
| `TM04-F` | integration owner | inherited / xhigh | Integrate code slices and run maintained validation. | Build/test scripts, focused docs, any touched C++/test files needed for integration | No new feature work after validation starts. | `ninja -C build CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_engagement_event_store.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_weapon_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_systems.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_observation_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_damage_debug_api.cpp.o`; focused pytest set; `cmake --build build --target ef_py -j2` when unrelated blocker is cleared. | Validation matrix records pass/block state with command outputs and blocker ownership. | Serial after implementation clusters. | 1 | planned |
| `TM04-G` | integration/docs owner | inherited / xhigh | Publish acceptance, blocked, or held closeout and update indexes/archive. | TM04 docs, parent simulation architecture indexes, archive README if historical records exist | No implementation. | `git diff --check`; docs link/path spot check; validation evidence copied from `TM04-F`. | Parent indexes, acceptance document, and residual map agree on final state. | Serial after `TM04-F`. | 1 | planned |

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
  [Subagent Usage Policy](../../../standards/governance/subagent_usage_policy.md).

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
ninja -C build CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_engagement_event_store.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_weapon_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_systems.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_observation_api.cpp.o CMakeFiles/ef_core.dir/src/core/engine/simulation_kernel_damage_debug_api.cpp.o
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free
python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py tests/runtime/engagement/test_launch_adapter_static_shape.py tests/runtime/engagement/test_munition_damage_adapter.py tests/runtime/engagement/test_air_launch_adapter.py tests/runtime/engagement/test_naval_launch_adapter.py tests/runtime/air_combat/test_air_combat_1v1_fire_missile.py
cmake --build build --target ef_py -j2
```

The full `ef_py` build remains externally blocked until the unrelated
`default_effects_model.cpp` / warhead detail dirty-work issue is resolved.

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

Immediate:

- Replace the forwarding `SimulationKernelWeaponReleaseService` adapter.
- Finish effects damage DTO migration and contain the legacy recorder overload.

Follow-on:

- Add a narrow damage bridge only if naval release migration still requires
  kernel-owned damage/debug behavior.
- Broaden structural guards once service boundaries stabilize.

Deferred:

- Full P7 launch/fire-control redesign.
- Public raw-runtime or compatibility retirement.
- Broad damage-model and default-effects-model refactors.
- Backend, facade, GPU, resident-state, training, or evaluation maturity claims.
