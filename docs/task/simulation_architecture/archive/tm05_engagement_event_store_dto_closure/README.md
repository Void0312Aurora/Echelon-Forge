# TM05 Engagement Event Store DTO Closure

Status: `2026-06-02` accepted bounded cleanup slice after
[TM04 SimulationKernel Decomposition](../tm04_simulation_kernel_decomposition/README.md).

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
  [TM04 SimulationKernel Decomposition](../tm04_simulation_kernel_decomposition/README.md)

## Purpose

TM05 closes the contained post-TM04 helper residual in the engagement event
store. At TM05 entry, TM04 had accepted the public DTO-shaped recorder surface,
but the store still used a private legacy-shaped helper to append effects,
damage report, and diagnostics trace records.

This lane removes that private long-argument helper, keeps the store append path
DTO-shaped internally, and adds focused guards so future work does not
reintroduce public or private long-argument effects recording.

## Current State

| Area | Status | Evidence | Boundary |
| --- | --- | --- | --- |
| Public recorder interface | pass | [engagement_event_recorder.h](../../../../../src/core/interfaces/engagement_event_recorder.h) | Public surface is DTO-shaped; this does not prove store internals are DTO-only. |
| Store append helper | pass | [simulation_kernel_engagement_event_store.cpp](../../../../../src/core/engine/simulation_kernel_engagement_event_store.cpp) | Private long-argument helper removed; store appends effects, damage report, and diagnostics trace records from `EngagementEffectsDamageEventRecord`. |
| Release damage bridge | pass | [weapon_release_damage_bridge.h](../../../../../src/core/interfaces/weapon_release_damage_bridge.h) | Bridge cleanup is not reopened by TM05. |

## Scope

In scope:

- Remove the private long-argument effects damage helper from
  `SimulationKernelEngagementEventStore`.
- Preserve event IDs, pending launch-event linkage, sorted exports, damage
  report derivation, and diagnostics traces.
- Add focused guard coverage for DTO-only recorder/store behavior.
- Keep TM04 accepted and update parent indexes only for the new TM05 route.

Out of scope:

- No P7 launch/fire-control redesign.
- No public API removal beyond the already accepted TM04 recorder surface.
- No damage-model rewrite.
- No raw-runtime retirement or broader `SimulationKernel` decomposition claim.

## Phase Plan

| Phase | Goal | Entry condition | Exit condition | Status |
| --- | --- | --- | --- | --- |
| `P0 Boundary` | Record a finite cleanup surface. | TM04 accepted with a contained private helper residual. | README and task clusters exist. | pass |
| `P1 Store Implementation` | Make store internals DTO-shaped. | Cluster `TM05-A` dispatched. | Private long-argument helper is removed. | pass |
| `P2 Guards` | Prevent DTO regression. | Cluster `TM05-B` dispatched. | Focused tests assert DTO-only public/store behavior. | pass |
| `P3 Integration` | Validate and synchronize status. | Implementation workers return packets. | Focused build/tests pass and docs are updated. | pass |

## Task Clusters

- Task cluster plan:
  [tm05_engagement_event_store_dto_closure_task_clusters_20260602.md](tm05_engagement_event_store_dto_closure_task_clusters_20260602.md)

## Outputs And Evidence

- Store implementation under `src/core/engine/`.
- Focused guards under `tests/architecture/` and `tests/runtime/engagement/`.
- Validation on `2026-06-02`:
  - `git diff --check`: pass, with LF/CRLF working-copy warnings only.
  - `cmake --build build-local-win --target ef_py -j2`: pass.
  - Focused structural guards: `2 passed`.
  - Engagement runtime event capture suite: `7 passed`.

## Acceptance Gate

TM05 is accepted because:

- No `record_effects_damage_event_legacy` helper or equivalent private
  long-argument recorder path remains in the store.
- Public effects damage recording stays DTO-shaped.
- Focused structural/runtime tests and `ef_py` build pass.
- TM04 remains accepted without expanding its claims.

## Residuals And Next Steps

- Closed: the post-TM04 private long-argument engagement event store helper.
- Held: broader P7 fire-control and damage-model changes.
- Held: any further `SimulationKernel` god-class cleanup beyond this store DTO
  helper slice.

## Archive

No archive records yet.
