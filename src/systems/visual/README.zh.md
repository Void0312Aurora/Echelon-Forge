# `src/systems/visual` 边界

`systems/visual` 保存视觉观测 system 的 ECS 调度和每 tick 更新逻辑。

## 允许

- visual sensor system。
- 对视觉 component 和空间查询结果的组合更新。

## 禁止

- visual component 定义。
- GPU CUDA kernel。
- Python image/DLPack binding。
- mission episode 或 facade 逻辑。

## 迁移备注

GPU 加速 helper 放在 `gpu/`；Python 视图导出放在 `interfaces/python`；本目录只负责 ECS system 行为。
