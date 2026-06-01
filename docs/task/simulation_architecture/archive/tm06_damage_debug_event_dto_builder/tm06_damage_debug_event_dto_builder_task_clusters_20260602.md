# TM06 Damage Debug Event DTO Builder Task Clusters

Status: `2026-06-02` accepted finite task-cluster plan for
[TM06 Damage Debug Event DTO Builder](README.md).

## Boundary Decision

TM06 reduced repeated debug proximity-hit DTO construction inside
`simulation_kernel_damage_debug_api.cpp` and added focused guards. It did not
remove public debug methods, change damage semantics, redesign P7
launch/fire-control, or claim full `SimulationKernel` decomposition.

## Finite Task Cluster List

| Cluster | Owner | Model / reasoning | Goal | Write set | Non-goals | Validation | Closure gate | Dependency / parallel | Round cap | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TM06-A` | worker | inherited / xhigh | Extract repeated debug proximity-hit DTO construction into local helper logic while preserving behavior. | `src/core/engine/simulation_kernel_damage_debug_api.cpp` | No public header/API changes; no tests/docs edits; no damage-model redesign. | `cmake --build build-local-win --target ef_py -j2`; focused engagement runtime test if feasible. | Debug damage paths record equivalent DTOs through one helper-owned construction path and still destruct impact entities. | Parallel-safe with `TM06-B`; disjoint write set. | 1 | pass |
| `TM06-B` | worker | inherited / xhigh | Add focused guards for debug DTO helper structure and preserved event capture. | `tests/architecture/test_wp22_structural_guardrails.py`, `tests/runtime/engagement/test_live_engagement_event_capture.py` | No production code edits; no docs edits. | Focused pytest targets for touched tests. | Guards fail if debug damage paths return to duplicated ad hoc DTO construction or stop recording effects DTOs. | Parallel-safe with `TM06-A`; may be red until `TM06-A` lands. | 1 | pass |
| `TM06-C` | integration owner | inherited / xhigh | Integrate worker packets, run validation, and update TM06/parent docs without overclaiming. | TM06 docs, parent indexes, minimal status text only | No new implementation after validation starts. | `git diff --check`; `cmake --build build-local-win --target ef_py -j2`; focused structural/runtime pytest suite. | Validation and docs agree on accepted or blocked state. | Serial after `TM06-A` and `TM06-B`. | 1 | pass |

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
python -m pytest -q tests/architecture/test_wp22_structural_guardrails.py::test_wp22_pilot_weapon_release_moves_to_named_helper_and_simulation_kernel_systems_stays_inline_free
$env:PYTHONPATH='build-local-win'; python -m pytest -q tests/runtime/engagement/test_live_engagement_event_capture.py
```

## Validation Outcome

`2026-06-02` TM06-C accepted:

- `git diff --check`: pass, with LF/CRLF working-copy warnings only.
- `cmake --build build-local-win --target ef_py -j2`: pass.
- Focused structural guard: `1 passed`.
- Engagement runtime event capture suite: `7 passed`.

## Acceptance Criteria

- `simulation_kernel_damage_debug_api.cpp` keeps public debug methods as wrappers
  around local helper-owned DTO construction.
- `EngagementEffectsDamageEventRecord` remains the only event record passed to
  the engagement store from debug damage paths.
- Impact entities are still destroyed after effects recording.
- Focused guards and runtime engagement tests pass.

## Residual Map

Held:

- Public debug API retirement.
- Broader damage-model redesign.
- Broader `SimulationKernel` decomposition.
