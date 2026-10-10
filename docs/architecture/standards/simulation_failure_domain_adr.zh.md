# ADR：分层仿真故障域与恢复契约

语言：
- 英文规范页：[simulation_failure_domain_adr.md](simulation_failure_domain_adr.md)
- 中文配套页：`simulation_failure_domain_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-10`

**状态：** 待评审的契约设计；不授权新增 host、事务引擎或生产切换。

使用分层 outcome 词汇区分 admission、mechanism/stage、单 world、batch 与 host/process 故障。
各层报告观察事实，native world/ECS truth 仍负责状态有效性；facade/Python 只能翻译，不得从
exception 推断 rollback。

当前 CPU/facade 最小策略是 fail-closed：preflight 拒绝不发布；mid-step 或 worker 故障产生明确
generation fence，除非有可靠的 per-world 证据，否则状态为 unknown/untrusted；禁止透明重试，
只能显式 reset/recreate。部分完成 batch 不得报告为同步成功；abort、死锁和阻塞 native code
不属于同进程恢复能力，需在受限 subprocess 中验证。#209/#210 保留各自实现所有权，现有
RunReceipt/evidence 和 #239 投影继续作为证据权威。
