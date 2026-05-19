# WP4-G 分发表：Facade Evidence Gates

状态：`2026-05-19` 第二波分发表。

语言版本：

- 英文主文：[wp4_facade_evidence_cluster_20260519.md](wp4_facade_evidence_cluster_20260519.md)
- 中文辅文：`wp4_facade_evidence_cluster_20260519.zh.md`

输入：

- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-B/C engagement-step 对齐笔记](wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-A surface inventory 初稿](wp4_surface_inventory_wp4a_20260519.zh.md)
- 当前 `tests/runtime/engagement/`、`tests/runtime/facade/` 与
  `tests/smoke/ci_smoke_suite.json`

## 一、目的

WP4-G 把第一波 engagement 与 step/lifecycle 发现转化为聚焦 evidence gate。它应优先使用窄测试和有文档记录的 skip，而不是大范围 facade DTO churn。

## 二、必需工作项

| 流 | 必需输出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP4-G1 Engagement Producer Coverage Gate` | 测试或文档 fixture，证明当前 `EngagementEventPacket` 已填充 slot 和 deferred placeholder 是有意的。 | `tests/runtime/engagement/`、docs。 | 中。 |
| `WP4-G2 Multi-World Retag Coverage` | 在当前 fixture 允许时，把覆盖扩展到 effects/damage retag，而不只 launch-event munition retag。 | `tests/runtime/engagement/`。 | 中。 |
| `WP4-G3 Diagnostics Piggyback Gate` | 测试或 doc gate，说明 engagement export 中的 `DiagnosticsTrace` 是 piggyback evidence，不是完整 diagnostics surface。 | `tests/runtime/engagement/`、docs。 | 中。 |
| `WP4-G4 Step Result Semantic Shape Gate` | 测试当前 `ExecutionBatchStepResult` 字段：reward、termination/truncation、reward JSON、step info、controller-state changed 与 observation packet。 | `tests/runtime/facade/`。 | 中高。 |
| `WP4-G5 Smoke Candidate Note` | 建议哪些聚焦测试应提升到 WP5 smoke，哪些只保留为 WP4-only。 | docs/task/simulation_architecture。 | 中。 |

## 三、非目标

- 除非没有最小已验收字段就无法写测试，否则不新增 public facade DTO。
- 不编辑 policy/gym/binding。
- 不替换 `RecentEngagementEvents`。
- 本任务簇不创建 dedicated diagnostics facade surface。

## 四、验收门槛

本任务簇验收条件：

1. 当前 engagement export producer coverage 可测试或已显式记录。
2. Deferred slot 保持有意且可见。
3. Multi-world retagging 至少有一个已验收 WP3 path 之外的聚焦 guard，或已记录缺失 fixture。
4. Step-result semantic shape 在不需要 RL training dependency 的情况下被 guard。
5. 推荐命令已记录，供 WP4-F/WP5 集成。
