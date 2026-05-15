# `src/core/mission/runtime` 边界

`mission/runtime` 承载 mission、objective、reward、termination 和 execution runtime 的纯计算入口。这里产出 runtime products，供 episode controller、GPU helper、Python binding 和 facade 底层实现复用。

## 允许

- mission observation、step、frame、episode runtime inputs/products。
- objective、reward、termination 的 deterministic evaluation。
- 只依赖 component DTO、geometry runtime 和局部数值 helper 的纯 C++ 计算。

## 禁止

- `ExecutionEpisodeController` state import/export。
- mission-command JSON round-trip、route transition、reward breakdown JSON。
- Python/nanobind 绑定和 facade request/result 适配。

## 依赖方向

本目录可以被 `mission/episode`、`runtime/facade` 底层实现、`interfaces/python` binding 和 `gpu` helper include。它不应 include `mission/episode` 或 `runtime/facade`。
