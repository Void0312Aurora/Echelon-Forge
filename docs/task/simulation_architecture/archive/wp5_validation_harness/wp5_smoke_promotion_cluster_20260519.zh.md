# WP5-E 分发单：Smoke Promotion 与文档

状态：`2026-05-19` 第二波串行集成分发单。

语言版本：

- 英文主文：[wp5_smoke_promotion_cluster_20260519.md](wp5_smoke_promotion_cluster_20260519.md)
- 中文辅文：`wp5_smoke_promotion_cluster_20260519.zh.md`

输入：

- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP5 第一波验收审查](../review/wp5_first_wave_acceptance_review_20260519.zh.md)
- [WP5-A harness inventory 笔记](wp5_harness_inventory_notes_20260519.zh.md)
- [WP5-B design/boundary 笔记](wp5_design_boundary_notes_20260519.zh.md)
- [WP5-C trace/replay gates 笔记](wp5_trace_replay_gates_notes_20260519.zh.md)
- WP5-D information/belief 产物，待验收后纳入
- 当前 `tests/smoke/ci_smoke_suite.json`

## 1. 目的

WP5-E 是串行集成流。它发布维护中的 WP5 smoke command set，更新索引，并记录每个
被提升测试为什么属于 validation harness。

WP5-E 不应在 WP5-D 返回前启动最终 smoke-suite 编辑，因为 information/belief 候选会影响最终五层覆盖。

## 2. 必做工作

| 流 | 必要产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP5-E1 Smoke Candidate Merge` | 合并 WP5-A/B/C/D 候选列表，形成聚焦 suite proposal。 | 先写 docs；如验收再写 `tests/smoke/ci_smoke_suite.json`。 | 中等。 |
| `WP5-E2 Smoke Rationale` | 记录每个 promoted test 覆盖哪个 validation tier。 | `docs/task/simulation_architecture`。 | 中等。 |
| `WP5-E3 Index Sync` | 从 task/review 索引链接 WP5 notes、review 与最终 validation command。 | `docs/task/simulation_architecture/README*`、`docs/task/review/README*`。 | 中等。 |
| `WP5-E4 Final Validation Command` | 发布并运行覆盖 design、trace、boundary、information/belief 与 replay/evidence 层级的本地命令集。 | docs、smoke suite。 | 中等。 |

## 3. 非目标

- 不新增 runtime 语义。
- 除非具备清楚 WP5 tier ownership 且成本可接受，不提升宽泛 domain directory。
- DTO 字段存在前，不强制 metadata-dependent gate。
- 不在未阅读和保留现有改动的情况下覆盖其他 worker 的 smoke-suite 编辑。

## 4. 验收门槛

本任务簇满足以下条件时验收：

1. Smoke suite 或已发布 smoke command 覆盖 WP5 五个层级。
2. 每个 promoted test 都有 tier rationale。
3. Task 与 review 索引同步。
4. 聚焦验证与 `git diff --check` 通过。
