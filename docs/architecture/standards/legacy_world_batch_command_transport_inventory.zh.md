# Legacy WorldBatch 命令传输清单

本清单记录维护迁移完成后三个 raw 命令写入器的处理决定。维护中的
`RuntimeFacade` 路径使用带类型的 `*MaintainedAssignment` 请求，是唯一受支持的
Python 执行路径。

| Legacy 符号 | 声明/定义位置 | 受支持调用者 | 决定 |
| --- | --- | --- | --- |
| `WorldBatchRuntime::set_mission_commands_batch` | `world_batch_runtime.h/.cpp`、`bindings_runtime_engine.cpp` | `src/`、`python/` 和受支持测试中均无 | 退役 |
| `WorldBatchRuntime::set_leader_intents_batch` | `world_batch_runtime.h/.cpp`、`bindings_runtime_engine.cpp` | `src/`、`python/` 和受支持测试中均无 | 退役 |
| `WorldBatchRuntime::set_pilot_reports_batch` | `world_batch_runtime.h/.cpp`、`bindings_runtime_engine.cpp` | `src/`、`python/` 和受支持测试中均无 | 退役 |

旧的 `World*Assignment` DTO 仍保留在 contract 头文件和 tasking binding 中，因为诊断和
证据投影的兼容 shell 仍使用其字段形状。它们不再被 raw 命令写入器接受。维护中的批量
DTO 和 facade 方法保持不变。

## 打包边界

生产 `ef_py` 使用 `EF_PRODUCTION_FACADE_ONLY=ON` 配置，并排除
`bindings_runtime_engine.cpp`，因此不会暴露 `WorldBatchRuntime`。显式 opt-in 的
`ef_py_diagnostics` 目标仍可以暴露 raw runtime 的诊断查询面，但三个退役写入符号也
已从该 binding 中删除。架构测试继续禁止旧名称重新进入维护 adapter 或 facade 路径。

本次是符号级退役，不删除 `WorldBatchRuntime`、兼容 shell DTO 或维护中的命令投影和
replay 逻辑。
