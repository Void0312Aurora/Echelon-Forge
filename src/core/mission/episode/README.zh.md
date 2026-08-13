# `src/core/mission/episode` 边界

`mission/episode` 负责 execution episode 状态 DTO、批量输入准备和 reward breakdown 序列化。有状态 step 编排保留在维护中的 Python 主路径；本目录不再拥有第二套 episode controller。

## 允许

- `ExecutionEpisodeState` 的导入/导出和状态字段演进。
- `StepEvaluationBatchConfig`、`StepEvaluationBatchEnvState` 与 batch prepare contract。
- 面向 `ExecutionEpisodeRuntimeProducts` 的稳定 reward breakdown 序列化。

## 禁止

- 直接实现 reward/objective/termination 数值公式；这些应位于 `mission/runtime`。
- Python/nanobind 绑定和 facade 适配。
- 引入并行的有状态 episode stepping owner 或 mission-command transition codec。
- 将 breakdown 实现辅助逻辑暴露为跨层公共 API。

## 子目录

- `detail/`：reward breakdown 私有实现。外部代码应 include episode 公共头。

## 依赖方向

本目录可以依赖 `mission/runtime`。它不应依赖 `runtime/facade`、`interfaces/python` 或 `gpu`。
