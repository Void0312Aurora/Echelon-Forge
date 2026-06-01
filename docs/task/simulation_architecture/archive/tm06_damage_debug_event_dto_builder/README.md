# TM06 Damage Debug Event DTO Builder

Status: `2026-06-02` accepted bounded cleanup slice after
[TM05 Engagement Event Store DTO Closure](../tm05_engagement_event_store_dto_closure/README.md).

Language:

- English canonical: `README.md`
- Chinese companion: not required yet; narrow implementation cleanup

Related authority:

- Parent task domain: [Simulation Architecture](../../README.md)
- Agent authority map:
  [document_authority_map.md](../../../../agent/rules/document_authority_map.md)
- Subproject standard:
  [subproject_creation_standard.md](../../../../agent/rules/subproject_creation_standard.md)
- Subagent governance:
  [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md)
- Predecessor lane:
  [TM05 Engagement Event Store DTO Closure](../tm05_engagement_event_store_dto_closure/README.md)

## Purpose

TM06 continues the bounded `SimulationKernel` cleanup by reducing duplicated
debug damage DTO construction in
[simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp).

The three debug proximity-hit entry points already preserve public behavior and
record `EngagementEffectsDamageEventRecord` instances into the accepted event
store. They still repeat synthetic missile setup, before/after capture, and
`EffectsEvent` field population. TM06 contains that repetition behind local
helper logic while keeping public debug APIs, damage semantics, and event output
stable.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Public debug damage API | pass / compatibility | [simulation_kernel.h](../../../../../src/core/engine/simulation_kernel.h) | Method signatures remain public compatibility/debug surface. |
| Event DTO recording | pass | [simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp) | Debug paths already build `EngagementEffectsDamageEventRecord` before recording. |
| Local duplication | pass | [simulation_kernel_damage_debug_api.cpp](../../../../../src/core/engine/simulation_kernel_damage_debug_api.cpp) | Debug paths now route event DTO field setup through `build_debug_effects_damage_event_record`. |

## Scope

In scope:

- Add local helper logic inside `simulation_kernel_damage_debug_api.cpp` for
  synthetic debug proximity-hit DTO construction.
- Preserve all public debug method signatures and return values.
- Preserve effects model invocation, before/after damage snapshots, engagement
  event recording, and impact entity cleanup.
- Add focused structural/runtime guards for the helper boundary.

Out of scope:

- No public debug API removal.
- No damage-model rewrite or changed effects semantics.
- No P7 launch/fire-control redesign.
- No broader `SimulationKernel` decomposition claim.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Record the finite cleanup surface. | TM05 accepted and debug damage duplication identified. | README and task clusters exist. | pass |
| `P1 Debug DTO Helper` | Move repeated debug DTO setup behind local helper logic. | Cluster `TM06-A` dispatched. | Debug damage API has one helper-owned DTO construction path. | pass |
| `P2 Guards` | Prevent local duplication from returning silently. | Cluster `TM06-B` dispatched. | Focused tests assert helper presence and preserved event capture. | pass |
| `P3 Integration` | Validate and synchronize status. | Implementation workers return packets. | Focused build/tests pass and docs are updated. | pass |

## Task Clusters

- Task cluster plan:
  [tm06_damage_debug_event_dto_builder_task_clusters_20260602.md](tm06_damage_debug_event_dto_builder_task_clusters_20260602.md)

## Outputs And Evidence

- Local helper implementation under `src/core/engine/simulation_kernel_damage_debug_api.cpp`.
- Focused guards under `tests/architecture/` and `tests/runtime/engagement/`.
- Validation on `2026-06-02`:
  - `git diff --check`: pass, with LF/CRLF working-copy warnings only.
  - `cmake --build build-local-win --target ef_py -j2`: pass.
  - Focused structural guard: `1 passed`.
  - Engagement runtime event capture suite: `7 passed`.

## Acceptance Gate

TM06 is accepted because:

- Debug proximity-hit methods still expose the same public signatures and return
  behavior.
- Effects model invocation and impact entity cleanup remain in the debug damage
  path.
- Event records still populate DTO effects fields before recording.
- Focused structural/runtime tests and `ef_py` build pass.

## Residuals And Next Steps

- Closed: repeated debug damage DTO field setup in public debug proximity-hit
  methods.
- Held: public debug API retirement.
- Held: broader damage-model redesign.
- Held: any `SimulationKernel` cleanup outside debug damage DTO construction.

## Archive

No archive records yet.
