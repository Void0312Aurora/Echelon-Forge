# `src/tools/experimental/gpu_phase0` 边界

`gpu_phase0` 保存早期 GPU phase-0 探针，用于验证候选列表、视觉、通信、飞行 shaping 等 GPU helper 的可行性。

## 允许

- 独立 probe executable。
- 与 GPU helper parity 或性能相关的临时验证。
- 只读或受控调用 runtime packet API 的实验代码。

## 禁止

- 默认 runtime backend。
- 被 Python binding、facade 或 core runtime 依赖。
- 在未冻结的情况下改变 CPU truth path。

## 迁移备注

可维护的 GPU helper 应迁移到 `src/gpu` 主目录；过期探针应归档或删除，而不是继续扩展 phase-0 目录。
