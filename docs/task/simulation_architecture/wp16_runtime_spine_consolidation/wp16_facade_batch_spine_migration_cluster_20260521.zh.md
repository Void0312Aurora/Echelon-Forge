# WP16-C Facade And Batch Path Spine Migration

状态：`2026-05-21` complete / facade and batch migration accepted。

语言版本：

- 英文主文：[wp16_facade_batch_spine_migration_cluster_20260521.md](wp16_facade_batch_spine_migration_cluster_20260521.md)
- 中文辅文：`wp16_facade_batch_spine_migration_cluster_20260521.zh.md`

输入：

- [WP16 runtime spine consolidation](runtime_spine_consolidation_wp16_20260521.zh.md)
- [WP7.5 training path facade bridge](../wp75_training_path_facade_bridge/training_path_facade_bridge_wp75_20260520.zh.md)
- [WP10 causal runtime foundation](../wp10_causal_runtime_foundation/causal_runtime_foundation_wp10_20260520.zh.md)
- [WP11 facade vertical slice and provenance](../wp11_facade_vertical_slice_provenance/facade_vertical_slice_provenance_wp11_20260520.zh.md)
- [WP15 counterfactual experiment generation](../wp15_counterfactual_experiment_generation/counterfactual_experiment_generation_wp15_20260521.zh.md)

## 1. 目标

`WP16-C` 把 maintained consumers 迁向 runtime spine。关键目标不是 API churn，
而是让 facade、world-batch、training、scenario 与 experiment consumers 获得同一套
barrier/event/provenance/cadence evidence，而不是继续穿透 raw runtime 或 private state。

## 2. 范围

范围内：

- 把选定 maintained facade 或 batch calls 迁到 runtime-window spine；
- caller 暂时不能安全迁移时，保留 compatibility wrappers；
- 确保 observation/facade exports 保留 consumer 所需 provenance、authority、
  capability、backend/fidelity、replay 与 cadence evidence；
- 触及 public surfaces 时更新 Python adapter 或 binding-facing tests；
- 记录必须继续 compatibility-only 的 fallback paths。

范围外：

- 全局删除 raw runtime access；
- 大范围改变 scenario schemas；
- 晋升 public experiment orchestration；
- 实现 WP16-B 负责的 clock-domain enforcement。

## 3. 交付物

- 一条迁移后的 maintained path，或包裹 runtime-window spine 的 wrapper。
- 测试证明 migrated consumer 能看到 barrier/event/provenance/cadence evidence。
- 无法在本切片迁移 caller 的 compatibility fallback records。
- 给 WP16-D 的 notes，说明哪些 legacy paths 可弃用或应保留。

## 4. Gate 规则

| Gate item | Pass condition |
|-----------|----------------|
| Maintained consumer | 至少一条 selected facade/batch/training consumer 使用 spine 或显式 wrapper。 |
| Evidence continuity | consumer-visible data 按需携带 barrier、event、provenance、authority、capability、backend/fidelity、replay 或 cadence evidence。 |
| Compatibility | 既有 maintained tests 继续通过，或 fallback behavior 被显式文档化并测试。 |
| No raw-state regression | 迁移路径不重新获得 raw runtime 或 direct ECS ownership。 |

## 5. 建议验证

```bash
git diff --check
python -m pytest -q tests/runtime/facade/test_runtime_facade_window_loop_injection.py
python -m pytest -q tests/world_batch/test_world_batch_runtime.py tests/runtime/execution/test_execution_episode_batch_prepare.py -k "facade or window or evidence or batch"
```

## 6. 交接契约

返回：

- touched files；
- migrated consumer paths；
- compatibility fallback paths；
- 精确验证命令和结果；
- residual raw/bypass access；
- 给 WP16-D 与 WP16-F 的 notes。
