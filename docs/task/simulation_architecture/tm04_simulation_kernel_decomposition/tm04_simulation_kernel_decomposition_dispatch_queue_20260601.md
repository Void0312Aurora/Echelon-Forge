# TM04 SimulationKernel Decomposition Dispatch Queue

Status: `2026-06-01` active dispatch queue for
[TM04 SimulationKernel Decomposition](README.md).

This queue is subordinate to
[tm04_simulation_kernel_decomposition_task_clusters_20260601.md](tm04_simulation_kernel_decomposition_task_clusters_20260601.md).
It is not implementation evidence.

## Round 1 Dispatch

Issued on `2026-06-01`:

| Dispatch | Cluster | Agent | Role | Status | Write scope |
| --- | --- | --- | --- | --- | --- |
| `TM04-C1 release service migration` | `TM04-C` | `019e83cf-8961-78e3-9610-25ad528a5f75` / Laplace | implementation worker | pass | Release-service files, bounded kernel/weapon API edits, CMake source registration, focused tests only. |
| `TM04-D1 effects DTO diagnostics` | `TM04-D` | `019e83cf-b3ef-7a32-8739-15edb6c5c7ba` / Bacon | read-only diagnostics worker | pass | No writes; mapped DTO call paths and legacy overload blockers. |
| `TM04-E1 naval damage bridge diagnostics` | `TM04-E` | `019e83cf-df72-7140-93e8-daf565b0f35a` / Jason | read-only diagnostics worker | pass | No writes; mapped naval deck-gun/CIWS damage coupling and bridge needs. |

Round 1 opened only one implementation write scope. The DTO and damage-bridge
agents remained read-only because both could collide with
`simulation_kernel_weapon_api.cpp` if turned into implementation work too early.

## Queue

| Dispatch | Cluster | Owner type | Model / reasoning | Write scope | Parallel-safe | Expected packet |
| --- | --- | --- | --- | --- | --- | --- |
| `TM04-A1 docs setup` | `TM04-A` | main thread | inherited / xhigh | TM04 docs and parent simulation-architecture indexes only | No; creates the normative task surface. | `status`, touched files, docs validation, remaining risks. |
| `TM04-C1 release service migration` | `TM04-C` | implementation worker | inherited / xhigh | `simulation_kernel_services.*`, candidate release-service files, `simulation_kernel_weapon_api.cpp`, `simulation_kernel.h`, `CMakeLists.txt`, focused release tests | Partly; do not run concurrently with any worker editing the same weapon API slice. | `status`, explicit dependency list, behavior risks, commands/outcomes, remaining kernel wrappers. |
| `TM04-D1 effects DTO migration` | `TM04-D` | implementation worker | inherited / xhigh | `engagement_event_recorder.h`, event store files, damage debug API, weapon API DTO call sites, focused tests | Only if weapon API edits are serialized against `TM04-C1`. | `status`, DTO call-site map, legacy overload decision, commands/outcomes, behavior risks. |
| `TM04-E1 damage bridge decision` | `TM04-E` | implementation or diagnostics worker | inherited / xhigh | Candidate narrow interface and release/damage bridge files only after source facts are known | No with `TM04-C1` if changing release damage paths. | `status`, selected bridge or blocked residual, touched files, validation gap. |
| `TM04-F1 validation` | `TM04-F` | integration worker | inherited / xhigh | Validation docs and any minimal test/build fixes within TM04 scope | No; serial after implementation. | Pass/block validation matrix with exact commands and blockers. |
| `TM04-G1 closeout` | `TM04-G` | integration/docs worker | inherited / xhigh | TM04 docs, parent indexes, archive README | No; final status lines are serial. | Accepted/blocked/held closeout and residual map. |

## Dispatch Guardrails

- Dispatch one implementation worker per shared C++ write surface.
- Pass `reasoning_effort: xhigh` to subagents for TM04 work.
- Tell workers they are not alone in the worktree and must not revert edits they
  did not make.
- Require workers to return the standard worker packet from the task-cluster
  document.
- Do not use this queue to add new waves after a round cap is reached; re-scope
  the cluster first.
