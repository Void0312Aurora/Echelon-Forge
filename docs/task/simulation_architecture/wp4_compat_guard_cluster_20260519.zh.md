# WP4-I 分发表：Compatibility Guard And Integration

状态：`2026-05-19` 第二波分发表；偏串行/集成。

语言版本：

- 英文主文：[wp4_compat_guard_cluster_20260519.md](wp4_compat_guard_cluster_20260519.md)
- 中文辅文：`wp4_compat_guard_cluster_20260519.zh.md`

输入：

- [WP4 第一波验收审查](../review/wp4_first_wave_acceptance_review_20260519.zh.md)
- [WP4-A surface inventory 初稿](wp4_surface_inventory_wp4a_20260519.zh.md)
- [WP4-B/C engagement-step 对齐笔记](wp4_engagement_step_alignment_notes_20260519.md)
- [WP4-D/E policy-binding 对齐笔记](wp4_policy_binding_alignment_notes_20260519.zh.md)
- 当前 `tests/architecture/`、WP4 docs 与 smoke suite metadata

## 一、目的

WP4-I 是串行 guardrail 与 integration 任务簇。它防止 compatibility-only path 悄悄成为 maintained frontend path，并把第二波成果整合进 WP4 到 WP5 的移交。

## 二、必需工作项

| 流 | 必需输出 | 写入范围 | 预算 |
|----|----------|----------|------|
| `WP4-I1 Raw Runtime Guard Review` | 审查或添加 architecture check，确保 maintained path 不新增依赖 `RuntimeFacade::runtime()`、raw `WorldBatchRuntime` 或 direct `sim.*` policy input。 | `tests/architecture/`、docs。 | 高。 |
| `WP4-I2 Surface Inventory Integration` | 更新 WP4 文档，引用已验收 WP4-A inventory 与第二波 gates。 | `docs/task/simulation_architecture`。 | 中。 |
| `WP4-I3 Review Index Sync` | 把 WP4 第一波验收审查与第二波任务簇加入 review/task index。 | `docs/task/review/README*`、`docs/task/simulation_architecture/README*`。 | 中。 |
| `WP4-I4 WP5 Handoff Note` | 说明 WP5 可立即验证什么，哪些仍等待 runtime/facade metadata。 | `docs/task/simulation_architecture`，可选 review doc。 | 中高。 |

## 三、非目标

- 不实现 facade DTO 变更。
- 不移除 compatibility adapter。
- 除非 focused guard 已通过且本地 artifact 明确新鲜，否则不运行大范围测试。
- 在 WP4-G 与 WP4-H 结果被验收前，不关闭 WP4。

## 四、验收门槛

本任务簇验收条件：

1. WP4 docs 与索引引用已验收第一波产物。
2. Compatibility-only 与 diagnostics-only path 有 guard 覆盖或记录了 pending guard。
3. WP5 handoff 明确 immediate validation target 与仍等待 runtime/facade work 的 metadata。
4. 被触及的 docs/tests 通过 `git diff --check`。
