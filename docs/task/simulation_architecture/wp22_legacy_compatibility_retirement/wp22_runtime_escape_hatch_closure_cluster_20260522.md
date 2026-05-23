# WP22-C Runtime Escape-Hatch And Legacy Mode Closure

Status: `2026-05-22` latest implementation wave locally accepted for
`RTE-003` final production raw-loader cleanup, main-thread `A-001` maintained
typed setup promotion, `RTE-005` silent selection removal, and `RTE-007`
setup/type/schema ownership. R3 must be re-scoped before more implementation
or closure dispatch. Runtime escape hatches are still not fully retired:
`RuntimeFacade::runtime()` / `WorldBatchRuntime::world()`,
`vec_env.batch_runtime`, diagnostics bindings, explicit `legacy` mode, and
fallback cadence remain only as named compatibility/diagnostics surfaces until
replacement APIs exist. The latest GPU visual binding slice also removed direct
`bindings_gpu.cpp` raw-world drilling by routing scene collection through a
named `WorldBatchRuntime` compatibility helper. `L-002` is therefore a scoped
pass for maintained facade internals and the direct GPU binding residual,
while public raw escape hatches remain quarantined and still block WP22
closure.

Preflight note: this is guard hardening only, not acceptance. The repo-level
maintained Python scan now also covers non-test entrypoints, and `train.py`
plus `tools/diagnostics/benchmarks/world_batch_vec_env.py` stay on the explicit
compatibility/diagnostics allowlist rather than being retired.
Beauvoir's preflight packet was accepted only as guard hardening:
`batch_runtime` consumers outside the explicit non-test compatibility/
diagnostics allowlist now fail architecture tests, but `WP22-F` remains not
eligible because public runtime/world escape hatches and diagnostics bindings
are still live.

Inputs:

- [WP22 main plan](legacy_compatibility_retirement_wp22_20260522.md)
- [WP22-A fact ledger](wp22_retirement_fact_ledger_cluster_20260522.md)

## Verification Scope

This pass re-checked `RTE-001` through `RTE-007` and `L-002` against the current tree. The result is still a forced-retirement audit, not a compatibility pass: every surviving raw runtime, raw loader, or silent `legacy` path remains either `quarantine`, `migrate`, or `blocker`.

## Source-Verified Findings

| Ledger item | Current fact | Classification | Source anchors | Repro command |
|---|---|---|---|---|
| `RTE-001` | `RuntimeFacade::runtime()` is still a live raw escape hatch. The C++ facade still returns `WorldBatchRuntime&`, the adapter still caches that raw runtime, and allowlist-based architecture tests still exist because the surface is not retired. | `quarantine` | `src/runtime/facade/runtime_facade.cpp:2360-2365`; `python/rl/runtime/world_batch/adapter.py:47-50`; `tests/architecture/test_runtime_facade_layering.py:379-394` | `rg -n "RuntimeFacade::runtime\\(|\\.runtime\\(" src python tests -S` |
| `RTE-002` | `vec_env.batch_runtime` is still a public compatibility view. The property remains exposed in maintained runtime code, the leader runtime group forwards it, and tests explicitly assert the compatibility view is present. Diagnostics bindings remain compatibility/diagnostics surfaces until replacement APIs exist. | `quarantine` | `python/rl/runtime/world_batch_vec_env.py:280-286`; `python/rl/runtime/leader_world_batch_runtime.py:204-206`; `tests/world_batch/test_world_batch_vec_env.py:457-473`; `tests/architecture/test_runtime_facade_layering.py:360-376` | `rg -n "batch_runtime" python/rl/runtime tests/world_batch tests/architecture -S` |
| `RTE-003` | Production `loader.sim.*` / `loader.sim,` usage is now empty. Maintained runtime reward/info, tasking command writes, time-step reads, naval-screen unit reads, scripted-opponent kernel access, runtime-state, and loading paths route through named loader-owned seams or typed helpers. | `pass for production raw-loader cleanup` | `python/rl/tasking/bridge.py`; `python/rl/tasking/leader_tasking.py`; `gym_envs/scenario_loader/runtime_state.py`; `gym_envs/scenario_loader/loading.py`; `tests/architecture/test_runtime_facade_layering.py`; `tests/architecture/test_wp22_tasking_bridge_retirement.py` | `rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> no matches |
| `RTE-004` | `execution_step_runtime_mode="legacy"` remains accepted only as an explicit compatibility opt-in. Env config and batch envs reject `legacy` unless `runtime_compatibility_enabled=True`, and maintained setup favors `compiled`. | `quarantine / explicit opt-in` | `python/env_config.py:130-134`; `python/rl/runtime/world_batch_vec_env.py:151-156`; `python/rl/runtime/cooperative_world_batch_vec_env.py:146-150`; `tests/runtime/core/test_env_config.py`; `tests/world_batch/test_world_batch_vec_env.py` | `python -m pytest -q tests/runtime/core/test_env_config.py tests/world_batch/test_world_batch_vec_env.py -k "execution_step_runtime_mode or runtime_compatibility"` |
| `RTE-005` | Silent runtime-mode selection is removed. `normalize_execution_step_runtime_mode(None)` resolves to `compiled`, loader init calls `set_execution_step_runtime_mode("compiled")`, and the production/test scan finds no `CMO_EXECUTION_STEP_RUNTIME` or `set_execution_step_runtime_mode(None)` anchors. | `pass for silent-selection removal` | `gym_envs/scenario_loader/common.py:124-132`; `gym_envs/scenario_loader/core.py:262-267`; `python/env_config.py:130-134`; `tests/runtime/core/test_env_config.py` | `rg -n "CMO_EXECUTION_STEP_RUNTIME|set_execution_step_runtime_mode\\(None\\)" gym_envs python tests -S` -> no matches |
| `RTE-006` | `compatibility_fallback_world_batch_step_worlds_wp16c` is still retained as a named fallback cadence path and guarded by compatibility tests. It is not a maintained default. | `quarantine / explicit fallback` | `python/rl/runtime/single_world_batch_runtime.py:255`; `python/rl/runtime/leader_world_batch_runtime.py:278`; `tests/world_batch/test_single_world_batch_runtime.py:211`; `tests/world_batch/test_single_world_batch_runtime.py:420` | `rg -n "compatibility_fallback_world_batch_step_worlds_wp16c" python tests -S` |
| `RTE-007` | Terrain source, compiler metadata, runtime apply, world-batch setup, and facade setup now share explicit non-legacy default ownership. Missing/blank terrain resolves to `flat` with `default_mainline`; explicit legacy terrain is labelled `explicit_legacy_compatibility`. | `pass for setup/type/schema slice` | `python/scenario/compiler/common.py`; `python/scenario/compiler/layout_template.py`; `python/scenario/runtime/kernel_apply.py`; `python/scenario/runtime/world_setup_compat.py`; `src/core/engine/world_batch_runtime.cpp`; `tests/runtime/core/test_world_setup_compat.py`; `tests/runtime/facade/test_runtime_facade.py`; `tests/world_batch/test_world_batch_runtime.py`; `tests/scenario/test_scenario_compiler.py` | `cmake --build build-workshop --target ef_py -j4 && bash tools/maintenance/cmo_env.sh python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "terrain or world_setup or setup"` |
| `L-002` | Raw batch/world access remains public, but the maintained facade and direct GPU binding residual are now narrowed. `WorldBatchRuntime::world()` and `RuntimeFacade::runtime()` remain public compatibility/diagnostics escape hatches; `bindings_gpu.cpp` no longer calls `.world(` and now consumes `collect_visual_binding_compatibility_scenes_batch(...)`, whose raw scene collection is centralized inside `WorldBatchRuntime`. Diagnostics bindings remain compatibility/diagnostics surfaces until replacement APIs exist. The old `runtime_facade.cpp:592` anchor is maintained typed setup evidence, not raw drilling. | `quarantine / scoped pass for maintained facade and direct binding residual` | `src/core/engine/world_batch_runtime.h:65-68`; `src/core/engine/world_batch_runtime.cpp:337-342`; `src/runtime/facade/runtime_facade.cpp:2498-2503`; `src/interfaces/python/bindings_gpu.cpp:520-527`; `src/core/engine/world_batch_runtime.cpp:1105-1130`; `tests/architecture/test_runtime_facade_layering.py:599-626` | `rg -n "RuntimeFacade::runtime\\(|WorldBatchRuntime::world\\(|collect_visual_binding_compatibility_scenes_batch|\\.world\\(" src python tests -S` |

## Implementation Dispatch Readiness

| Scope | Ready now? | Why |
|---|---|---|
| `RTE-001` | `yes` | Guard tightening and compatibility-module quarantine can start from already verified escape-hatch locations. |
| `RTE-002` | `yes` | Public `batch_runtime` can be fenced with explicit compatibility naming and allowlist guard work without waiting on other packages. |
| `RTE-004` | `guard follow-up only` | Explicit compatibility opt-in is now enforced; remaining work is guard coverage and avoiding new default-legacy callers. |
| `RTE-005` | `complete for silent-selection slice` | Env-silent selection and `None` setter anchors are gone from the scanned production/test scope. |
| `RTE-006` | `guard follow-up only` | Compatibility fallback remains named and test-visible; do not promote it to maintained default. |
| `RTE-003` | `complete for production raw-loader cleanup` | The latest wave removed the final production `loader.sim.*` / `loader.sim,` anchors from `gym_envs` and `python/rl`. |
| `RTE-007` | `complete for setup/type/schema slice` | Source, rebuilt binding, compiler metadata, runtime apply, facade setup, and world-batch setup now agree on the non-legacy default and explicit legacy compatibility labels. |
| `L-002` | `guard follow-up / service split` | Maintained facade raw drilling and direct GPU binding raw-world use are closed for their scoped slices. Public `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` escape hatches and diagnostics bindings still require guard discipline and later service-boundary narrowing. |

## Required Runtime-Closure Direction

- `migrate`: `RTE-007` source, binding, setup, type, and schema ownership now
  prove the default is `flat`; remaining explicit `legacy` schema values are
  compatibility consumers, not maintained defaults.
- `migrate / pass`: `RTE-003` production raw-loader cleanup and `RTE-005`
  silent-selection removal are locally accepted for their scoped runtime lanes.
- `quarantine`: `RTE-001`, `RTE-002`, `RTE-004`, and `RTE-006` can stay only as
  named compatibility surfaces with guard-tested allowlists.
- `quarantine`: `L-002` is a scoped pass for maintained facade internals and
  direct GPU binding raw-world drilling, but the public C++ facade/world raw
  accessors and diagnostics bindings remain compatibility/diagnostics escape
  hatches and cannot be treated as closure until they are narrowed or guarded
  as explicit opt-ins.

## Current Implementation Wave Snapshot

| Field | Value |
|---|---|
| `status` | `partial overall`: `RTE-003`, `A-001`, `RTE-005`, `RTE-007`, and the direct GPU visual binding raw-world slice passed; `RTE-001`, `RTE-002`, `RTE-004`, `RTE-006`, and public `L-002` escape-hatch quarantine remain compatibility/guard work. |
| `commands run` | `git diff --check` -> pass; `cmake --build build-workshop --target ef_py -j4` -> pass in worker packet; `rg -n "loader\\.sim\\.|loader\\.sim," gym_envs python/rl -S` -> no matches; `tests/architecture/test_runtime_facade_layering.py` focused runtime guards -> `8 + 4` passed across the accepted packets; `tests/architecture/test_wp22_tasking_bridge_retirement.py` -> `7` passed; env/world-batch fallback tests -> `6 + 3 + 8` passed. |
| `remaining blockers` | Public `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` compatibility access remains; explicit compatibility surfaces for `batch_runtime`, `legacy`, fallback cadence, and diagnostics bindings still require guard discipline. The direct `bindings_gpu.cpp` raw-world residual is now quarantined behind `WorldBatchRuntime::collect_visual_binding_compatibility_scenes_batch(...)`. R3 must be re-scoped before more implementation or closure dispatch. |
| `integration notes` | Dispatch C++ raw facade/world narrowing separately from command/setup and structural decomposition. Do not create acceptance until these and the structural/command blockers are closed or explicitly guarded. |

## First-Wave Implementation Snapshot

This snapshot is historical. It is retained to show why the later Russell and
Bernoulli packets were needed; the current state is the table above.

| Field | Value |
|---|---|
| `status` | `partial` |
| `commands run` | `git diff --check` -> pass; `python -m pytest -q tests/architecture/test_runtime_facade_layering.py -k "runtime_facade_runtime_consumers or leader_world_batch_runtime_does_not_call_runtime_facade_runtime or batch_runtime"` -> collection-limited by missing `ef_py.ConditionalObjectiveProperty`; focused runtime opt-in/quarantine tests pass; focused env/world_batch tests `2+3+2` pass |
| `remaining blockers` | Superseded by the current snapshot: `RTE-003` production raw-loader cleanup and `RTE-007` setup/type/schema ownership have since passed; `L-002` remains open. |
| `integration notes` | Keep quarantine allowlists explicit and do not describe escape hatches as retired; do not reintroduce production `loader.sim` anchors. |

## Return Packet

This packet is the earlier documentation verification packet. It is superseded
for `RTE-003`, `RTE-005`, and `RTE-007` by the current implementation wave, but
still explains why `L-002` remains open.

### Verification Notes

| Field | Value |
|---|---|
| `status` | `partial` |
| `touched files` | `docs/task/simulation_architecture/wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.md`; `docs/task/simulation_architecture/wp22_legacy_compatibility_retirement/wp22_runtime_escape_hatch_closure_cluster_20260522.zh.md` |
| `commands run` | Historical packet: earlier scans found live runtime escape hatches and compatibility surfaces. Current verification supersedes this for `loader.sim`, `CMO_EXECUTION_STEP_RUNTIME`, `set_execution_step_runtime_mode(None)`, and terrain setup. |
| `remaining blockers` | Current closure blocker is the public compatibility surface: raw facade/world access cannot be fully closed until replacement APIs or explicit quarantine guards exist. The former direct GPU binding residual has moved behind the named `WorldBatchRuntime` compatibility helper. |
| `integration notes` | Do not treat compatibility residuals as pass. Runtime quarantine work may proceed only on the ready subset, and any implementation stream must preserve explicit allowlists without reintroducing production `loader.sim` anchors. |
| `WP22-C implementation dispatch allowed?` | `no` for now; R3 must be re-scoped before more implementation or closure dispatch. Public `RuntimeFacade::runtime()` / `WorldBatchRuntime::world()` access plus `RTE-001`, `RTE-002`, `RTE-004`, `RTE-006`, and diagnostics bindings remain compatibility/diagnostics work, and the completed direct GPU binding residual must not be reopened. |

## Stop Rules

- Do not describe `RuntimeFacade.runtime()`, `batch_runtime`, `vec_env.batch_runtime`, or diagnostics bindings as retired while raw C++ access and compatibility views are still live.
- Do not call `legacy` mode acceptable for maintained paths; it is an explicit compatibility opt-in only.
- Do not reintroduce production `loader.sim.*` / `loader.sim,` anchors in `gym_envs` or `python/rl`.
