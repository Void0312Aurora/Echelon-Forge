<!-- Machine-translated draft generated on 2026-05-18 from src/runtime/contracts/README.md. Review before treating this file as authoritative. -->

# `src/runtime/contracts` 边界

`runtime/contracts` 保存运行时/门面与低级运行时所有者之间共享的稳定DTO。这里的类型可以被门面、引擎、Python绑定和测试共同引用，但不能拥有世界状态、ECS注册表或系统调度逻辑。

## 允许

- `WorldEntityRef` 这类轻量引用。
- 批量设置/命令/任务/情节步骤请求DTO。
- 仅由值类型、组件DTO和任务运行时DTO组成的请求/结果类型。

## 禁止

- `SimulationKernel`、`WorldBatchRuntime` 或其他所有者类。
- Flecs系统注册、步骤调度、GPU辅助程序实现。
- Python/nanobind 绑定逻辑。
- 为了方便包含而引入 `core/engine/*`。

## 迁移备注

本目录是后续 `ef_contracts` target 的候选起点。新增面向门面的类型应优先放在这里，再由门面或引擎实现消费。
