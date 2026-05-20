# `src/runtime/facade` 边界

`runtime/facade` 是维护中的 C++ 应用层 API。它面向训练环境、Python 绑定和后续前端主线，提供 typed request/result，而不是暴露底层 world owner 的全部细节。

## 允许

- `RuntimeFacade`。
- facade request/result/capability 类型。
- 批量 reset、setup、step、command、tasking、episode 和 observation 操作。
- 专用 diagnostics-trace query/export 操作。
- 对 `WorldBatchRuntime` 与 `ExecutionEpisodeController` 的受控包装。
- public header 只暴露 facade / contracts 类型；底层 `WorldBatchRuntime` owner 应留在 implementation 中。

## 禁止

- 实现 ECS system 或物理模型。
- 内联 Python 绑定逻辑。
- 把 `WorldBatchRuntime` 的所有低层 API 无选择复制为 facade API。
- 新增未设计 request/result 的主线入口。
- 在 `*_types.h` 或 facade public header 中直接 include `core/engine/*`。

## 逃逸口规则

`RuntimeFacade::runtime()` 是 compatibility / diagnostics 逃逸口。它可以服务旧测试、迁移期调试和底层能力验证，但新主线代码不应依赖它。

维护中的 Python 前端如果仍需要兼容低层 `WorldBatchRuntime`，必须把访问集中在一个显式 adapter 中，并在 adapter 对外提供 facade-shaped 方法。主类和业务流程不得直接调用 `RuntimeFacade.runtime()` 或根据 facade 是否存在分叉。

主线前端也不应缓存 raw `WorldBatchRuntime` 或从 adapter 重新暴露 compatibility runtime。确实需要 `SimulationKernel` 的兼容路径时，应新增 adapter 方法，并在方法名或调用点说明它是迁移期 compatibility / diagnostics 能力。

新增长期 API 时，应优先补充 facade request/result，并在 Python 层绑定 facade，而不是直接暴露新的底层 runtime 方法。

## Diagnostics Surface

`DiagnosticsTrace` 本身就是维护中的 facade surface。它可以与 engagement
export 共享 kernel evidence，但 facade 必须提供独立的 diagnostics query path，
不能要求使用者为了读取 trace 只能 piggyback 到
`export_engagement_event_packet()`。

## Split Threshold

`RuntimeFacade` 的治理计数规则如下：

- 只统计维护中的 public request/result 方法。
- 不统计 constructor、accessor，以及像 `runtime()` 这样的
  compatibility-only escape hatch。
- 当维护中的方法数接近约 40 个时，应先围绕 Session、Setup、Execution、
  Observation、Diagnostics、Engagement 与 Capability groups 规划拆分，再继续扩张主线 surface。
