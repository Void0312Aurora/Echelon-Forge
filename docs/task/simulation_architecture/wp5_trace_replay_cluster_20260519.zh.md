# WP5-C 分发单：Trace 与 Replay Gate

状态：`2026-05-19` 第一波分发单。

语言版本：

- 英文主文：[wp5_trace_replay_cluster_20260519.md](wp5_trace_replay_cluster_20260519.md)
- 中文辅文：`wp5_trace_replay_cluster_20260519.zh.md`

输入：

- [WP5 验证套件](validation_harness_wp5_20260519.zh.md)
- [WP4 facade 对齐验收审查](../review/wp4_facade_alignment_acceptance_review_20260519.zh.md)
- [WP4-G facade evidence 笔记](wp4_facade_evidence_notes_20260519.md)
- [WP4-B/C engagement-step 对齐笔记](wp4_engagement_step_alignment_notes_20260519.md)
- 当前 `tests/runtime/engagement/` 与 `tests/runtime/facade/`

## 1. 目的

WP5-C 围绕已经存在的 evidence 添加 trace 与 replay-facing gate。它应验证 ancestry、id、world-safe retagging 与当前 replay metadata 可用性，但不发明新的 runtime 语义。

这是一条高推理流，因为对 event ordering、source time 或 trace ancestry 的错误假设会产生脆弱测试。

## 2. 必做工作

| 流 | 必要产出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP5-C1 Trace Ancestry Gate` | 为 engagement export 当前携带的 launch/effects/damage/diagnostics ancestry 添加或记录聚焦测试。 | `tests/runtime/engagement/`，可选 docs note。 | 高。 |
| `WP5-C2 Replay Metadata Availability Review` | 区分今天已有的 metadata 与 WP2.5/WP4 推迟的 metadata，尤其是 snapshot、barrier、source-time 与 deterministic event-id 字段。 | `tests/runtime/facade/`、`tests/runtime/engagement/`、docs note。 | 高。 |
| `WP5-C3 Piggyback Diagnostics Boundary` | 保持 `DiagnosticsTrace` 在 WP4/WP5 第一波中只是 piggyback evidence，而不是专用 diagnostics facade surface。 | `tests/runtime/engagement/`、docs。 | 中高。 |
| `WP5-C4 Smoke Candidate Note` | 为后续 WP5 smoke promotion 推荐 trace/replay 测试。 | 文档笔记或交给 integration owner。 | 中等。 |

## 3. 非目标

- 不在本任务簇新增专用 diagnostics facade query。
- DTO 支持存在前，不要求 snapshot/barrier/source-time metadata。
- 不替换 `RecentEngagementEvents`，不改变 event ordering 语义。
- 除非 integration owner 已接受最小字段，否则不编辑宽泛 facade signature。

## 4. 验收门槛

本任务簇满足以下条件时验收：

1. 当前 trace ancestry 被测试，或被明确记录为缺失。
2. 当前可用 replay metadata 与依赖未来 metadata 的 gate 被分开。
3. Diagnostics piggyback evidence 与 dedicated diagnostics surface 保持区分。
4. 聚焦测试本地通过。
