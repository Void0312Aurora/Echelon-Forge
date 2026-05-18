# `src/runtime/contracts` 边界

`runtime/contracts` 保存 runtime/facade 与 lower-level runtime owner 之间共享的稳定 DTO。这里的类型可以被 facade、engine、Python bindings 和测试共同引用，但不能拥有 world state、ECS registry 或系统调度逻辑。

## 允许

- `WorldEntityRef` 这类轻量引用。
- batch setup / command / tasking / episode step request DTO。
- 只由 value types、component DTO 和 mission runtime DTO 组成的 request/result 类型。

## 禁止

- `SimulationKernel`、`WorldBatchRuntime` 或其他 owner class。
- Flecs system 注册、step 调度、GPU helper 实现。
- Python/nanobind 绑定逻辑。
- 为了方便 include 而引入 `core/engine/*`。

## 迁移备注

本目录是后续 `ef_contracts` target 的候选起点。新增 facade-facing 类型应优先放在这里，再由 facade 或 engine implementation 消费。
