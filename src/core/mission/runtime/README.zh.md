# `src/core/mission/runtime` 边界

`mission/runtime` 承载 mission、objective、reward、termination 和 execution runtime 的纯计算入口。这里产出运行时产物，供 episode controller、GPU 辅助逻辑、Python 绑定和 facade 底层实现复用。

## 允许

- mission observation、step、frame、episode runtime inputs/products。
- objective、reward、termination 的确定性评估。
- 只依赖 component DTO、geometry runtime 和局部数值辅助逻辑的纯 C++ 计算。

## 禁止

- `ExecutionEpisodeController` 状态导入/导出。
- mission-command JSON 往返、route transition、reward breakdown JSON。
- Python/nanobind 绑定和 facade request/result 适配。

## 依赖方向

本目录可以被 `mission/episode`、`runtime/facade` 底层实现、`interfaces/python` 绑定和 `gpu` 辅助逻辑 include。它不应 include `mission/episode` 或 `runtime/facade`。
