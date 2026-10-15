# ADR：分层仿真故障域与恢复契约

语言：
- 英文规范页：[simulation_failure_domain_adr.md](simulation_failure_domain_adr.md)
- 中文配套页：`simulation_failure_domain_adr.zh.md`

Document kind: `standard`
Lifecycle: `proposed`
Canonical: `docs/architecture/standards/simulation_failure_domain_adr.md`
Owner: `architecture/failure-contracts`
Last verified: `2026-10-15`

**状态：** 待评审的契约设计；不授权新增 host、事务引擎或生产切换。
上游 `main` 不被视为已经执行了完整契约；其中有界的 native #210 owner 修复已通过
PR #278 进入 `main`，并在 `main@ed9e476be4b57831001e0ef8e42d500989933e0e` 上重新验证；
更宽的恢复和 supervisor 契约仍为 proposed，尚未准入。

使用分层 outcome 词汇区分 admission、mechanism/stage、单 world、batch 与 host/process 故障。
各层报告观察事实，native world/ECS truth 仍负责状态有效性；facade/Python 只能翻译，不得从
exception 推断 rollback。

目标 CPU/facade 策略是 fail-closed：preflight 拒绝不发布；mid-step 或 worker 故障产生明确
generation fence，除非有可靠的 per-world 证据，否则状态为 unknown/untrusted；禁止透明重试，
只能显式 reset/recreate。已进入 `main` 的有界 native #210 owner 修复在受测
`WorldBatchRuntime` 路径上验证了该目标；但 supervisor 隔离、per-world commit 真值、回滚和
事务语义仍未建立，因此更宽的生产路径仍是开放的集成门槛。部分完成 batch 不得报告为同步成功；
abort、死锁和阻塞 native code
不属于同进程恢复能力，需在受限 subprocess 中验证。#209/#210 保留各自实现所有权，现有
RunReceipt/evidence 和 #239 投影继续作为证据权威。

## 当前状态和迁移矩阵

| 状态 | 观察含义 | 允许操作 | 离开状态所需证据 |
| --- | --- | --- | --- |
| `healthy` | generation 没有故障 fence | 按 owner API 执行已准入 setup、step、只读导出和 reset | 成功操作或成功 reset 证据 |
| `failed/untrusted` | 已记录 preflight 安全失败、worker 故障或修改后不确定性；不暗示 rollback | 诊断和显式 reset/recreate；禁止修改性重试或同步成功导出 | 成功 reset/recreate，重新初始化完整 expected world 范围 |
| `failed/host-recreate-required` | 运行中的 Flecs callback 留下未结束的 readonly/defer 状态 | 诊断并退役宿主进程；reset、step 和同步导出继续被封锁 | 独立替代进程初始化并成功运行新的 native batch |
| reset 后 `healthy` | 新 generation 已完成初始化 | 新 generation 的正常操作 | reset 结果及 native 状态/setup 证据；不证明发生了 rollback |

本分支可以在受测 native 路径证明注入的 worker 启动和任务故障会进入第二行；native
owner 提供仅在成功 reset 后递增的 batch generation ID。运行中 system 异常证明进入终止恢复路径；
受限子进程控制验证 fatal 退出、非终止 callback 的超时终止及回收、替代宿主进程正常启动。
这些证据尚不证明生产 supervisor 隔离、可靠的 per-world 提交、回滚、取消或受损 Flecs world 的安全析构。

Python 资格 adapter 现在先读取 native owner 的 `batch_healthy()` 和
`batch_failure_reason()`，再投影全部未知结果；健康 runtime 会被拒绝，adapter 不会创建
generation ID，也不会伪造 reset 结果；native generation identity 仍由 owner 提供。

## 方案比较与实现检查点

方案比较以英文规范页的 Option comparison 为准。

公开 `BatchOperationOutcome` 构造在任何 `completed` 结果上都要求非空的 expected-world
证据并精确覆盖全部 world index；默认空范围不能绕过这个不变量。skipped/unknown 不能冒充完成，
aggregate fault 保守投影为全部受影响 world 未知，不从时钟推断回滚。PR #230 中的 #210 owner 修复
历史上曾移植到资格分支接口，并保护新增的组合证据导出；现已通过 PR #278 进入 `main`；参见
[WorldBatch 故障契约](world_batch_failure_contract.zh.md)。

native 3/4-world 串并行证明覆盖不同 world 的推进差异、时间步已改变后的 setup 异常、
导出/重试保护、无效恢复输入及显式 reset；Python 和 maintained facade 复用同一 native
fence。全部 world 未知时结果为 `failed`，要求显式 reset/recreate，不推断 per-world commit。
机制子故障证明单独观察到内部状态改变、外部 packet 尚未发布。这些有界变更不关闭更宽的
#210 契约；native batch 另注入 worker 启动失败，验证已启动 worker 汇合、导出封锁、失败
恢复封锁和显式 reset 的 fail-closed 行为。新的 native system 探针在修改 ECS 状态后抛异常，
验证未结束的 pipeline 会拒绝 reset 和 raw step，native owner 的
`batch_requires_host_recreate()` 由 Python 转译为 `terminate_generation`。
危险控制只在独立子进程中执行；受损异常测试进程直接退役，不宣称 Flecs 析构安全。

详见[原型证据和剩余门槛](../work/issues/rfc_qualified_composition_implementation.md)。Lifecycle 仍为 proposed；此检查点不代表 owner 批准或生产准入。
