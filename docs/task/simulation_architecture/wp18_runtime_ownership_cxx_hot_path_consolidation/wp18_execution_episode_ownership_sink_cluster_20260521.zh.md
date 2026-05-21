# WP18-B Execution Episode Ownership Sink

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp18_execution_episode_ownership_sink_cluster_20260521.md](wp18_execution_episode_ownership_sink_cluster_20260521.md)
- 中文辅文：`wp18_execution_episode_ownership_sink_cluster_20260521.zh.md`

输入：

- [WP18 主计划](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18-A ownership fact ledger](wp18_ownership_fact_ledger_hot_path_map_cluster_20260521.zh.md)
- [WP17 facade business migration](../wp17_stage3_runtime_materialization_cleanup/wp17_facade_business_migration_cleanup_cluster_20260521.zh.md)

## 目标

把一个 maintained execution-episode state/export/consume slice 收到 C++/facade-owned
results 后面，让 Python wrapper 不再充当该 slice 的 authoritative runtime owner。

## 范围

范围内：

- 从 WP18-A 选出的一个窄 execution-episode ownership slice；
- 暴露 C++/runtime-owned state/results 的 facade 或 adapter methods；
- 聚焦测试证明 selected maintained caller 不再需要 raw compatibility world reads；
- 保持既有 batch/runtime compatibility tests 通过。

范围外：

- 完整 VecEnv rewrite；
- 删除 `WorldBatchRuntime`、`batch_runtime` 或 `RuntimeFacade.runtime()`；
- 拆分 `ScenarioLoader` 结构；该项由 WP18-C 拥有。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `B1` | Select first ownership slice | 选定 slice 具备 source/test anchors、有限写入范围与直接业务价值。 |
| `B2` | Facade/runtime-owned export | Maintained caller 可通过 facade-shaped runtime evidence 接收 state/result。 |
| `B3` | Python mirror demotion | Python path 对该 slice 只是 mirror 或 consumer，不是 authoritative owner。 |
| `B4` | Compatibility proof | 既有 compatibility tests 仍通过，direct raw reads 保持显式分类。 |

## 建议验证

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade.py -k "execution or episode or batch"
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
python -m pytest -q tests/world_batch/test_world_batch_runtime.py -k "execution_episode"
```

## Handoff

返回 selected slice、touched files、新 facade/runtime evidence、retained
compatibility paths、commands run、blockers，以及仍留在 Python 的 residual ownership。
