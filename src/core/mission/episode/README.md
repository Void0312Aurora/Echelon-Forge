# `src/core/mission/episode` 边界

`mission/episode` 负责 execution episode 的状态、批量输入准备和 controller 编排。它把 scenario/env state 转换为 `mission/runtime` inputs，并把 runtime products 应用回 episode state。

## 允许

- `ExecutionEpisodeState` import/export 和状态字段演进。
- `StepEvaluationBatchConfig`、`StepEvaluationBatchEnvState` 与 batch prepare contract。
- `ExecutionEpisodeController` 的 prepare、evaluate、step 协调逻辑。

## 禁止

- 直接实现 reward/objective/termination 数值公式；这些应位于 `mission/runtime`。
- Python/nanobind 绑定和 facade 适配。
- 将 controller 内部 JSON codec、transition 和 breakdown helper 暴露为跨层公共 API。

## 子目录

- `detail/`：controller 私有 helper。外部代码一般不应 include 这里的头。

## 依赖方向

本目录可以依赖 `mission/runtime`。它不应依赖 `runtime/facade`、`interfaces/python` 或 `gpu`。
