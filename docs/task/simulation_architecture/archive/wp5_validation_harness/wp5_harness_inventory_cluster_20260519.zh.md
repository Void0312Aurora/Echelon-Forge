# WP5-A 分发单：验证套件盘点

状态：`2026-05-19` 第一波分发单。

语言版本：

- 英文主文：[wp5_harness_inventory_cluster_20260519.md](wp5_harness_inventory_cluster_20260519.md)
- 中文辅文：`wp5_harness_inventory_cluster_20260519.zh.md`

输入：

- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-F 集成交接](wp4_integration_handoff_20260519.zh.md)
- 当前 `tests/architecture/`、`tests/runtime/` 与 `tests/smoke/ci_smoke_suite.json`

## 1. 目的

WP5-A 在更宽的测试提升前，把当前证据映射到 WP5 五个验证层级。它应找出已经能证明架构的内容，以及仍然缺失的 gate，但不改变 runtime 行为。

## 2. 必做工作

| 流 | 必要产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP5-A1 Tier Inventory` | 将现有 architecture、facade、engagement、binding、execution 与 smoke tests 映射到 design、trace、boundary、information/belief 与 replay/evidence 层级。 | `docs/task/simulation_architecture`。 | 中等。 |
| `WP5-A2 Smoke Membership Review` | 识别哪些测试已在 `tests/smoke/ci_smoke_suite.json` 中，哪些应成为候选，哪些过宽或依赖 metadata。 | 本任务簇只写文档。 | 中等。 |
| `WP5-A3 Gap Register` | 根据 WP4 最终验收的剩余风险，记录 immediate gap 与 metadata-dependent gap。 | `docs/task/simulation_architecture`。 | 中等。 |
| `WP5-A4 Dispatch Advice` | 建议哪些 gate 交给 WP5-B/C/D/E 实现，哪些应继续 deferred。 | `docs/task/simulation_architecture`。 | 中等。 |

## 3. 非目标

- 不编辑 runtime code。
- 不在本任务簇提升 smoke-suite 条目。
- 除非需要极小的文档支撑 fixture，否则不新增测试。
- 不强制 WP4 明确推迟到 WP5 或后续 DTO 工作的 metadata。

## 4. 验收门槛

本任务簇满足以下条件时验收：

1. WP5 每个验证层级都有当前覆盖、候选覆盖或显式 gap。
2. Smoke-suite 候选带有理由。
3. Immediate gate 与 metadata-dependent gate 被分开。
4. Inventory 为 WP5-B/C/D/E 提供足够清楚的 ownership 边界，避免写入重叠。
