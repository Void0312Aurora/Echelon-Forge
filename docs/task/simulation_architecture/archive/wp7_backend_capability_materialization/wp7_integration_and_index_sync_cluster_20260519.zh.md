# WP7-E 分发单：Integration And Index Sync

状态：`2026-05-19` WP7 串行发布交接已验收。

语言版本：

- 英文主文：[wp7_integration_and_index_sync_cluster_20260519.md](wp7_integration_and_index_sync_cluster_20260519.md)
- 中文辅文：`wp7_integration_and_index_sync_cluster_20260519.zh.md`

输入：

- [WP7 后端能力物化](backend_capability_materialization_wp7_20260519.zh.md)
- [WP7-A registry materialization](wp7_registry_materialization_cluster_20260519.zh.md)
- [WP7-B runtime capability projection](wp7_runtime_capability_projection_cluster_20260519.zh.md)
- [WP7-C promotion evidence gates](wp7_promotion_evidence_gates_cluster_20260519.zh.md)
- [WP7-D multi-fidelity entry conditions](wp7_multifidelity_entry_conditions_cluster_20260519.zh.md)

## 1. 目的

WP7-E 是串行发布步骤。它应在 WP7-A 到 WP7-D 足够稳定、可以被引用后执行。
它的职责是发布一条连贯的 WP7 线，并防止旧 `WP7` 命名重新打开已验收的
WP6 policy 线。

## 2. 必需工作项

| 流 | 必需产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP7-E1 Task README Sync` | 把 WP7 产出与工作流地图加入 simulation architecture README 双语文档。 | `docs/task/simulation_architecture/README*.md`。 | 中。 |
| `WP7-E2 Architecture Relation Sync` | 把 WP7 relation note 加入 architecture README 与 strict architecture baseline。 | `docs/plan/architecture/README*.md`、架构设计双语文档。 | 中。 |
| `WP7-E3 Review Index Sync` | 只有 review 文件存在后才加入未来 WP7 acceptance review 链接；否则只在 WP7 docs 记录待评审范围。 | `docs/task/review/README*.md` 或推迟说明。 | 中。 |
| `WP7-E4 Final Handoff` | 记录最终验证命令、已评审产物与推迟事项。 | WP7 handoff 或 acceptance review。 | 中高。 |

## 3. 发布规则

1. WP7 任务线在已验收的 WP6 policy 之后启动。
2. `WP6` 仍是 backend profile policy 的名称。
3. `WP7` 是 backend capability materialization 与 multi-fidelity entry conditions 的名称。
4. 索引应引用稳定的 WP7 文档，而不是草稿碎片。
5. review index 不应在 acceptance review 文件存在前链接它们。

## 4. 非目标

- 不重写 WP6 已验收产物。
- A-D 证据存在前不创建 acceptance-review 文件。
- 初始文档创建阶段不把 WP7 标为 complete。
- 不在发布文案中晋级 candidate capability。

## 5. 验收门槛

本任务簇在以下条件满足时验收：

1. 任务 README 文件列出 WP7，并链接所有稳定 WP7 cluster docs。
2. architecture README 与 baseline relation sections 说明 WP7 是 WP6 之后的 materialization 线。
3. 没有活跃文档把 WP6 前旧 `WP7` 命名当作当前 policy 线。
4. review index 状态与实际 review 文件一致。
5. 最终验证命令已记录。

## 6. 验证命令

```bash
git diff --check
rg -n "WP7|backend_capability_materialization_wp7|wp7_registry_materialization|wp7_runtime_capability_projection|wp7_promotion_evidence|wp7_multifidelity|wp7_integration" docs/task/simulation_architecture docs/plan/architecture docs/task/review
```

## 7. 发布交接结果

WP7-E 在 WP7-A 到 WP7-D 产出稳定的实现准备笔记后完成串行发布步骤。已发布的
WP7 线现在作为文档与实现准备状态验收，而不是 capability promotion。

已验收产物：

- [WP7-A registry materialization 笔记](wp7_registry_materialization_notes_20260519.zh.md)：
  hand-maintained YAML seed shape、schema/provenance 要求、
  `maintained_status`、`projection_eligibility` 与 drift detection 计划。
- [WP7-B runtime capability projection 笔记](wp7_runtime_capability_projection_notes_20260519.zh.md)：
  从维护中 metadata 投影 `RuntimeCapabilities`，deployment facts 仅保留为
  diagnostics/availability 说明。
- [WP7-C promotion evidence gates 笔记](wp7_promotion_evidence_gates_notes_20260519.zh.md)：
  exact GPU、resident-state 与 shadow promotion gate，并映射到 WP5 evidence
  tiers 与 acceptance review。
- [WP7-D multi-fidelity entry conditions 笔记](wp7_multifidelity_entry_conditions_notes_20260519.zh.md)：
  fidelity profile request 与 entry gates，request label 不被视为 support claim。
- [WP7 后端能力物化验收审查](../review/wp7_backend_capability_materialization_acceptance_review_20260519.zh.md)：
  验收 WP7 文档/实现准备线，并保持当前 exact GPU、resident-state、shadow、
  device observation 与 multi-fidelity support 为 false。

已更新索引：

- simulation architecture README 双语文档将 WP7 标为 complete/accepted，并链接
  A-D clusters、A-D notes、WP7-E 与验收审查。
- architecture README 双语文档与 strict architecture baseline 双语文档说明
  WP7 是 WP6 之后的 materialization 计划，并链接验收审查。
- review README 双语文档列出 WP7 验收审查。

推迟事项：

1. 添加 hand-maintained WP7 registry seed。
2. 添加 seed fields、provenance、pairing、projection eligibility 与 drift
   detection 的 doc/schema tests。
3. 实现从 normalized registry metadata 投影的 runtime projection adapter。
4. 在任何 exact GPU、resident-state、shadow、device observation 或
   multi-fidelity support 字段变为 true 前，先运行未来 promotion packet。

本交接的最终验证命令：

```bash
git diff --check
rg -n "WP7|backend capability materialization|acceptance review|RuntimeCapabilities|maintained_status|projection_eligibility|multi-fidelity|promotion gate" docs/task/simulation_architecture docs/plan/architecture docs/task/review
python -m pytest tests/runtime/facade/test_runtime_facade.py tests/test_gpu_runtime_bindings.py tests/architecture/runtime_facade/test_layering.py -q
```
