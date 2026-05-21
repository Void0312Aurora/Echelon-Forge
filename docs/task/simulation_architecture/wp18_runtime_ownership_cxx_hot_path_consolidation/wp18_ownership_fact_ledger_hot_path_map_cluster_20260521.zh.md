# WP18-A  Ownership 事实台账与 Hot-Path 地图

状态：`2026-05-21` 已核实 / authoritative evidence ledger。

语言版本：

- 英文主文：[wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.md)
- 中文辅文：`wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md`

证据窗口：

- 源码核查：`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py`、`gym_envs/scenario_loader/core.py`、`src/core/mission/runtime/*`、`src/core/mission/episode/*`
- 测试核查：`tests/architecture/test_runtime_facade_layering.py`、`tests/runtime/execution/test_execution_episode_controller.py`、`tests/runtime/execution/test_execution_episode_batch_prepare.py`、`tests/world_batch/test_world_batch_vec_env.py`、`tests/world_batch/test_world_batch_runtime.py`

## 分类标记

- `maintained owner`：维护中的 runtime 状态或 hot-path 数学的当前真值来源。
- `compatibility mirror`：为兼容而保留的 raw runtime/world 访问。
- `frontend helper`：负责请求形状与场景装配，但不应拥有维护态执行真值的 Python 前端逻辑。
- `blocked/unknown`：被显式守卫、尚未证明可提升，或暂不明确的 surface。

## Ownership 台账

| Surface | 当前事实 | 分类 | 证据 |
|---|---|---|---|
| `src/core/mission/episode/execution_episode_controller.*` | episode state 的 import/export、runtime-input 准备、step 与 step-result 应用已经在 C++ 中。 | maintained owner | `src/core/mission/episode/execution_episode_controller.h`、`src/core/mission/episode/execution_episode_controller.cpp`、`tests/runtime/execution/test_execution_episode_controller.py` |
| `src/core/mission/runtime/*` | reward、termination、mission-observation、step-info 与 episode-level batch aggregation 都是已编译 runtime 资产。 | maintained owner | `src/core/mission/runtime/execution_episode_runtime.cpp`、`src/core/mission/runtime/execution_step_runtime.cpp`、`src/core/mission/runtime/mission_runtime.cpp`、`src/core/mission/runtime/termination_runtime.cpp`、`src/core/mission/runtime/reward_runtime.cpp` |
| `gym_envs/scenario_loader/core.py` | `ScenarioLoader` 仍同时承担 scenario adapter 与 runtime-state mirror，包含 state shell 与 runtime step helper。 | frontend helper + runtime mirror | `gym_envs/scenario_loader/core.py`、`gym_envs/scenario_loader/core.py`、`gym_envs/scenario_loader/core.py`、`gym_envs/scenario_loader/core.py`、`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py` |
| `python/rl/runtime/world_batch/adapter.py` 与 `python/rl/runtime/world_batch_vec_env.py` | 维护中的 Python 前端仍在构建/消费 request state，但 raw runtime/world 访问被限制在 compatibility adapter 与 `batch_runtime` surface 内。 | compatibility mirror + frontend helper | `python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch/adapter.py`、`python/rl/runtime/world_batch_vec_env.py`、`python/rl/runtime/world_batch_vec_env.py`、`tests/architecture/test_runtime_facade_layering.py`、`tests/world_batch/test_world_batch_vec_env.py` |
| adapter 允许列表外的 raw runtime/world-handle reads | architecture guard 继续阻止新的 maintained raw runtime reads。 | blocked/unknown | `tests/architecture/test_runtime_facade_layering.py`、`tests/architecture/test_runtime_facade_layering.py`、`tests/architecture/test_runtime_facade_layering.py` |

## Python Hot-Path 清单

| Path | 热路径角色 | 复杂度 | 测试锚点 | 说明 |
|---|---|---|---|---|
| `python/rl/runtime/world_batch_vec_env.py` | reset/step 主线、shadow compare、mainline consume、request build/consume。 | 高 | `tests/world_batch/test_world_batch_vec_env.py`、`tests/architecture/test_runtime_facade_layering.py` | 仍然在 Python 中装配 request 并消费 loader mirrors，因此是前端 hot-path，而不是 owner。 |
| `python/rl/runtime/world_batch/adapter.py` | facade bootstrap、observation packet export、compatibility world fallback。 | 中高 | `tests/architecture/test_runtime_facade_layering.py`、`tests/world_batch/test_world_batch_vec_env.py` | 这是唯一被容忍的 compatibility escape hatch，必须保持很窄。 |
| `gym_envs/scenario_loader/core.py` | state shell、load/apply execution-episode state、mission observation、`compute_full_step`。 | 高 | `tests/runtime/execution/test_execution_episode_controller.py`、`tests/runtime/execution/test_scenario_loader_execution_step_runtime.py`、`tests/world_batch/test_world_batch_runtime.py` | 这是最大的 Python ownership 风险点。 |
| `src/core/mission/episode/execution_episode_controller.cpp` + `src/core/mission/episode/execution_episode_batch_prepare.cpp` | Canonical C++ episode-state sink 与 batch-input materialization seam。 | 高 | `tests/runtime/execution/test_execution_episode_controller.py`、`tests/runtime/execution/test_execution_episode_batch_prepare.py` | 最适合作为第一条 ownership sink。 |
| `src/core/mission/runtime/*` | compiled reward、termination、mission-observation、step math。 | 高 | `tests/runtime/execution/test_execution_step_runtime.py`、`tests/runtime/execution/test_execution_episode_batch_prepare.py` | 这些是应优先复用的 C++ hot-path 资产。 |

## C++ 资产清单

| 资产组 | 当前拥有内容 | 证据 |
|---|---|---|
| `src/core/mission/runtime/*` | episode-level runtime aggregation、step info、mission observation、reward、termination math。 | `src/core/mission/runtime/execution_episode_runtime.h`、`src/core/mission/runtime/execution_episode_runtime.cpp`、`src/core/mission/runtime/mission_runtime.h`、`src/core/mission/runtime/reward_runtime.h`、`src/core/mission/runtime/termination_runtime.h` |
| `src/core/mission/episode/execution_episode_state.*` 与 `execution_episode_controller.*` | canonical episode state、import/export、state equivalence、step-result application。 | `src/core/mission/episode/execution_episode_state.h`、`src/core/mission/episode/execution_episode_state.cpp`、`src/core/mission/episode/execution_episode_controller.h`、`src/core/mission/episode/execution_episode_controller.cpp` |
| `src/core/mission/episode/execution_episode_batch_prepare.*` | batch env-state -> runtime-input materialization，包含 rich-input override 与 episode-state fallback。 | `src/core/mission/episode/execution_episode_batch_prepare.h`、`src/core/mission/episode/execution_episode_batch_prepare.cpp` |
| `src/core/mission/episode/detail/*` | route guidance、post-waypoint transition、landing vector 调整与 reward telemetry。 | `src/core/mission/episode/detail/episode_transition_runtime.cpp`、`src/core/mission/episode/detail/episode_reward_breakdown.cpp` |

## First Slice 建议

WP18 的第一刀应优先做 execution-episode ownership sink，而不是先拆 `ScenarioLoader` 或大改 `VecEnv`。也就是说，先把 maintained episode-state import/export 与 step-result application 收进 `ExecutionEpisodeController` 和 C++ runtime helpers；`ScenarioLoader` 与 `WorldBatchVecEnv` 先保留为 frontend / compatibility mirror。这条路径风险最小，因为 C++ state path 已经存在，而且现有测试足以验证 parity。

## WP19 / WP21 Residuals

| Residual ID | 前置条件 | 触发点 | Owner / gate | 当前阻塞 |
|---|---|---|---|---|
| `WP19-R1` | 稳定的 host-visible resident-state / GPU projection boundary | 推进 resident-state 或 exact GPU 之前 | `RuntimeFacade` / core runtime | `tests/architecture/test_runtime_facade_layering.py` 继续禁止 GPU probing 与 capability projection 进入 maintained runtime surfaces。 |
| `WP19-R2` | Python request/build/consume 兼容缝不再是 source of truth | 将 hot request loop 整体迁入 C++ 之前 | `WorldBatchVecEnv` 维护者 | `python/rl/runtime/world_batch_vec_env.py` 仍在 Python 中 build/consume loader mirrors。 |
| `WP21-R1` | snapshot/restore 与 worldline orchestration 由 controller-owned state 支撑 | full counterfactual experiment runtime 之前 | `RuntimeFacade` + `ExecutionEpisodeController` | 当前证据只覆盖 controller-owned state roundtrip 与 selected-slice parity。 |
| `WP21-R2` | loader runtime-state mirror 已拆分或预先加闸 | broad counterfactual / experiment runtime 迁移之前 | Python runtime 维护者 | `ScenarioLoader` 仍然混合 scenario adaptation、state-shell mirroring 与 runtime compute paths。 |

## 验证

- `git diff --check`
- `python -m pytest -q tests/architecture/test_runtime_facade_layering.py`
