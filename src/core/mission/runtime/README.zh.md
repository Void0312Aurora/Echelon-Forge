<!-- Machine-translated draft generated on 2026-05-18 from src/core/mission/runtime/README.md. Review before treating this file as authoritative. -->

# `src/core/mission/runtime` 边界

`mission/runtime` 承载任务、目标、奖励、终止和执行运行时的纯计算入口。这里产出运行时产物，供回合控制器、GPU 辅助器、Python 绑定和外观底层实现复用。

## 允许

- 任务观测、步骤、帧、回合运行时输入/产出。
- 目标、奖励、终止的确定性评估。
- 只依赖组件 DTO、几何运行时和局部数值辅助器的纯 C++ 计算。

## 禁止

- `ExecutionEpisodeController` 状态导入/导出。
- 任务指令 JSON 往返、路线切换、奖励分解 JSON。
- Python/nanobind 绑定和外观请求/结果适配。

## 依赖方向

本目录可以被 `mission/episode`、`runtime/facade` 底层实现、`interfaces/python` 绑定和 `gpu` 辅助器包含。它不应包含 `mission/episode` 或 `runtime/facade`。
