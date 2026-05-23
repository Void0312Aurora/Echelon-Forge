# WP18-A Ownership Fact Ledger And Hot-Path Map

Status: `2026-05-21` verified / authoritative evidence ledger.

Language:

- English canonical: `wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md`
- Chinese companion: [wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)

Evidence window:

- Source inspection: `python/rl/runtime/world_batch/adapter.py:44`, `python/rl/runtime/world_batch_vec_env.py:89`, `gym_envs/scenario_loader/core.py:171`, `src/core/mission/runtime/*`, `src/core/mission/episode/*`
- Test inspection: `tests/architecture/test_runtime_facade_layering.py:155`, `tests/runtime/execution/test_execution_episode_controller.py:232`, `tests/runtime/execution/test_execution_episode_batch_prepare.py:293`, `tests/world_batch/test_world_batch_vec_env.py:275`, `tests/world_batch/test_world_batch_runtime.py:1014`

## Classification Legend

- `maintained owner`: the current source of truth for maintained runtime state or hot-path math.
- `compatibility mirror`: tolerated raw runtime/world access kept only for compatibility while callers migrate.
- `frontend helper`: Python orchestration and adapter code that shapes requests and scenario data but should not own maintained execution truths.
- `blocked/unknown`: surfaces that are intentionally guarded or not yet proven safe for promotion.

## Ownership Ledger

| Surface | Current code fact | Classification | Evidence |
|---|---|---|---|
| `src/core/mission/episode/execution_episode_controller.*` | Canonical episode-state import/export, runtime-input preparation, step, and step-result application are already in C++. | maintained owner | `src/core/mission/episode/execution_episode_controller.h:20`, `src/core/mission/episode/execution_episode_controller.cpp:34`, `tests/runtime/execution/test_execution_episode_controller.py:232` |
| `src/core/mission/runtime/*` | Reward, termination, mission-observation, step-info, and episode-level batch aggregation are compiled runtime assets. | maintained owner | `src/core/mission/runtime/execution_episode_runtime.cpp:127`, `src/core/mission/runtime/execution_step_runtime.cpp:16`, `src/core/mission/runtime/mission_runtime.cpp:170`, `src/core/mission/runtime/termination_runtime.cpp:14`, `src/core/mission/runtime/reward_runtime.cpp:32` |
| `gym_envs/scenario_loader/core.py` | `ScenarioLoader` still acts as both scenario adapter and runtime-state mirror via state-shell ownership and runtime-step helpers. | frontend helper + runtime mirror | `gym_envs/scenario_loader/core.py:171`, `gym_envs/scenario_loader/core.py:176`, `gym_envs/scenario_loader/core.py:284`, `gym_envs/scenario_loader/core.py:1140`, `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py:251` |
| `python/rl/runtime/world_batch/adapter.py` and `python/rl/runtime/world_batch_vec_env.py` | The maintained Python frontend still builds and consumes request state, but keeps raw runtime/world access inside the compatibility adapter and `batch_runtime` surface. | compatibility mirror + frontend helper | `python/rl/runtime/world_batch/adapter.py:44`, `python/rl/runtime/world_batch/adapter.py:49`, `python/rl/runtime/world_batch/adapter.py:203`, `python/rl/runtime/world_batch_vec_env.py:89`, `python/rl/runtime/world_batch_vec_env.py:281`, `tests/architecture/test_runtime_facade_layering.py:155`, `tests/world_batch/test_world_batch_vec_env.py:275` |
| Raw runtime/world-handle reads outside the adapter allowlist | The architecture guard keeps new maintained raw runtime reads out of the codebase unless they are explicitly allowlisted. | blocked/unknown | `tests/architecture/test_runtime_facade_layering.py:29`, `tests/architecture/test_runtime_facade_layering.py:122`, `tests/architecture/test_runtime_facade_layering.py:228` |

## Python Hot-Path Inventory

| Path | Current hot-path role | Complexity | Test anchors | Why it matters |
|---|---|---|---|---|
| `python/rl/runtime/world_batch_vec_env.py` | Reset/step mainline, shadow compare, mainline consume, and request build/consume loops. | high | `tests/world_batch/test_world_batch_vec_env.py:275`, `tests/world_batch/test_world_batch_vec_env.py:834`, `tests/world_batch/test_world_batch_vec_env.py:918`, `tests/architecture/test_runtime_facade_layering.py:206` | It still assembles requests and consumes loader mirrors in Python, so it remains a hot-path frontend rather than an owner. |
| `python/rl/runtime/world_batch/adapter.py` | Facade bootstrap, observation packet export, and compatibility world fallback. | medium-high | `tests/architecture/test_runtime_facade_layering.py:155`, `tests/world_batch/test_world_batch_vec_env.py:275` | This is the one tolerated compatibility escape hatch; it must stay narrow. |
| `gym_envs/scenario_loader/core.py` | State shell, load/apply execution-episode state, mission observation, and `compute_full_step`. | high | `tests/runtime/execution/test_execution_episode_controller.py:352`, `tests/runtime/execution/test_execution_episode_controller.py:389`, `tests/runtime/execution/test_execution_episode_controller.py:460`, `tests/runtime/execution/test_execution_episode_controller.py:542`, `tests/runtime/execution/test_execution_episode_controller.py:637`, `tests/runtime/execution/test_execution_episode_controller.py:749`, `tests/runtime/execution/test_scenario_loader_execution_step_runtime.py:251`, `tests/world_batch/test_world_batch_runtime.py:1014` | This is still a high-frequency runtime mirror and the biggest Python ownership risk. |
| `src/core/mission/episode/execution_episode_controller.cpp` + `src/core/mission/episode/execution_episode_batch_prepare.cpp` | Canonical C++ episode-state sink and batch-input materialization seam. | high | `tests/runtime/execution/test_execution_episode_controller.py:232`, `tests/runtime/execution/test_execution_episode_batch_prepare.py:293`, `tests/runtime/execution/test_execution_episode_batch_prepare.py:368` | This is the safest first ownership sink because the maintained C++ state path already exists. |
| `src/core/mission/runtime/*` | Compiled reward, termination, mission-observation, and step math. | high | `tests/runtime/execution/test_execution_step_runtime.py:28`, `tests/runtime/execution/test_execution_episode_batch_prepare.py:293` | These are the reusable C++ hot-path assets that should be consumed before any new DTO layer is invented. |

## C++ Asset Inventory

| Asset group | What it owns today | Evidence |
|---|---|---|
| `src/core/mission/runtime/*` | Episode-level runtime aggregation, step info, mission observation, reward, and termination math. | `src/core/mission/runtime/execution_episode_runtime.h:8`, `src/core/mission/runtime/execution_episode_runtime.cpp:127`, `src/core/mission/runtime/mission_runtime.h:7`, `src/core/mission/runtime/reward_runtime.h:32`, `src/core/mission/runtime/termination_runtime.h:14` |
| `src/core/mission/episode/execution_episode_state.*` and `execution_episode_controller.*` | Canonical episode state plus import/export, state equivalence, and step-result application. | `src/core/mission/episode/execution_episode_state.h:10`, `src/core/mission/episode/execution_episode_state.cpp:64`, `src/core/mission/episode/execution_episode_controller.h:20`, `src/core/mission/episode/execution_episode_controller.cpp:34`, `src/core/mission/episode/execution_episode_controller.cpp:171` |
| `src/core/mission/episode/execution_episode_batch_prepare.*` | Batch env-state to runtime-input materialization, including rich-input overrides and episode-state fallback. | `src/core/mission/episode/execution_episode_batch_prepare.h:13`, `src/core/mission/episode/execution_episode_batch_prepare.cpp:40`, `src/core/mission/episode/execution_episode_batch_prepare.cpp:315` |
| `src/core/mission/episode/detail/*` | Route guidance, post-waypoint transition activation, landing-vector adjustment, and reward telemetry. | `src/core/mission/episode/detail/episode_transition_runtime.cpp:61`, `src/core/mission/episode/detail/episode_transition_runtime.cpp:251`, `src/core/mission/episode/detail/episode_reward_breakdown.cpp:71` |

## First-Slice Recommendation

Start WP18 with the execution-episode ownership sink, not with a ScenarioLoader split or a broad VecEnv rewrite. The first slice should move the maintained episode-state import/export and step-result application behind `ExecutionEpisodeController` and the C++ runtime helpers, while `ScenarioLoader` and `WorldBatchVecEnv` stay as frontends/compatibility mirrors. That slice is the safest because the maintained C++ state path already exists, and the current tests can prove parity without changing the wider Python training loop.

## WP19 / WP21 Residuals

| Residual ID | Prerequisite | Trigger | Owner / gate | Current blocker |
|---|---|---|---|---|
| `WP19-R1` | Stable host-visible resident-state / GPU projection boundary | Before promoting resident-state or exact GPU paths | `RuntimeFacade` / core runtime | `tests/architecture/test_runtime_facade_layering.py:298` and `tests/architecture/test_runtime_facade_layering.py:325` keep GPU probing and capability projection out of maintained runtime surfaces. |
| `WP19-R2` | Python request/build/consume compatibility seams are no longer the source of truth | Before moving the hot request loop entirely to C++ | `WorldBatchVecEnv` maintainers | `python/rl/runtime/world_batch_vec_env.py:450`, `python/rl/runtime/world_batch_vec_env.py:953`, and `python/rl/runtime/world_batch_vec_env.py:1495` still build and consume loader mirrors in Python. |
| `WP21-R1` | Snapshot/restore and worldline orchestration on top of controller-owned state | Before full counterfactual experiment runtime | `RuntimeFacade` + `ExecutionEpisodeController` | Current evidence only covers controller-owned state roundtrip and selected-slice parity, not arbitrary worldline trees. |
| `WP21-R2` | Loader runtime-state mirror split or pre-gate | Before broad counterfactual / experiment runtime migration | Python runtime maintainers | `ScenarioLoader` still mixes scenario adaptation, state-shell mirroring, and runtime compute paths. |

## Validation

- `git diff --check`
- `python -m pytest -q tests/architecture/test_runtime_facade_layering.py`
