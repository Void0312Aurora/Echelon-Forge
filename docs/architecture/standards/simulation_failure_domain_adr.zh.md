# ADR：分层仿真故障域与恢复契约

语言：
- 英文规范页：[simulation_failure_domain_adr.md](simulation_failure_domain_adr.md)
- 中文配套页：`simulation_failure_domain_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-11`

**状态：** 待评审的契约设计；不授权新增 host、事务引擎或生产切换。

使用分层 outcome 词汇区分 admission、mechanism/stage、单 world、batch 与 host/process 故障。
各层报告观察事实，native world/ECS truth 仍负责状态有效性；facade/Python 只能翻译，不得从
exception 推断 rollback。

当前 CPU/facade 最小策略是 fail-closed：preflight 拒绝不发布；mid-step 或 worker 故障产生明确
generation fence，除非有可靠的 per-world 证据，否则状态为 unknown/untrusted；禁止透明重试，
只能显式 reset/recreate。部分完成 batch 不得报告为同步成功；abort、死锁和阻塞 native code
不属于同进程恢复能力，需在受限 subprocess 中验证。#209/#210 保留各自实现所有权，现有
RunReceipt/evidence 和 #239 投影继续作为证据权威。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

completed 构造要求覆盖全部 expected worlds；skipped/unknown 不能冒充完成，aggregate fault
保守投影为全部受影响 world 未知，不从时钟推断回滚。PR #230 中的 #210 owner 修复已局部
移植到当前 main 接口，并保护新增的组合证据导出；参见
[WorldBatch 故障契约](world_batch_failure_contract.zh.md)。

native 3/4-world 串并行证明覆盖不同 world 的推进差异、时间步已改变后的 setup 异常、
导出/重试保护、无效恢复输入及显式 reset；Python 和 maintained facade 复用同一 native
fence。全部 world 未知时结果为 `failed`，要求显式 reset/recreate，不推断 per-world commit。
机制子故障证明单独观察到内部状态改变、外部 packet 尚未发布。这些本地变更不代表上游
#210 关闭；native batch 另注入 worker 启动失败，验证已启动 worker 汇合、导出封锁、失败
恢复封锁和显式 reset 的 fail-closed 行为。运行中的 native system 异常、runtime generation
ID 和受限 fatal/阻塞控制仍待验证。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
