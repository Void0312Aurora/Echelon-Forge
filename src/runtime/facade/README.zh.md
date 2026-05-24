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

## 逃逸口退休

`RuntimeFacade` 不再公开 raw `WorldBatchRuntime` 逃逸口。维护前端必须使用 facade-level request/result API；低层 diagnostics 或能力验证如果确实需要 raw runtime，应在 diagnostics/test scope 直接实例化 `WorldBatchRuntime`，而不是从 facade 向下钻。

主线前端不得缓存 raw `WorldBatchRuntime`、不得从 adapter 重新暴露 compatibility runtime，也不得根据 raw runtime 是否可用分叉。新增长期能力时，应补充设计过的 facade request/result，并在 Python 层绑定 facade 方法。

新增长期 API 时，应优先补充 facade request/result，并在 Python 层绑定 facade，而不是直接暴露新的底层 runtime 方法。

## Diagnostics Surface

`DiagnosticsTrace` 本身就是维护中的 facade surface。它可以与 engagement
export 共享 kernel evidence，但 facade 必须提供独立的 diagnostics query path，
不能要求使用者为了读取 trace 只能 piggyback 到
`export_engagement_event_packet()`。

## Split Threshold

`RuntimeFacade` 的治理计数规则如下：

- 只统计维护中的 public request/result 方法。
- 不统计 constructor 和简单 accessor。
- 当维护中的方法数接近约 40 个时，应先围绕 Session、Setup、Execution、
  Observation、Diagnostics、Engagement 与 Capability groups 规划拆分，再继续扩张主线 surface。
