# TM05 Engagement Event Store DTO Closure Task Clusters

Status: `2026-06-02` accepted finite task-cluster plan for
[TM05 Engagement Event Store DTO Closure](README.md).

## Boundary Decision

TM05 removed the private long-argument engagement effects recording helper and
strengthened focused guards. It did not reopen TM04's accepted release
service, public API compatibility, P7 fire-control, raw runtime, or broad damage
model boundaries.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TM05-A` | worker | inherited / xhigh | Remove the private long-argument store helper and make effects damage append logic DTO-shaped internally. | `src/core/engine/simulation_kernel_engagement_event_store.h`, `src/core/engine/simulation_kernel_engagement_event_store.cpp` | No public interface changes; no release-service or damage-model edits. | Store object build or `cmake --build build-local-win --target ef_py -j2`; focused engagement event test if feasible. | `record_effects_damage_event_legacy` is gone and DTO event fields still populate effects/damage/trace outputs. | Parallel-safe with `TM05-B`; disjoint write set. | 1 | pass |
| `TM05-B` | worker | inherited / xhigh | Add guard coverage for DTO-only recorder/store behavior and named bridge preservation. | `tests/architecture/test_wp22_structural_guardrails.py`, `tests/runtime/engagement/test_live_engagement_event_capture.py` | No production code edits; no docs edits. | Focused pytest targets for touched tests. | Guards fail if public or private long-argument effects recording is reintroduced. | Parallel-safe with `TM05-A`; may be red until `TM05-A` lands. | 1 | pass |
| `TM05-C` | integration owner | inherited / xhigh | Integrate worker packets, run validation, and update TM05/TM04/parent docs without overclaiming. | TM05 docs, parent indexes, minimal status text only | No new implementation after validation starts. | `git diff --check`; `cmake --build build-local-win --target ef_py -j2`; focused structural/runtime pytest suite. | Validation and docs agree on accepted or blocked state. | Serial after `TM05-A` and `TM05-B`. | 1 | pass |

## Dispatch Rules

- Every worker packet must map to exactly one cluster above.
- Workers are not alone in the worktree and must not revert edits made by
  others.
- Do not let two workers edit the same source or test file concurrently.
- Keep acceptance/closure serial.
- Follow
  [Subagent Usage Policy](../../../../standards/governance/subagent_usage_policy.md).

## Worker Packet Requirements

```md
status: pass | partial | blocked | failed
touched files:
commands/outcomes:
remaining paths:
behavior risks:
integration notes:
```

## Validation Plan

Run from the repository root:

```powershell
git diff --check
cmake --build build-local-win --target ef_py -j2
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free tests/architecture/test_wp22_structural_guardrails.py::test_tm04_weapon_release_service_is_not_a_kernel_forwarding_adapter
$env:PYTHONPATH='build-local-win'; python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py
```

## Validation Outcome

`2026-06-02` TM05-C accepted:

- `git diff --check`: pass, with LF/CRLF working-copy warnings only.
- `cmake --build build-local-win --target ef_py -j2`: pass.
- Focused structural guards: `2 passed`.
- Engagement runtime event capture suite: `7 passed`.

## Acceptance Criteria

- `SimulationKernelEngagementEventStore` exposes and implements the public DTO
  recorder path without a private `record_effects_damage_event_legacy` helper.
- Effects, damage report, and diagnostics trace outputs remain populated from
  DTO data.
- Focused guards and runtime engagement tests pass.
- TM04 remains accepted only for its bounded slice.

## Residual Map

Held:

- Broader `SimulationKernel` decomposition.
- P7 launch/fire-control redesign.
- Broad damage-model cleanup.
