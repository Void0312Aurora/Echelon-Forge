# `src/core/mission/runtime` 边界

`mission/runtime` 承载 mission、objective、reward、termination 和 execution runtime 的纯计算入口。这里产出运行时产物，供维护中的 Python 编排、GPU 辅助逻辑、Python 绑定和 facade 底层实现复用。

成熟 execution runtime 仍以 air 为主，但边界描述应是 domain-aware，而不是 flight-only：它消费上层准备好的 component DTO 与 mission input；naval tasking/evidence surface 和早期 ground-aware setup 留在纯 runtime owner 之外。本目录不得宣称拥有完整 naval 或 ground runtime 语义。

## 允许

- mission observation、step、frame、episode runtime inputs/products。
- objective、reward、termination 的确定性评估。
- 只依赖 component DTO、geometry runtime 和局部数值辅助逻辑的纯 C++ 计算。
- 可被 facade/binding 层复用、但不引入这些上层的 domain-neutral runtime product。

## 禁止

- 有状态的 episode 编排或 `ExecutionEpisodeState` 所有权。
- mission-command JSON 往返、route transition、reward breakdown JSON。
- Python/nanobind 绑定和 facade request/result 适配。
- ground movement、sensing、terrain、fires、damage 或完整 land-domain runtime。

## 依赖方向

本目录可以被 `mission/episode`、`runtime/facade` 底层实现、`interfaces/python` 绑定和 `gpu` 辅助逻辑 include。它不应 include `mission/episode` 或 `runtime/facade`。
