# WP20 Subagent Dispatch Queue

状态：`2026-05-21` closed / accepted。

语言版本：

- 英文主文：[wp20_subagent_dispatch_queue_20260521.md](wp20_subagent_dispatch_queue_20260521.md)
- 中文辅文：`wp20_subagent_dispatch_queue_20260521.zh.md`

输入：

- [WP20 主计划](public_capability_platform_composition_wp20_20260521.zh.md)
- [Subagent 使用规范](../../../standards/governance/subagent_usage_policy.zh.md)

## 队列

| Stream | 依赖 | 派发状态 | 写入范围 |
|--------|------|----------|----------|
| `WP20-A Public Capability Fact Ledger` | none | pass | 仅文档：fact ledger。source/test 只读盘点。 |
| `WP20-B Public Typed Platform Spawn Contract` | A 可细化但不阻塞 | focused pass | Contract/result DTO 与聚焦 architecture tests。不改 runtime materialization。 |
| `WP20-E Compatibility And Schema Guard` | A 可细化但不阻塞 | pass | Architecture/schema/compatibility tests。不改 runtime behavior。 |
| `WP20-C Runtime Setup Consume Bridge` | B contract | accepted / focused pass | Runtime/facade setup consume path 与 runtime/facade tests。 |
| `WP20-D Facade And Binding Public Surface` | B and C | accepted / focused pass | Python/facade binding exposure 与 binding tests。 |
| `WP20-F Integration And Handoff` | A-E | complete / accepted | Integration、validation rollup、residuals、indexes、acceptance review。 |

## 第一轮派发

| Stream | 建议模型 / 思考预算 | Dispatch packet |
|--------|----------------------|-----------------|
| `WP20-A` | `gpt-5.4-mini`, xhigh | 产出 source-backed fact ledger；必要时只编辑 A cluster docs。 |
| `WP20-B` | `gpt-5.4`, xhigh | 实现/添加 public result/admission contract 与聚焦测试；不改 runtime materialization。 |
| `WP20-E` | `gpt-5.4`, high | 将 WP14 additive-only guards 更新为 WP20 validation-first publicization；不改 runtime behavior。 |

## 第二轮派发

| Stream | 建议模型 / 思考预算 | Dispatch packet |
|--------|----------------------|-----------------|
| `WP20-C` | `gpt-5.4`, xhigh | Bernoulli 已返回并通过 focused validation。它在 runtime/facade setup 中通过 B contract 消费 typed setup requests，且未改 bindings。 |
| `WP20-D` | `gpt-5.4`, high | Lovelace 已返回并通过 focused validation。它通过 Python bindings 暴露 `TypedPlatformSpawnResult` 与 `BatchWorldSetupResult.typed_platform_spawn_results`，且未改变 runtime materialization semantics。 |

## Closure-Wave Dispatch

| Stream | 建议模型 / 思考预算 | Dispatch packet |
|--------|----------------------|-----------------|
| `WP20-F` | `gpt-5.4-mini`, xhigh | 已关闭。集成 A-E evidence、运行 validation rollup、记录 residuals、同步 README/index status，并起草 acceptance review。不改变 implementation semantics。 |

## Worker Return Packet

每个 worker 必须返回：

- status: `pass`、`blocked` 或 `preflight-only`；
- touched files；
- validation commands and outcomes；
- blockers and residuals；
- 给下一 stream 的 integration notes；
- 确认没有回退 unrelated edits。

## Stop Rules

- 不删除或废弃 `spawn_unit(type_name)` / `WorldSpawnRequest.type_name`。
- 不强制 scenario JSON、examples 或 Python callers 迁移。
- 不把 platform capability semantics 放进 backend `RuntimeCapabilities`。
- 不添加新 tactical behavior。
- 遇到 blocker 时命名后停止，不要扩展到 WP21。
