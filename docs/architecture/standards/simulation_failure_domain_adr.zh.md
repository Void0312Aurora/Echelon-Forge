# ADR：分层仿真故障域与恢复契约

语言：
- 英文规范页：[simulation_failure_domain_adr.md](simulation_failure_domain_adr.md)
- 中文配套页：`simulation_failure_domain_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-12`

**状态：** 待评审的契约设计；不授权新增 host、事务引擎或生产切换。
上游 `main` 不被视为已经执行了完整契约；资格分支只携带本地 #210 owner
实现和相应证据，不能把它报告为主线或生产保证。

使用分层 outcome 词汇区分 admission、mechanism/stage、单 world、batch 与 host/process 故障。
各层报告观察事实，native world/ECS truth 仍负责状态有效性；facade/Python 只能翻译，不得从
exception 推断 rollback。

目标 CPU/facade 策略是 fail-closed：preflight 拒绝不发布；mid-step 或 worker 故障产生明确
generation fence，除非有可靠的 per-world 证据，否则状态为 unknown/untrusted；禁止透明重试，
只能显式 reset/recreate。本资格分支在受测 `WorldBatchRuntime` 路径上验证了本地 #210 移植；
上游生产路径仍须等待 owner 修复交付并按主线祖先重新验证。部分完成 batch 不得报告为同步成功；
abort、死锁和阻塞 native code
不属于同进程恢复能力，需在受限 subprocess 中验证。#209/#210 保留各自实现所有权，现有
RunReceipt/evidence 和 #239 投影继续作为证据权威。

## 当前状态和迁移矩阵

| 状态 | 观察含义 | 允许操作 | 离开状态所需证据 |
| --- | --- | --- | --- |
| `healthy` | generation 没有故障 fence | 按 owner API 执行已准入 setup、step、只读导出和 reset | 成功操作或成功 reset 证据 |
| `failed/untrusted` | 已记录 preflight 安全失败、worker 故障或修改后不确定性；不暗示 rollback | 诊断和显式 reset/recreate；禁止修改性重试或同步成功导出 | 成功 reset/recreate，重新初始化完整 expected world 范围 |
| reset 后 `healthy` | 新 generation 已完成初始化 | 新 generation 的正常操作 | reset 结果及 native 状态/setup 证据；不证明发生了 rollback |

本分支可以在受测 native 路径证明注入的 worker 启动和任务故障会进入第二行，
但尚未证明 native 签发的 generation ID、可靠的 per-world 提交发布、取消，或对
`abort`、进程退出、死锁和非终止的隔离。

Python 资格 adapter 现在先读取 native owner 的 `batch_healthy()` 和
`batch_failure_reason()`，再投影全部未知结果；健康 runtime 会被拒绝，adapter 不会创建
generation ID，也不会伪造 reset 结果。

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
