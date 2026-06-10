# WP17-B Facade Business Migration And Compatibility Cleanup

状态：`2026-05-21` implemented / focused validation passed。

英文主文：[wp17_facade_business_migration_cleanup_cluster_20260521.md](wp17_facade_business_migration_cleanup_cluster_20260521.md)

输入：

- [WP17 主计划](stage3_runtime_materialization_cleanup_wp17_20260521.zh.md)
- [WP16 facade/batch migration](../wp16_runtime_spine_consolidation/wp16_facade_batch_spine_migration_cluster_20260521.zh.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.md)

## 目标

在不删除兼容 API 的前提下压缩旧业务访问路径。直接目标是把仍通过 `vec_env.batch_runtime` 读取 runtime state 的 maintained training/batch code 和测试，迁移到 facade-shaped adapter 或 env methods。

## 范围

范围内：

- 按需添加或暴露 `WorldBatchVecEnv` facade-shaped 方法，用于 execution episode readiness 与 state export；
- 将 maintained tests 与业务面对的 call sites 从 direct `batch_runtime` reads 迁出；
- 保留 `batch_runtime` 作为明确 compatibility view；
- 扩展 architecture guards，使 direct `batch_runtime` reads 只允许出现在命名 compatibility tests 或 adapters 中。

范围外：

- 删除 `WorldBatchRuntime`、`RuntimeFacade.runtime()` 或 `batch_runtime`；
- 修改 scenario schemas；
- scheduler、fidelity、capability 或 counterfactual 实现。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `B1` | Facade-shaped env accessors | Maintained env callers 可在不直接访问 `batch_runtime` 的情况下查询 execution readiness/state。 |
| `B2` | Business/test migration | Mainline tests 使用 env/adapter facade methods；compatibility test 保持显式。 |
| `B3` | Guard tightening | Architecture guard 防止新增 mainline `batch_runtime.export_execution_episode_states_batch` 与 `execution_episode_controller_ready` reads。 |
| `B4` | Compatibility proof | 兼容 view 测试仍通过，并记录保留的 legacy 行为。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/architecture/runtime_facade
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
python -m pytest -q tests/world_batch/test_single_world_batch_runtime.py
```

## 交接

返回 migrated call sites、retained compatibility paths、guard changes、commands run 与 residual legacy accesses。
