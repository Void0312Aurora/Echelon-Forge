# WorldBatch 故障契约

Language:
- English canonical: [world_batch_failure_contract.md](world_batch_failure_contract.md)
- Chinese companion: `world_batch_failure_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/world_batch_failure_contract.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-10-17`

`WorldBatchRuntime` 不承诺对状态修改失败进行事务回滚。一个 world 可能已经推进或修改，
另一个 world 才报告异常。

本页描述的 maintained owner 契约已通过 PR #278（合并提交
`9edcb14dacd1127442efe0504bfee7c487a53628`）进入 `main`，并在最终 RFC 堆栈的
`main@ed9e476be4b57831001e0ef8e42d500989933e0e` 上重新验证。这是有界的 native
fail-closed 行为；不表示 #251 ADR 已批准，也不建立生产 supervisor 隔离、per-world
commit 真值、回滚或事务语义。

现有 fail-closed 契约要求：

1. 等待已经启动的 worker，向调用者重抛首个异常。
2. 将该 runtime generation 标记为 unhealthy。
3. unhealthy 期间，maintained batch 操作拒绝继续执行或重试。
4. 调用者通过 `batch_healthy()`、`batch_failure_reason()` 和 `batch_requires_host_recreate()` 获取诊断；仅在 native pipeline 已正常结束时允许 reset，否则退役宿主进程。
5. 只有成功完成的 reset 才清除故障状态。

maintained `RuntimeFacade` 通过 `batch_failure_status()` 暴露同一份 native-owned 快照，
字段包括 `healthy`、`generation`、`failure_reason` 和 `requires_host_recreate`。Facade
及 Python binding 不从异常或时钟观察自行重建恢复状态。CPU exact backend 是当前生产契约的
实现；候选 backend 只能报告自身拥有的故障信息，不能据此声称 CPU 或宿主 parity。

reset 使用指定 seed 重新初始化全部 world；它不是回滚。`world_raw_quarantine()` 仅用于诊断，
不属于同步恢复接口。无效 seed/time-step 等在 world 操作前被拒绝的输入不会使 batch 失效；
runtime task/worker 启动异常会使其失效。只读 batch 导出同样受保护，不能把失败 generation
当成成功同步结果。

Flecs callback 内的 C++ 异常可能留下未结束的 readonly/defer 和 iterator 状态，episode reset
无法修复这些内部状态。reset 和 raw step 会在修改前拒绝执行；失败 reset 保持 batch unhealthy，
generation 不变。恢复诊断仍可穿过故障 fence 读取；当 native owner 要求重建宿主时，Python
投影为 `terminate_generation`。此规则不证明同进程 world 析构安全。
仅测试用的 `ef_native_system_fault_probe` 构造 maintained `RuntimeFacade`，通过其
reset、step、快照和受保护导出操作运行；私有 accessor 只负责安装一次性的 ECS 故障夹具。
它验证该路径、fatal/非终止时间上限和新进程启动，不部署生产 supervisor。

native 资格测试通过私有 test accessor，在实际 3/4-world batch 中注入首个或后续 worker
启动失败，验证已启动 worker 在异常返回前汇合、导出和重试被封锁、恢复启动失败仍保留
故障状态，以及成功 reset 后恢复操作。时钟观察仍只是诊断；Python 聚合投影继续报告
未知的 per-world commit 状态。

实现起源于 PR #230 的 #210 owner 修复（`7989800d284484c76ccd0aed77cca32300fb2dda`），
并在资格验证阶段从历史的 `de19c3dbd69e9feb330b1291e84a210c53bfd09f` 接口基线完成适配。
历史分支和 SHA 继续保留用于溯源；maintained owner 修复现已进入 `main`。#210 仍为更宽的
契约与验收工作保持 open。后来新增的组合证据导出和 resize 操作同样会拒绝 unhealthy generation。
