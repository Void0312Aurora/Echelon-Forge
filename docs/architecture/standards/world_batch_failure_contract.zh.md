# WorldBatch 故障契约

Language:
- English canonical: [world_batch_failure_contract.md](world_batch_failure_contract.md)
- Chinese companion: `world_batch_failure_contract.zh.md`

Document kind: `standard`
Lifecycle: `maintained`
Canonical: `docs/architecture/standards/world_batch_failure_contract.md`
Owner: `architecture/runtime-workflow`
Last verified: `2026-10-11`

`WorldBatchRuntime` 不承诺对状态修改失败进行事务回滚。一个 world 可能已经推进或修改，
另一个 world 才报告异常。

现有 fail-closed 契约要求：

1. 等待已经启动的 worker，向调用者重抛首个异常。
2. 将该 runtime generation 标记为 unhealthy。
3. unhealthy 期间，maintained batch 操作拒绝继续执行或重试。
4. 调用者通过 `batch_healthy()`、`batch_failure_reason()` 获取诊断，显式调用 `reset_batch()` 恢复。
5. 只有成功完成的 reset 才清除故障状态。

reset 使用指定 seed 重新初始化全部 world；它不是回滚。`world_raw_quarantine()` 仅用于诊断，
不属于同步恢复接口。无效 seed/time-step 等在 world 操作前被拒绝的输入不会使 batch 失效；
runtime task/worker 启动异常会使其失效。只读 batch 导出同样受保护，不能把失败 generation
当成成功同步结果。

本地集成从 `7989800d284484c76ccd0aed77cca32300fb2dda` 移植 PR #230 的 #210 owner 实现，
保留当前 maintained command 接口和 broadphase 类型，同时保护后来新增的组合证据导出和
resize 操作。移植保留在资格验证分支，上游 #210 仍然 open，此分支不代表已交付 main。
