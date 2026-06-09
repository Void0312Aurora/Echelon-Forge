# WP18-F Integration And Handoff

状态：`2026-05-21` complete / accepted。

语言版本：

- 英文主文：[wp18_integration_handoff_cluster_20260521.md](wp18_integration_handoff_cluster_20260521.md)
- 中文辅文：`wp18_integration_handoff_cluster_20260521.zh.md`

输入：

- [WP18 主计划](runtime_ownership_cxx_hot_path_consolidation_wp18_20260521.zh.md)
- [WP18 dispatch queue](wp18_subagent_dispatch_queue_20260521.zh.md)
- [WP Closure Lane Policy](../../../standards/governance/wp_closure_lane_policy.md)

## 目标

在 WP18-A 到 WP18-E 回收后，负责串行 integration lane。本流不实现主要 runtime
slices，而是验证集成、记录 residuals、同步索引，并且只在实现证据存在后创建验收审查。

## 范围

范围内：

- 收集 worker return packets，并协调互相冲突的 residuals；
- 运行聚焦验证和 closure validation；
- 更新 WP18 docs、README entries、review indexes 与中文辅文；
- 只有 implementation gates 通过后才创建 acceptance review；
- 将 residuals 路由到 WP19/WP20/WP21，避免开启额外阶段。

范围外：

- workers 活跃时并行编辑同一张规范性表；
- 把 planned docs 当作 implementation evidence 验收；
- broad runtime refactors。

## 任务项

| ID | 项目 | 验收 |
|----|------|------|
| `F1` | Worker result rollup | 汇总 A-E statuses、touched files、commands、blockers 与 residuals。 |
| `F2` | Validation rollup | 记录精确 commands 与 outcomes。 |
| `F3` | Residual routing | 将 remaining blockers 分配到 WP19、WP20、WP21 或 retained compatibility。 |
| `F4` | Closure docs | 同步 README/review/bilingual docs，并且只在 gates 通过后创建 acceptance review。 |

## 建议验证

```bash
git diff --check
python3 tools/maintenance/wp_doc_closure_audit.py --wp WP18
python -m pytest -q tests/architecture/runtime_facade/test_layering.py
python -m pytest -q tests/world_batch/test_world_batch_vec_env.py -k "execution_episode_controller_mainline or compatibility_view"
```

## Handoff

返回 acceptance decision、精确 validation outcomes、residual register、
documentation sync status，以及 WP19 entry conditions 是否满足。
