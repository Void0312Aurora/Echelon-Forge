# WP9-E Integration And Index Sync

状态：`2026-05-20` complete / accepted WP9 串行集成流。

语言版本：

- 英文主文：[wp9_integration_and_index_sync_cluster_20260520.md](wp9_integration_and_index_sync_cluster_20260520.md)
- 中文辅文：`wp9_integration_and_index_sync_cluster_20260520.zh.md`

输入：

- [WP9 contract and infrastructure closure](contract_infrastructure_closure_wp9_20260520.zh.md)
- [WP9-A DTO promotion batch 1](wp9_dto_promotion_batch1_cluster_20260520.zh.md)
- [WP9-B DTO promotion batch 2](wp9_dto_promotion_batch2_cluster_20260520.zh.md)
- [WP9-C infrastructure closure](wp9_infrastructure_closure_cluster_20260520.zh.md)
- [WP9-D guard enforcement](wp9_guard_enforcement_cluster_20260520.zh.md)
- 已完成 subagents 的 worker handoff notes。

## 1. 目的

WP9-E 是 A-D 之后的唯一串行发布步骤。它负责 shared binding glue、CMake/module reconciliation、README/index 更新、双语对齐与最终验收证据。

## 2. 前置条件

WP9-E 不应在以下条件满足前启动：

1. WP9-A、WP9-B、WP9-C 与 WP9-D 均返回 touched files 与 validation results。
2. 任何 shared edit conflict 都有明确 owner。
3. DTO streams 的 binding/CMake changes 已合并，或列为 integration work。
4. 没有 worker 留下无命名 owner 的 untracked residual。

## 3. 必需集成工作

| 项目 | 必需产出 |
|------|----------|
| Shared contract includes | 确保 DTO headers 可从 facade 与 bindings 到达，且没有 circular 或 engine-owner includes。 |
| Python binding glue | 协调 A/B binding additions、module declarations 与 focused smoke tests。 |
| README/index sync | 用最终 WP9 status 与链接更新 simulation architecture README 及中文辅文。 |
| Architecture cross references | 添加或更新 promoted DTOs、diagnostics facade、guard allowlist 与 infrastructure closure 引用。 |
| Acceptance review | 发布 `wp9_contract_infrastructure_closure_acceptance_review_20260520.md` 与 `.zh.md`。 |
| Validation | 运行或记录 doc checks、architecture tests、binding smoke 与 focused runtime tests 的 blocked status。 |

## 4. 验收 Review 形状

最终 review 必须包括：

1. WP9-A 至 WP9-E 的逐 gate verdict。
2. DTO-1 至 DTO-8、INF-1 至 INF-7 与 GUA-1/GUA-2 的 evidence rows。
3. 准确 validation commands 与 outcomes。
4. 如有 residual risks，带 owner 与 next work package labels。
5. 双语对齐说明。

## 5. 非目标

- 不在 WP9-E 中引入新的 WP10+ scope。
- 不把 blocked runtime validation 藏在 passing doc checks 后面。
- 除了解决 integration conflicts，不重写 worker-owned implementation。
- 在中英文 acceptance review 均存在前，不标记 WP9 accepted。

## 6. 验证命令

```bash
git diff --check
pytest tests/architecture tests/runtime/bindings tests/runtime/engagement tests/runtime/facade
rg -n "WP9|Contract And Infrastructure Closure|RewardReport|TerminationSpec|ObservationViewSpec|ActionIntentPacket|CoordinationIntentPacket|AgentRole|DecisionBelief|DiagnosticsTrace|StageNodeManifest|sim\\.\\*" docs/task/simulation_architecture docs/task/review docs/plan/architecture src tests
```
